"""
题目批量导入工具

支持：
- 多种格式导入：JSON, CSV, Excel
- 题目验证：类型、必填字段、难度范围
- 重复检测：精确匹配、相似度匹配
- 批量处理：分批导入、进度追踪
- 错误处理：部分失败、事务回滚
"""

import json
import csv
import asyncio
import hashlib
from io import StringIO, BytesIO
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Tuple
from enum import Enum
from difflib import SequenceMatcher


# ============================================================================
# 错误类型定义
# ============================================================================

class ImportError(Exception):
    """导入基础异常"""
    pass


class InvalidImportModeError(ImportError):
    """无效的导入模式"""
    pass


class InvalidBatchSizeError(ImportError):
    """无效的批量大小"""
    pass


class UnsupportedFileTypeError(ImportError):
    """不支持的文件类型"""
    pass


class CSVParseError(ImportError):
    """CSV解析错误"""
    pass


class CSVParseException(CSVParseError):
    """CSV解析错误（兼容性别名）"""
    pass


class JSONParseError(ImportError):
    """JSON解析错误"""
    pass


# ============================================================================
# 配置类
# ============================================================================

@dataclass
class ImportConfig:
    """批量导入配置"""
    import_mode: str = "create"                    # create/update/upsert
    skip_duplicates: bool = True                   # 跳过重复题目
    batch_size: int = 100                          # 批量大小
    validate_only: bool = False                     # 仅验证不导入
    update_existing: bool = False                   # 更新已存在题目
    supported_formats: List[str] = field(
        default_factory=lambda: ["json", "csv", "xlsx"]
    )
    max_retries: int = 3                          # 最大重试次数
    rollback_on_error: bool = False                # 错误时回滚
    
    def __post_init__(self):
        """验证配置"""
        # 验证导入模式
        valid_modes = ["create", "update", "upsert"]
        if self.import_mode not in valid_modes:
            raise InvalidImportModeError(
                f"Invalid import_mode: {self.import_mode}. "
                f"Must be one of {valid_modes}"
            )
        
        # 验证批量大小
        if self.batch_size < 1 or self.batch_size > 1000:
            raise InvalidBatchSizeError(
                f"batch_size must be between 1 and 1000, got {self.batch_size}"
            )
        
        # 验证格式
        valid_formats = ["json", "csv", "xlsx"]
        for fmt in self.supported_formats:
            if fmt not in valid_formats:
                raise UnsupportedFileTypeError(
                    f"Unsupported format: {fmt}. "
                    f"Supported formats: {valid_formats}"
                )


# ============================================================================
# 题目验证器
# ============================================================================

class QuestionValidator:
    """题目验证器"""
    
    # 题目类型定义
    QUESTION_TYPES = ["single", "multiple", "fill", "short", "programming", "discussion", "material"]
    
    # 各类型题目必填字段
    REQUIRED_FIELDS = {
        "single": ["content", "options", "answer"],
        "multiple": ["content", "options", "answer"],
        "fill": ["content", "answer"],
        "short": ["content", "answer"],
        "programming": ["content", "answer"],
        "discussion": ["content", "answer"],
        "material": ["content", "sub_questions"]
    }
    
    # 选项题目的最小选项数
    MIN_OPTIONS = {
        "single": 2,
        "multiple": 2
    }
    
    # 最大选项数
    MAX_OPTIONS = 6
    
    def __init__(self, strict_mode: bool = False):
        """初始化验证器"""
        self.strict_mode = strict_mode
    
    def validate(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证单个题目
        
        Returns:
            Dict with keys: valid (bool), errors (List), question (Dict)
        """
        errors = []
        
        # 检查题目类型
        q_type = question.get("type")
        if not q_type:
            errors.append("Missing required field: type")
        elif q_type not in self.QUESTION_TYPES:
            errors.append(f"Invalid question type: {q_type}")
        
        # 检查必填字段
        if q_type and q_type in self.REQUIRED_FIELDS:
            for field_name in self.REQUIRED_FIELDS[q_type]:
                if field_name not in question or not question[field_name]:
                    errors.append(f"Missing required field: {field_name}")
        
        # 检查选项数量
        if q_type in self.MIN_OPTIONS:
            options = question.get("options", [])
            if len(options) < self.MIN_OPTIONS[q_type]:
                errors.append(
                    f"{q_type} requires at least {self.MIN_OPTIONS[q_type]} options"
                )
            elif len(options) > self.MAX_OPTIONS:
                errors.append(
                    f"Maximum {self.MAX_OPTIONS} options allowed"
                )
        
        # 检查答案有效性
        if q_type in ["single", "multiple"] and "options" in question:
            options = question["options"]
            answer = question.get("answer", "")
            
            if isinstance(answer, str):
                # 单选题答案应该是单个字母
                if q_type == "single" and len(answer) > 1:
                    errors.append("Single choice answer must be a single option key")
            
            # 检查答案是否在选项中
            valid_keys = [opt.get("key") for opt in options]
            if isinstance(answer, str) and answer not in valid_keys:
                errors.append(f"Invalid answer key: {answer}")
        
        # 检查难度范围
        difficulty = question.get("difficulty")
        if difficulty is not None:
            if not isinstance(difficulty, (int, float)):
                errors.append("Difficulty must be a number")
            elif difficulty < 1 or difficulty > 5:
                errors.append("Difficulty must be between 1 and 5")
        
        # 检查内容长度
        content = question.get("content", "")
        if content and len(content) > 5000:
            errors.append("Content exceeds maximum length of 5000 characters")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "question": question
        }
    
    def validate_batch(self, questions: List[Dict]) -> Dict[str, Any]:
        """批量验证"""
        results = [self.validate(q) for q in questions]
        
        valid_count = sum(1 for r in results if r["valid"])
        invalid_count = len(results) - valid_count
        
        return {
            "total": len(results),
            "valid": valid_count,
            "invalid": invalid_count,
            "results": results
        }


# ============================================================================
# CSV 解析器
# ============================================================================

class CSVParser:
    """CSV格式解析器"""
    
    REQUIRED_COLUMNS = ["type", "content"]
    
    def __init__(self, encoding: str = "utf-8"):
        """初始化解析器"""
        self.encoding = encoding
    
    def parse(self, content: str) -> List[Dict[str, Any]]:
        """
        解析CSV内容
        
        Args:
            content: CSV格式字符串
            
        Returns:
            List of question dictionaries
        """
        try:
            reader = csv.DictReader(StringIO(content))
            
            # 检查必需列
            if reader.fieldnames is None:
                raise CSVParseError("Empty CSV content")
            
            for col in self.REQUIRED_COLUMNS:
                if col not in reader.fieldnames:
                    raise CSVParseError(f"Missing required column: {col}")
            
            questions = []
            for row in reader:
                question = self._parse_row(row)
                if question:
                    questions.append(question)
            
            return questions
            
        except csv.Error as e:
            raise CSVParseError(f"CSV parsing error: {str(e)}")
    
    def _parse_row(self, row: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """解析单行数据"""
        question = {}
        
        # 基本字段
        question["type"] = row.get("type", "").strip()
        question["content"] = row.get("content", "").strip()
        
        if not question["type"] or not question["content"]:
            return None
        
        # 可选字段
        if row.get("answer"):
            question["answer"] = row["answer"].strip()
        
        if row.get("difficulty"):
            try:
                question["difficulty"] = int(row["difficulty"])
            except ValueError:
                question["difficulty"] = 2
        
        if row.get("score"):
            try:
                question["score"] = float(row["score"])
            except ValueError:
                question["score"] = 5.0
        
        if row.get("knowledge_points"):
            try:
                question["knowledge_points"] = json.loads(row["knowledge_points"])
            except json.JSONDecodeError:
                question["knowledge_points"] = []
        
        # 解析选项
        if row.get("options"):
            try:
                question["options"] = json.loads(row["options"])
            except json.JSONDecodeError:
                question["options"] = []
        
        return question


# ============================================================================
# JSON 解析器
# ============================================================================

class JSONParser:
    """JSON格式解析器"""
    
    def __init__(self):
        """初始化解析器"""
        pass
    
    def parse(self, content: str) -> List[Dict[str, Any]]:
        """
        解析JSON内容
        
        Args:
            content: JSON格式字符串
            
        Returns:
            List of question dictionaries
        """
        try:
            data = json.loads(content)
            
            if not isinstance(data, list):
                raise JSONParseError("JSON content must be an array of questions")
            
            return data
            
        except json.JSONDecodeError as e:
            raise JSONParseError(f"JSON parsing error: {str(e)}")


# ============================================================================
# 重复检测器
# ============================================================================

class DuplicateDetector:
    """重复题目检测器"""
    
    def __init__(self, compare_content_only: bool = False, similarity_threshold: float = 0.0):
        """
        初始化检测器
        
        Args:
            compare_content_only: 是否仅比较内容
            similarity_threshold: 相似度阈值（0-1），0表示完全匹配
        """
        self.compare_content_only = compare_content_only
        self.similarity_threshold = similarity_threshold
    
    def is_duplicate(self, q1: Dict, q2: Dict) -> bool:
        """
        判断两个题目是否重复
        
        Args:
            q1: 题目1
            q2: 题目2
            
        Returns:
            True if duplicate
        """
        if self.similarity_threshold > 0:
            return self._is_similar(q1, q2)
        
        return self._is_exact_duplicate(q1, q2)
    
    def _is_exact_duplicate(self, q1: Dict, q2: Dict) -> bool:
        """精确匹配"""
        if self.compare_content_only:
            return q1.get("content") == q2.get("content")
        
        return (
            q1.get("content") == q2.get("content") and
            q1.get("answer") == q2.get("answer")
        )
    
    def _is_similar(self, q1: Dict, q2: Dict) -> bool:
        """相似度匹配"""
        content1 = q1.get("content", "")
        content2 = q2.get("content", "")
        
        similarity = SequenceMatcher(
            None, content1, content2
        ).ratio()
        
        return similarity >= self.similarity_threshold
    
    def find_duplicates(self, questions: List[Dict]) -> List[Tuple[int, int]]:
        """
        在题目列表中找出所有重复对
        
        Returns:
            List of (index1, index2) tuples
        """
        duplicates = []
        n = len(questions)
        
        for i in range(n):
            for j in range(i + 1, n):
                if self.is_duplicate(questions[i], questions[j]):
                    duplicates.append((i, j))
        
        return duplicates


# ============================================================================
# 导入进度追踪
# ============================================================================

@dataclass
class ImportProgress:
    """导入进度追踪"""
    total: int = 0
    processed: int = 0
    success_count: int = 0
    failed_count: int = 0
    errors: List[Dict] = field(default_factory=list)
    callback: Optional[Callable] = field(default=None, repr=False)
    
    @property
    def percentage(self) -> float:
        """计算进度百分比"""
        if self.total == 0:
            return 0.0
        return round(self.processed / self.total * 100, 2)
    
    def update(self, success: int = 0, failed: int = 0, error: Optional[Dict] = None):
        """更新进度"""
        self.processed += success + failed
        self.success_count += success
        self.failed_count += failed
        
        if error:
            self.errors.append(error)
        
        # 触发回调
        if self.callback:
            self.callback(self)
    
    def reset(self):
        """重置进度"""
        self.processed = 0
        self.success_count = 0
        self.failed_count = 0
        self.errors = []


# ============================================================================
# 导入结果
# ============================================================================

@dataclass
class ImportResult:
    """导入结果"""
    total: int = 0
    processed: int = 0
    success_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    errors: List[Dict] = field(default_factory=list)
    imported_ids: List[int] = field(default_factory=list)
    
    @property
    def success(self) -> bool:
        """是否成功"""
        return self.failed_count == 0
    
    def add_success(self, question_id: Optional[int] = None):
        """添加成功记录"""
        self.processed += 1
        self.success_count += 1
        if question_id:
            self.imported_ids.append(question_id)
    
    def add_error(self, error: Dict):
        """添加错误记录"""
        self.processed += 1
        self.failed_count += 1
        self.errors.append(error)
    
    def add_skipped(self):
        """添加跳过记录"""
        self.processed += 1
        self.skipped_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "total": self.total,
            "processed": self.processed,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "errors": self.errors,
            "imported_ids": self.imported_ids
        }


# ============================================================================
# 批量导入服务
# ============================================================================

class BatchImportService:
    """批量导入服务"""
    
    def __init__(self, config: Optional[ImportConfig] = None):
        """
        初始化服务
        
        Args:
            config: 导入配置
        """
        self.config = config or ImportConfig()
        self.validator = QuestionValidator()
        self.detector = DuplicateDetector()
    
    async def import_questions(
        self,
        questions: List[Dict],
        progress: Optional[ImportProgress] = None
    ) -> Dict[str, Any]:
        """
        批量导入题目
        
        Args:
            questions: 题目列表
            progress: 进度回调
            
        Returns:
            导入结果字典
        """
        result = ImportResult(total=len(questions))
        progress = progress or ImportProgress(total=len(questions))
        
        # 验证所有题目
        validation_results = self.validator.validate_batch(questions)
        
        # 按批次处理
        batch_size = self.config.batch_size
        batches = [
            validation_results["results"][i:i + batch_size]
            for i in range(0, len(questions), batch_size)
        ]
        
        for batch_idx, batch in enumerate(batches):
            batch_result = await self._process_batch(batch)
            
            # 更新结果
            for item in batch_result:
                if item["success"]:
                    result.add_success(item.get("id"))
                    progress.update(success=1)
                else:
                    result.add_error(item["error"])
                    progress.update(failed=1, error=item["error"])
        
        result.batch_count = len(batches)
        return result.to_dict()
    
    async def _process_batch(self, batch: List[Dict]) -> List[Dict]:
        """处理单个批次"""
        results = []
        
        for item in batch:
            if not item["valid"]:
                results.append({
                    "success": False,
                    "error": {
                        "message": "Validation failed",
                        "errors": item["errors"],
                        "question": item["question"]
                    }
                })
                continue
            
            question = item["question"]
            
            # 检测重复
            if self.config.skip_duplicates and self._is_duplicate(question):
                results.append({
                    "success": True,
                    "skipped": True
                })
                continue
            
            # 导入
            if self.config.validate_only:
                results.append({"success": True, "id": None})
            else:
                question_id = await self._import_single(question)
                results.append({"success": True, "id": question_id})
        
        return results
    
    async def _import_single(self, question: Dict) -> int:
        """导入单个题目（模拟）"""
        # 实际应调用数据库或API
        # 模拟返回ID
        return hash(question.get("content", "")) % 100000
    
    def _is_duplicate(self, question: Dict) -> bool:
        """检查是否重复"""
        # 实际应查询数据库
        return False


# ============================================================================
# 批量导入 API
# ============================================================================

class BatchImportAPI:
    """批量导入API封装"""
    
    def __init__(self):
        """初始化API"""
        self.config = ImportConfig()
        self.service = BatchImportService(self.config)
        self.json_parser = JSONParser()
        self.csv_parser = CSVParser()
    
    def import_from_file(self, file_path: str, config: Optional[ImportConfig] = None) -> Dict[str, Any]:
        """
        从文件导入题目
        
        Args:
            file_path: 文件路径
            config: 导入配置
            
        Returns:
            导入结果
        """
        import os
        
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}
        
        suffix = file_path.lower().split(".")[-1]
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            request = {
                "content": content,
                "format": suffix
            }
            
            return self.import_from_content(request)
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def validate_content(self, request: Dict) -> Dict[str, Any]:
        """
        验证导入内容
        
        Args:
            request: {
                "content": str,  # 导入内容
                "format": str,   # json/csv
                "validate_only": bool
            }
            
        Returns:
            验证结果
        """
        content = request.get("content", "")
        format_type = request.get("format", "json").lower()
        
        try:
            # 解析内容
            if format_type == "json":
                questions = self.json_parser.parse(content)
            elif format_type == "csv":
                questions = self.csv_parser.parse(content)
            else:
                return {"valid": False, "error": f"Unsupported format: {format_type}"}
            
            # 验证
            validator = QuestionValidator()
            result = validator.validate_batch(questions)
            
            return {
                "valid": result["invalid"] == 0,
                "total": result["total"],
                "valid_count": result["valid"],
                "invalid_count": result["invalid"],
                "errors": [
                    {"index": i, "errors": r["errors"]}
                    for i, r in enumerate(result["results"])
                    if not r["valid"]
                ]
            }
            
        except ImportError as e:
            return {"valid": False, "error": str(e)}
    
    def import_from_content(self, request: Dict) -> Dict[str, Any]:
        """
        从内容导入题目
        
        Args:
            request: {
                "content": str,
                "format": str,
                "import_mode": str,
                "validate_only": bool
            }
        """
        content = request.get("content", "")
        format_type = request.get("format", "json").lower()
        
        try:
            # 解析
            if format_type == "json":
                questions = self.json_parser.parse(content)
            elif format_type == "csv":
                questions = self.csv_parser.parse(content)
            else:
                return {"success": False, "error": f"Unsupported format: {format_type}"}
            
            # 更新配置
            import_mode = request.get("import_mode", "create")
            validate_only = request.get("validate_only", False)
            
            config = ImportConfig(
                import_mode=import_mode,
                validate_only=validate_only
            )
            service = BatchImportService(config)
            
            # 导入
            import asyncio
            result = asyncio.run(service.import_questions(questions))
            
            return result
            
        except ImportError as e:
            return {"success": False, "error": str(e)}


# ============================================================================
# 便捷函数
# ============================================================================

def detect_format(content: str) -> Optional[str]:
    """检测内容格式"""
    content = content.strip()
    
    if content.startswith("[") or content.startswith("{"):
        return "json"
    
    if "\t" in content or "," in content:
        # 检查是否是CSV
        lines = content.split("\n")
        if lines:
            first_line = lines[0].lower()
            if "type" in first_line or "content" in first_line:
                return "csv"
    
    return None


async def import_from_file(
    file_path: str,
    config: Optional[ImportConfig] = None
) -> Dict[str, Any]:
    """
    从文件导入题目
    
    Args:
        file_path: 文件路径
        config: 导入配置
    """
    # 检测格式
    suffix = file_path.lower().split(".")[-1]
    
    if suffix == "json":
        parser = JSONParser()
    elif suffix == "csv":
        parser = CSVParser()
    else:
        return {"success": False, "error": f"Unsupported file type: {suffix}"}
    
    # 读取文件
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 解析
    questions = parser.parse(content)
    
    # 导入
    service = BatchImportService(config)
    return await service.import_questions(questions)


# ============================================================================
# 主入口
# ============================================================================

if __name__ == "__main__":
    # 测试代码
    config = ImportConfig(
        import_mode="create",
        batch_size=10,
        validate_only=True
    )
    
    sample_questions = [
        {
            "type": "single",
            "content": "Python是什么类型的语言？",
            "options": [
                {"key": "A", "content": "编译型"},
                {"key": "B", "content": "解释型"}
            ],
            "answer": "B",
            "difficulty": 1
        }
    ]
    
    service = BatchImportService(config)
    print("BatchImportService initialized successfully!")
    print(f"Config: {config}")
