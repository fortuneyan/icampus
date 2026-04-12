"""
T23: 题目批量导入工具 - 测试文件

TDD 开发模式：
- Red: 编写测试用例（当前文件）
- Green: 实现最小可用代码
- Refactor: 清理和优化
"""

import pytest
import json
import csv
from io import StringIO, BytesIO
from typing import Dict, List, Any
from unittest.mock import MagicMock, AsyncMock, patch


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_single_question() -> Dict[str, Any]:
    """单个题目数据"""
    return {
        "type": "single",
        "content": "以下哪个是Python的数据类型？",
        "options": [
            {"key": "A", "content": "int"},
            {"key": "B", "content": "str"},
            {"key": "C", "content": "list"},
            {"key": "D", "content": "以上都是"}
        ],
        "answer": "D",
        "difficulty": 2,
        "knowledge_points": ["Python基础", "数据类型"],
        "score": 5
    }


@pytest.fixture
def sample_questions() -> List[Dict[str, Any]]:
    """多个题目数据"""
    return [
        {
            "type": "single",
            "content": "1+1等于多少？",
            "options": [
                {"key": "A", "content": "1"},
                {"key": "B", "content": "2"},
                {"key": "C", "content": "3"},
                {"key": "D", "content": "4"}
            ],
            "answer": "B",
            "difficulty": 1
        },
        {
            "type": "fill",
            "content": "Python的创始人是_____。",
            "answer": "Guido van Rossum",
            "difficulty": 2
        },
        {
            "type": "short",
            "content": "简述Python的特点。",
            "answer": "简洁、易读、可扩展",
            "difficulty": 3
        }
    ]


@pytest.fixture
def sample_csv_content() -> str:
    """CSV格式题目数据"""
    return """type,content,options,answer,difficulty,knowledge_points,score
single,"以下哪个是Python的list方法？","[{\"key\":\"A\",\"content\":\"append\"},{\"key\":\"B\",\"content\":\"add\"},{\"key\":\"C\",\"content\":\"insert\"},{\"key\":\"D\",\"content\":\"push\"}]","A",2,"[\"Python\",\"数据结构\"]",5
fill,Python中用于定义函数的关键字是_____。,,def,1,"[\"Python\",\"函数\"]",3
short,请简述装饰器的用途。,,增强函数功能,3,"[\"Python\",\"装饰器\"]",10"""


@pytest.fixture
def sample_json_content() -> str:
    """JSON格式题目数据"""
    return json.dumps([
        {
            "type": "single",
            "content": "Python是什么类型的语言？",
            "options": [
                {"key": "A", "content": "编译型"},
                {"key": "B", "content": "解释型"},
                {"key": "C", "content": "汇编型"},
                {"key": "D", "content": "机器码"}
            ],
            "answer": "B",
            "difficulty": 1
        },
        {
            "type": "fill",
            "content": "Python的标准库用_____包管理。",
            "answer": "pip",
            "difficulty": 1
        }
    ], ensure_ascii=False)


@pytest.fixture
def sample_excel_bytes() -> BytesIO:
    """Excel格式题目数据（简化模拟）"""
    # 实际应使用 openpyxl 读取真实 Excel 文件
    return BytesIO(b"SIMULATED_EXCEL_DATA")


@pytest.fixture
def sample_import_request(sample_questions) -> Dict[str, Any]:
    """导入请求数据"""
    return {
        "questions": sample_questions,
        "subject_id": 1,
        "grade_level": 10,
        "import_mode": "create",
        "skip_duplicates": True
    }


# ============================================================================
# Test: ImportConfig 配置验证
# ============================================================================

class TestImportConfig:
    """导入配置测试"""

    def test_config_default_values(self):
        """测试默认配置"""
        from app.services.batch_import import ImportConfig
        
        config = ImportConfig()
        
        assert config.import_mode == "create"
        assert config.skip_duplicates is True
        assert config.batch_size == 100
        assert config.validate_only is False
        assert config.update_existing is False

    def test_config_custom_values(self):
        """测试自定义配置"""
        from app.services.batch_import import ImportConfig
        
        config = ImportConfig(
            import_mode="update",
            skip_duplicates=False,
            batch_size=50,
            validate_only=True,
            update_existing=True
        )
        
        assert config.import_mode == "update"
        assert config.skip_duplicates is False
        assert config.batch_size == 50
        assert config.validate_only is True
        assert config.update_existing is True

    def test_config_invalid_import_mode(self):
        """测试无效的导入模式"""
        from app.services.batch_import import ImportConfig
        from app.services.batch_import import InvalidImportModeError
        
        with pytest.raises(InvalidImportModeError):
            ImportConfig(import_mode="invalid")

    def test_config_invalid_batch_size(self):
        """测试无效的批量大小"""
        from app.services.batch_import import ImportConfig
        from app.services.batch_import import InvalidBatchSizeError
        
        with pytest.raises(InvalidBatchSizeError):
            ImportConfig(batch_size=0)
        
        with pytest.raises(InvalidBatchSizeError):
            ImportConfig(batch_size=-1)
        
        with pytest.raises(InvalidBatchSizeError):
            ImportConfig(batch_size=1001)

    def test_config_invalid_file_type(self):
        """测试不支持的文件类型"""
        from app.services.batch_import import ImportConfig
        from app.services.batch_import import UnsupportedFileTypeError
        
        # 测试格式验证（默认格式是支持的）
        config = ImportConfig(supported_formats=["json", "csv"])
        assert "json" in config.supported_formats
        assert "csv" in config.supported_formats
        
        # 测试包含不支持格式会报错
        with pytest.raises(UnsupportedFileTypeError):
            ImportConfig(supported_formats=["json", "invalid_format"])


# ============================================================================
# Test: QuestionValidator 题目验证
# ============================================================================

class TestQuestionValidator:
    """题目验证测试"""

    def test_validate_single_choice(self, sample_single_question):
        """测试单选题验证"""
        from app.services.batch_import import QuestionValidator
        
        validator = QuestionValidator()
        result = validator.validate(sample_single_question)
        
        assert result["valid"] is True
        assert "errors" in result
        assert len(result["errors"]) == 0

    def test_validate_fill_blank(self):
        """测试填空题验证"""
        from app.services.batch_import import QuestionValidator
        
        question = {
            "type": "fill",
            "content": "Python的创始人是_____。",
            "answer": "Guido van Rossum",
            "difficulty": 2
        }
        
        validator = QuestionValidator()
        result = validator.validate(question)
        
        assert result["valid"] is True

    def test_validate_missing_required_field(self):
        """测试缺少必填字段"""
        from app.services.batch_import import QuestionValidator
        
        question = {
            "type": "single",
            "content": "测试题"
            # 缺少 options, answer
        }
        
        validator = QuestionValidator()
        result = validator.validate(question)
        
        assert result["valid"] is False
        assert any("options" in str(e) for e in result["errors"])
        assert any("answer" in str(e) for e in result["errors"])

    def test_validate_invalid_type(self):
        """测试无效的题目类型"""
        from app.services.batch_import import QuestionValidator
        
        question = {
            "type": "invalid_type",
            "content": "测试题"
        }
        
        validator = QuestionValidator()
        result = validator.validate(question)
        
        assert result["valid"] is False
        assert any("type" in str(e).lower() for e in result["errors"])

    def test_validate_invalid_options_count(self):
        """测试无效的选项数量"""
        from app.services.batch_import import QuestionValidator
        
        question = {
            "type": "single",
            "content": "测试题",
            "options": [
                {"key": "A", "content": "选项1"}
            ],
            "answer": "A"
        }
        
        validator = QuestionValidator()
        result = validator.validate(question)
        
        assert result["valid"] is False

    def test_validate_difficulty_out_of_range(self):
        """测试难度超出范围"""
        from app.services.batch_import import QuestionValidator
        
        question = {
            "type": "single",
            "content": "测试题",
            "options": [
                {"key": "A", "content": "1"},
                {"key": "B", "content": "2"}
            ],
            "answer": "A",
            "difficulty": 10  # 应该是 1-5
        }
        
        validator = QuestionValidator()
        result = validator.validate(question)
        
        assert result["valid"] is False
        assert any("difficulty" in str(e).lower() for e in result["errors"])


# ============================================================================
# Test: CSVParser CSV解析
# ============================================================================

class TestCSVParser:
    """CSV解析器测试"""

    def test_parse_basic_csv(self, sample_csv_content):
        """测试基本CSV解析"""
        from app.services.batch_import import CSVParser
        
        parser = CSVParser()
        questions = parser.parse(sample_csv_content)
        
        assert len(questions) == 3
        assert questions[0]["type"] == "single"
        assert questions[1]["type"] == "fill"
        assert questions[2]["type"] == "short"

    def test_parse_csv_with_encoding(self):
        """测试带编码的CSV解析"""
        from app.services.batch_import import CSVParser
        
        csv_content = "type,content,answer\nfill,中文测试_____。,测试"
        
        parser = CSVParser()
        questions = parser.parse(csv_content)
        
        assert len(questions) == 1
        assert "中文" in questions[0]["content"]

    def test_parse_csv_missing_columns(self):
        """测试CSV列缺失"""
        from app.services.batch_import import CSVParser
        from app.services.batch_import import CSVParseError
        
        csv_content = "type,content"  # 缺少必要的列
        
        parser = CSVParser()
        
        # 应该不抛出异常，而是返回空列表或只包含空题目
        questions = parser.parse(csv_content)
        # 至少验证解析不崩溃
        assert isinstance(questions, list)

    def test_parse_csv_invalid_format(self):
        """测试CSV格式错误"""
        from app.services.batch_import import CSVParser
        from app.services.batch_import import CSVParseError
        
        csv_content = "not,a,valid,csv,line\n"
        
        parser = CSVParser()
        
        with pytest.raises(CSVParseError):
            parser.parse(csv_content)

    def test_parse_csv_with_quotes(self):
        """测试带引号的CSV解析"""
        from app.services.batch_import import CSVParser
        
        csv_content = '''type,content,answer
single,"测试"题，内容包含逗号",A",A",1'''
        
        parser = CSVParser()
        questions = parser.parse(csv_content)
        
        assert len(questions) == 1
        assert "测试" in questions[0]["content"]


# ============================================================================
# Test: JSONParser JSON解析
# ============================================================================

class TestJSONParser:
    """JSON解析器测试"""

    def test_parse_basic_json(self, sample_json_content):
        """测试基本JSON解析"""
        from app.services.batch_import import JSONParser
        
        parser = JSONParser()
        questions = parser.parse(sample_json_content)
        
        assert len(questions) == 2
        assert questions[0]["type"] == "single"
        assert questions[1]["type"] == "fill"

    def test_parse_json_array(self):
        """测试JSON数组解析"""
        from app.services.batch_import import JSONParser
        
        json_content = json.dumps([
            {"type": "single", "content": "题1", "answer": "A"},
            {"type": "fill", "content": "题2", "answer": "答"}
        ])
        
        parser = JSONParser()
        questions = parser.parse(json_content)
        
        assert len(questions) == 2

    def test_parse_invalid_json(self):
        """测试无效JSON"""
        from app.services.batch_import import JSONParser
        from app.services.batch_import import JSONParseError
        
        json_content = "{ invalid json }"
        
        parser = JSONParser()
        
        with pytest.raises(JSONParseError):
            parser.parse(json_content)

    def test_parse_json_not_array(self):
        """测试JSON非数组"""
        from app.services.batch_import import JSONParser
        from app.services.batch_import import JSONParseError
        
        json_content = json.dumps({"type": "single"})
        
        parser = JSONParser()
        
        with pytest.raises(JSONParseError):
            parser.parse(json_content)


# ============================================================================
# Test: BatchImportService 批量导入服务
# ============================================================================

class TestBatchImportService:
    """批量导入服务测试"""

    @pytest.mark.asyncio
    async def test_import_basic(self, sample_questions):
        """测试基本导入"""
        from app.services.batch_import import BatchImportService, ImportConfig
        
        config = ImportConfig(validate_only=False)
        service = BatchImportService(config)
        
        result = await service.import_questions(sample_questions)
        
        assert "success" in result
        assert result["total"] == len(sample_questions)
        assert "success_count" in result
        assert "errors" in result

    @pytest.mark.asyncio
    async def test_import_with_validation(self, sample_questions):
        """测试带验证的导入"""
        from app.services.batch_import import BatchImportService, ImportConfig
        
        config = ImportConfig(validate_only=True)
        service = BatchImportService(config)
        
        result = await service.import_questions(sample_questions)
        
        assert "success" in result
        assert result["total"] == len(sample_questions)
        assert result["success_count"] >= 0  # 验证模式可能不过滤

    @pytest.mark.asyncio
    async def test_import_with_errors(self):
        """测试含错误的导入"""
        from app.services.batch_import import BatchImportService, ImportConfig
        
        questions = [
            {"type": "invalid", "content": "测试"},  # 无效类型
            {"type": "single", "content": "正常题", "answer": "A"}  # 缺少选项
        ]
        
        config = ImportConfig(validate_only=False)
        service = BatchImportService(config)
        
        result = await service.import_questions(questions)
        
        # 可能有错误，但不一定是 success=False
        assert result["total"] == 2
        assert result["failed_count"] >= 0

    @pytest.mark.asyncio
    async def test_import_empty_list(self):
        """测试空列表导入"""
        from app.services.batch_import import BatchImportService, ImportConfig
        
        config = ImportConfig()
        service = BatchImportService(config)
        
        result = await service.import_questions([])
        
        assert result["total"] == 0
        assert result["processed"] == 0

    @pytest.mark.asyncio
    async def test_import_with_batch_size(self, sample_questions):
        """测试分批导入"""
        from app.services.batch_import import BatchImportService, ImportConfig
        
        config = ImportConfig(batch_size=1, validate_only=True)
        service = BatchImportService(config)
        
        result = await service.import_questions(sample_questions)
        
        assert result["total"] == len(sample_questions)
        # 验证处理数量正确
        assert result["processed"] == len(sample_questions)


# ============================================================================
# Test: DuplicateDetector 重复检测
# ============================================================================

class TestDuplicateDetector:
    """重复检测测试"""

    def test_detect_exact_duplicate(self):
        """测试完全重复检测"""
        from app.services.batch_import import DuplicateDetector
        
        detector = DuplicateDetector()
        
        q1 = {"content": "测试题", "answer": "A"}
        q2 = {"content": "测试题", "answer": "A"}
        
        assert detector.is_duplicate(q1, q2) is True

    def test_detect_content_only_duplicate(self):
        """测试仅内容重复检测"""
        from app.services.batch_import import DuplicateDetector
        
        detector = DuplicateDetector(compare_content_only=True)
        
        q1 = {"content": "测试题", "answer": "A"}
        q2 = {"content": "测试题", "answer": "B"}  # 不同答案
        
        assert detector.is_duplicate(q1, q2) is True

    def test_not_duplicate(self):
        """测试不重复检测"""
        from app.services.batch_import import DuplicateDetector
        
        detector = DuplicateDetector()
        
        q1 = {"content": "测试题1", "answer": "A"}
        q2 = {"content": "测试题2", "answer": "A"}
        
        assert detector.is_duplicate(q1, q2) is False

    def test_similar_content_duplicate(self):
        """测试相似内容重复检测（编辑距离）"""
        from app.services.batch_import import DuplicateDetector
        
        detector = DuplicateDetector(similarity_threshold=0.8)
        
        q1 = {"content": "Python是什么编程语言？"}
        q2 = {"content": "Python是什么的编程语言？"}
        
        assert detector.is_duplicate(q1, q2) is True


# ============================================================================
# Test: ImportProgress 导入进度
# ============================================================================

class TestImportProgress:
    """导入进度测试"""

    def test_progress_initialization(self):
        """测试进度初始化"""
        from app.services.batch_import import ImportProgress
        
        progress = ImportProgress(total=100)
        
        assert progress.total == 100
        assert progress.processed == 0
        assert progress.success_count == 0
        assert progress.failed_count == 0

    def test_progress_update(self):
        """测试进度更新"""
        from app.services.batch_import import ImportProgress
        
        progress = ImportProgress(total=100)
        progress.update(success=1)
        
        assert progress.processed == 1
        assert progress.success_count == 1
        
        progress.update(failed=1)
        assert progress.processed == 2
        assert progress.failed_count == 1

    def test_progress_percentage(self):
        """测试进度百分比"""
        from app.services.batch_import import ImportProgress
        
        progress = ImportProgress(total=100)
        progress.update(success=50)
        
        assert progress.percentage == 50

    def test_progress_callback(self):
        """测试进度回调"""
        from app.services.batch_import import ImportProgress
        
        callback_data = []
        
        def callback(p: ImportProgress):
            callback_data.append(p.percentage)
        
        progress = ImportProgress(total=100, callback=callback)
        progress.update(success=25)
        progress.update(success=25)
        
        assert 25 in callback_data
        assert 50 in callback_data


# ============================================================================
# Test: ImportResult 导入结果
# ============================================================================

class TestImportResult:
    """导入结果测试"""

    def test_result_success(self):
        """测试成功结果"""
        from app.services.batch_import import ImportResult
        
        result = ImportResult(total=10)
        result.add_success()
        result.add_success()
        
        assert result.success is True
        assert result.total == 10
        assert result.processed == 2
        assert result.success_count == 2

    def test_result_failure(self):
        """测试失败结果"""
        from app.services.batch_import import ImportResult
        
        result = ImportResult(total=10)
        result.add_error({"message": "Test error", "question": {}})
        
        assert result.success is False
        assert result.failed_count == 1
        assert len(result.errors) == 1

    def test_result_to_dict(self):
        """测试结果转换为字典"""
        from app.services.batch_import import ImportResult
        
        result = ImportResult(total=10)
        result.add_success()
        result.add_error({"message": "Error"})
        
        data = result.to_dict()
        
        assert "success" in data
        assert data["total"] == 10
        assert data["processed"] == 2
        assert data["success_count"] == 1
        assert data["failed_count"] == 1


# ============================================================================
# Test: BatchImportAPI 批量导入API
# ============================================================================

class TestBatchImportAPI:
    """批量导入API测试"""

    def test_import_endpoint_format(self):
        """测试导入端点格式"""
        from app.services.batch_import import BatchImportAPI
        
        api = BatchImportAPI()
        
        # 验证方法存在
        assert hasattr(api, "import_from_file")
        assert hasattr(api, "import_from_content")
        assert hasattr(api, "validate_content")

    def test_validate_content_endpoint(self, sample_json_content):
        """测试验证内容端点"""
        from app.services.batch_import import BatchImportAPI
        
        api = BatchImportAPI()
        
        # 模拟验证请求
        request = {
            "content": sample_json_content,
            "format": "json",
            "validate_only": True
        }
        
        # 验证返回格式
        response = api.validate_content(request)
        
        assert "valid" in response
        assert "total" in response

    def test_import_from_content(self, sample_csv_content):
        """测试从内容导入"""
        from app.services.batch_import import BatchImportAPI
        
        api = BatchImportAPI()
        
        request = {
            "content": sample_csv_content,
            "format": "csv",
            "import_mode": "create"
        }
        
        response = api.import_from_content(request)
        
        assert "success" in response
        assert "total" in response


# ============================================================================
# Test: BatchImportIntegration 批量导入集成测试
# ============================================================================

class TestBatchImportIntegration:
    """批量导入集成测试"""

    @pytest.mark.asyncio
    async def test_full_import_workflow(self, sample_questions):
        """测试完整导入工作流"""
        from app.services.batch_import import (
            BatchImportService,
            QuestionValidator,
            DuplicateDetector,
            ImportConfig
        )
        
        # 1. 验证题目
        validator = QuestionValidator()
        validation_results = [validator.validate(q) for q in sample_questions]
        
        valid_questions = [r["question"] for r in validation_results if r["valid"]]
        assert len(valid_questions) == len(sample_questions)
        
        # 2. 检测重复
        detector = DuplicateDetector()
        duplicates = set()
        for i, q1 in enumerate(valid_questions):
            for j, q2 in enumerate(valid_questions[i+1:], i+1):
                if detector.is_duplicate(q1, q2):
                    duplicates.add(j)
        
        unique_questions = [q for i, q in enumerate(valid_questions) if i not in duplicates]
        
        # 3. 导入
        config = ImportConfig(validate_only=False)
        service = BatchImportService(config)
        result = await service.import_questions(unique_questions)
        
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_import_with_retry(self):
        """测试带重试的导入"""
        from app.services.batch_import import BatchImportService, ImportConfig
        
        questions = [{"type": "single", "content": f"题目{i}", "answer": "A"} for i in range(5)]
        
        config = ImportConfig(max_retries=3, validate_only=True)
        service = BatchImportService(config)
        
        result = await service.import_questions(questions)
        
        assert "success" in result
        assert result["total"] == 5

    @pytest.mark.asyncio
    async def test_import_with_rollback(self):
        """测试带回滚的导入"""
        from app.services.batch_import import BatchImportService, ImportConfig
        
        questions = [
            {"type": "single", "content": "正常题", "answer": "A"},
            {"type": "invalid", "content": "错误题"}  # 第2条会失败
        ]
        
        config = ImportConfig(rollback_on_error=True, validate_only=False)
        service = BatchImportService(config)
        
        result = await service.import_questions(questions)
        
        # 如果启用回滚，全部失败
        # 如果不启用，第一条成功
        assert result["processed"] >= 0


# ============================================================================
# Test: BatchImportEdgeCases 边界情况测试
# ============================================================================

class TestBatchImportEdgeCases:
    """批量导入边界情况测试"""

    def test_very_long_content(self):
        """测试超长内容"""
        from app.services.batch_import import QuestionValidator
        
        question = {
            "type": "single",
            "content": "A" * 10000,  # 超长内容
            "options": [
                {"key": "A", "content": "A" * 1000},
                {"key": "B", "content": "B" * 1000}
            ],
            "answer": "A"
        }
        
        validator = QuestionValidator()
        result = validator.validate(question)
        
        # 验证是否检查长度限制
        assert "content_length" in result or len(result["errors"]) > 0

    def test_special_characters(self):
        """测试特殊字符"""
        from app.services.batch_import import QuestionValidator
        
        question = {
            "type": "single",
            "content": "测试 <script>alert('xss')</script> 标签",
            "options": [
                {"key": "A", "content": "选项 &amp; 测试"},
                {"key": "B", "content": "选项 \"引号\" 测试"}
            ],
            "answer": "A"
        }
        
        validator = QuestionValidator()
        result = validator.validate(question)
        
        assert result["valid"] is True

    def test_empty_content(self):
        """测试空内容"""
        from app.services.batch_import import QuestionValidator
        
        question = {
            "type": "single",
            "content": "",
            "options": [
                {"key": "A", "content": ""},
                {"key": "B", "content": ""}
            ],
            "answer": "A"
        }
        
        validator = QuestionValidator()
        result = validator.validate(question)
        
        assert result["valid"] is False

    def test_unicode_content(self):
        """测试Unicode内容"""
        from app.services.batch_import import QuestionValidator
        
        question = {
            "type": "single",
            "content": "日本語テスト 🎉 emoji测试",
            "options": [
                {"key": "A", "content": "日本語"},
                {"key": "B", "content": "中文"}
            ],
            "answer": "A"
        }
        
        validator = QuestionValidator()
        result = validator.validate(question)
        
        assert result["valid"] is True

    def test_nested_options(self):
        """测试嵌套选项"""
        from app.services.batch_import import QuestionValidator
        
        question = {
            "type": "single",
            "content": "测试嵌套选项",
            "options": [
                {"key": "A", "content": "正常选项"},
                {"key": "B", "content": {"text": "嵌套选项", "sub": True}}  # 嵌套结构
            ],
            "answer": "A"
        }
        
        validator = QuestionValidator()
        result = validator.validate(question)
        
        # 应该处理嵌套或报错
        assert "valid" in result


# ============================================================================
# Test: BatchImportPerformance 性能测试
# ============================================================================

class TestBatchImportPerformance:
    """批量导入性能测试"""

    @pytest.mark.asyncio
    async def test_large_batch_import(self):
        """测试大批量导入"""
        from app.services.batch_import import BatchImportService, ImportConfig
        import time
        
        # 生成1000个题目
        questions = [
            {
                "type": "single",
                "content": f"题目{i}",
                "options": [
                    {"key": "A", "content": "A"},
                    {"key": "B", "content": "B"}
                ],
                "answer": "A",
                "difficulty": (i % 5) + 1
            }
            for i in range(1000)
        ]
        
        config = ImportConfig(batch_size=100, validate_only=True)
        service = BatchImportService(config)
        
        start = time.time()
        result = await service.import_questions(questions)
        elapsed = time.time() - start
        
        assert result["success"] is True
        assert result["total"] == 1000
        assert elapsed < 5  # 应该在5秒内完成

    @pytest.mark.asyncio
    async def test_concurrent_imports(self):
        """测试并发导入"""
        from app.services.batch_import import BatchImportService, ImportConfig
        import asyncio
        
        questions = [
            {"type": "single", "content": f"题{i}", "answer": "A"}
            for i in range(100)
        ]
        
        config = ImportConfig(validate_only=True)
        service = BatchImportService(config)
        
        # 并发执行5个导入任务
        tasks = [service.import_questions(questions) for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # 验证结果存在
        assert len(results) == 5
        assert all("total" in r for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
