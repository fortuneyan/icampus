"""
题库管理模块 - Pydantic Schema

包含：
1. QuestionOption - 题目选项
2. ScoringCriterion - 评分标准
3. QuestionCreate - 创建题目
4. QuestionUpdate - 更新题目
5. QuestionResponse - 题目响应
6. QuestionQuery - 查询参数
7. BatchRequest - 批量操作请求
8. SimilarityCheck - 相似度检测
"""
from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class QuestionType(str, Enum):
    """题型枚举"""
    SINGLE = "single"      # 单选题
    MULTIPLE = "multiple"   # 多选题
    FILL = "fill"           # 填空题
    ESSAY = "essay"         # 解答题
    CALCULATION = "calculation"  # 计算题


class ReviewStatus(str, Enum):
    """审核状态枚举"""
    PENDING = "pending"     # 待审核
    APPROVED = "approved"   # 已通过
    REJECTED = "rejected"   # 已拒绝


class SourceType(str, Enum):
    """来源类型枚举"""
    MANUAL = "manual"       # 手动录入
    AI = "ai"              # AI生成
    REFERENCE = "reference" # 参考题改编
    ADAPTED = "adapted"    # 热门题改编


class CognitiveLevel(str, Enum):
    """认知层级枚举 (布鲁姆分类)"""
    L1_REMEMBER = "L1"  # 记忆
    L2_UNDERSTAND = "L2"  # 理解
    L3_APPLY = "L3"    # 运用
    L4_ANALYZE = "L4"  # 分析
    L5_EVALUATE = "L5"  # 评价
    L6_CREATE = "L6"   # 创造


class BatchOperation(str, Enum):
    """批量操作枚举"""
    IMPORT = "import"
    DELETE = "delete"
    UPDATE_STATUS = "update_status"


# ============ 选项与评分标准 ============

class QuestionOption(BaseModel):
    """题目选项"""
    key: str = Field(..., description="选项标识 (A/B/C/D)")
    text: str = Field(..., description="选项内容")


class ScoringCriterion(BaseModel):
    """评分标准"""
    level: str = Field(..., description="得分等级")
    score: float = Field(..., ge=0, description="得分")
    description: str = Field(..., description="等级说明")


# ============ 创建与更新 Schema ============

class QuestionCreate(BaseModel):
    """创建题目请求"""
    content: str = Field(..., min_length=1, max_length=5000, description="题目内容")
    question_type: str = Field(..., pattern="^(single|multiple|fill|essay|calculation)$", description="题型")
    options: Optional[List[QuestionOption]] = Field(None, description="选择题选项")
    answer: Optional[str] = Field(None, description="标准答案")
    has_answer: bool = Field(True, description="是否有预设答案")
    scoring_criteria: Optional[List[ScoringCriterion]] = Field(None, description="评分标准")
    analysis: Optional[str] = Field(None, max_length=2000, description="题目解析")
    difficulty: int = Field(2, ge=1, le=5, description="难度 1-5")
    cognitive_level: Optional[str] = Field(None, pattern="^L[1-6]$", description="认知层级 L1-L6")
    score: float = Field(5.0, ge=0, le=100, description="分值")
    knowledge_points: List[str] = Field(default_factory=list, description="知识点标签")
    error_causes: List[Any] = Field(default_factory=list, description="易错点标注")
    tags: List[str] = Field(default_factory=list, description="自定义标签")
    source: str = Field("manual", description="来源: manual/ai/reference/adapted")
    source_ref: Optional[str] = Field(None, max_length=200, description="来源参考")
    
    @field_validator("options")
    @classmethod
    def validate_options(cls, v, info):
        """验证选项格式"""
        if v and len(v) < 2:
            raise ValueError("选择题至少需要2个选项")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "下列关于二次函数的说法正确的是？",
                "question_type": "single",
                "options": [
                    {"key": "A", "text": "开口向上"},
                    {"key": "B", "text": "开口向下"},
                    {"key": "C", "text": "对称轴是y轴"},
                    {"key": "D", "text": "顶点在原点"}
                ],
                "answer": "A",
                "difficulty": 2,
                "cognitive_level": "L3",
                "knowledge_points": ["二次函数", "性质"],
                "source": "ai"
            }
        }
    }


class QuestionUpdate(BaseModel):
    """更新题目请求"""
    content: Optional[str] = Field(None, min_length=1, max_length=5000)
    question_type: Optional[str] = Field(None, pattern="^(single|multiple|fill|essay|calculation)$")
    options: Optional[List[QuestionOption]] = None
    answer: Optional[str] = None
    has_answer: Optional[bool] = None
    scoring_criteria: Optional[List[ScoringCriterion]] = None
    analysis: Optional[str] = Field(None, max_length=2000)
    difficulty: Optional[int] = Field(None, ge=1, le=5)
    cognitive_level: Optional[str] = Field(None, pattern="^L[1-6]$")
    score: Optional[float] = Field(None, ge=0, le=100)
    knowledge_points: Optional[List[str]] = None
    error_causes: Optional[List[Any]] = None
    tags: Optional[List[str]] = None
    review_status: Optional[str] = Field(None, pattern="^(pending|approved|rejected)$")
    review_comment: Optional[str] = None


# ============ 响应 Schema ============

class QuestionResponse(BaseModel):
    """题目响应"""
    id: UUID
    content: str
    question_type: str
    options: Optional[List[dict]] = None
    answer: Optional[str] = None
    has_answer: bool
    scoring_criteria: Optional[List[dict]] = None
    analysis: Optional[str] = None
    difficulty: int
    cognitive_level: Optional[str] = None
    score: float
    knowledge_points: List[Any]
    error_causes: List[Any] = None
    tags: List[str] = None
    source: str
    source_ref: Optional[str] = None
    review_status: str
    review_comment: Optional[str] = None
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    usage_count: int = 0
    correct_rate: Optional[float] = None
    avg_time: Optional[float] = None
    discrimination: Optional[float] = None
    creator_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class QuestionListResponse(BaseModel):
    """题目列表响应"""
    items: List[QuestionResponse]
    total: int
    page: int
    page_size: int
    pages: int


class SimilarQuestion(BaseModel):
    """相似题目"""
    id: UUID
    content: str
    similarity_score: float
    knowledge_points: List[str] = []


# ============ 查询 Schema ============

class QuestionQuery(BaseModel):
    """题目查询参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    
    # 筛选条件
    question_types: Optional[List[str]] = Field(None, description="题型筛选")
    difficulties: Optional[List[int]] = Field(None, description="难度筛选")
    cognitive_levels: Optional[List[str]] = Field(None, description="认知层级筛选")
    knowledge_points: Optional[List[str]] = Field(None, description="知识点筛选")
    sources: Optional[List[str]] = Field(None, description="来源筛选")
    review_status: Optional[str] = Field(None, description="审核状态")
    has_answer: Optional[bool] = Field(None, description="是否有答案")
    
    # 搜索
    keyword: Optional[str] = Field(None, max_length=100, description="关键词搜索")
    search_fields: List[str] = Field(["content", "answer", "analysis"], description="搜索字段")
    
    # 排序
    sort_by: str = Field("created_at", description="排序字段")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="排序方向")
    
    # 排除已删除
    include_deleted: bool = Field(False, description="包含已删除")


# ============ 批量操作 ============

class QuestionBatchRequest(BaseModel):
    """批量操作请求"""
    operation: str = Field(..., pattern="^(import|delete|update_status)$", description="操作类型")
    question_ids: Optional[List[UUID]] = Field(None, description="题目ID列表")
    data: Optional[dict] = Field(None, description="批量数据")
    file: Optional[str] = Field(None, description="Base64编码文件")


class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    question_ids: List[UUID] = Field(..., min_length=1, description="待删除题目ID")


class BatchUpdateStatusRequest(BaseModel):
    """批量更新状态请求"""
    question_ids: List[UUID] = Field(..., min_length=1)
    review_status: str = Field(..., pattern="^(approved|rejected)$")
    review_comment: Optional[str] = None


# ============ 相似度检测 ============

class SimilarityCheckRequest(BaseModel):
    """相似度检测请求"""
    content: str = Field(..., min_length=10, max_length=5000, description="待检测内容")
    threshold: float = Field(0.8, ge=0, le=1, description="相似度阈值")


class SimilarityCheckResponse(BaseModel):
    """相似度检测响应"""
    is_duplicate: bool
    similarity_score: float
    similar_questions: List[SimilarQuestion] = []


# ============ 题目标注 ============

class AnnotationCreate(BaseModel):
    """创建标注请求"""
    annotation_type: str = Field(..., pattern="^(difficulty|error_cause|cognitive|thinking)$")
    key: str = Field(..., max_length=50)
    value: Any
    confidence: Optional[float] = Field(None, ge=0, le=1)
    annotation_method: str = Field("manual", pattern="^(manual|ai)$")


class AnnotationResponse(BaseModel):
    """标注响应"""
    id: UUID
    question_id: UUID
    annotation_type: str
    key: str
    value: Any
    confidence: Optional[float] = None
    annotated_by: Optional[UUID] = None
    annotation_method: str
    created_at: datetime
    
    model_config = {"from_attributes": True}


# ============ 统计 ============

class QuestionStatistics(BaseModel):
    """题库统计"""
    total_count: int
    today_count: int = 0
    pending_count: int = 0
    by_type: List[dict] = []
    by_difficulty: List[dict] = []
    by_cognitive_level: List[dict] = []
    by_source: List[dict] = []


class DistributionItem(BaseModel):
    """分布项"""
    category: str
    count: int
    percentage: float = 0


class QuestionDistribution(BaseModel):
    """题目分布统计"""
    by_type: List[DistributionItem]
    by_difficulty: List[DistributionItem]
    by_cognitive_level: List[DistributionItem]
    by_source: List[DistributionItem]


# ============ 导入导出 ============

class QuestionImportTemplate(BaseModel):
    """导入模板"""
    questions: List[QuestionCreate]
    import_mode: str = Field("create", pattern="^(create|update|skip)$")
    skip_duplicates: bool = True


class QuestionImportResult(BaseModel):
    """导入结果"""
    total: int
    success: int
    failed: int
    errors: List[str] = []
