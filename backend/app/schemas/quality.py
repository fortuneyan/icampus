"""
题库质量评分模块 - Pydantic Schema

包含：
1. QualityEvaluationRequest - 质量评估请求
2. QualityEvaluationResponse - 质量评估响应
3. DimensionScore - 维度评分
4. BatchEvaluateRequest - 批量评估请求
5. BatchEvaluateResponse - 批量评估响应
6. QualityScoreResponse - 评分详情响应
7. QualityScoreQuery - 评分查询
8. ReviewQueueItem - 审核队列项
9. ReviewQueueQuery - 审核队列查询
10. ReviewDecision - 审核决策
11. QualityStatistics - 质量统计
"""
from typing import Optional, List, Any, Dict
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from enum import Enum


# ============ 枚举定义 ============

class QualityLevelEnum(str, Enum):
    """质量等级"""
    A = "A"  # 优秀
    B = "B"  # 良好
    C = "C"  # 一般
    D = "D"  # 较差


class ApprovalSuggestionEnum(str, Enum):
    """审批建议"""
    AUTO_APPROVE = "auto_approve"
    CONDITIONAL_PASS = "conditional_pass"
    NEEDS_REVIEW = "needs_review"
    AUTO_REJECT = "auto_reject"


class ReviewPriorityEnum(str, Enum):
    """审核优先级"""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class EvaluationModeEnum(str, Enum):
    """评估模式"""
    STANDARD = "standard"
    STRICT = "strict"


class ReviewDecisionType(str, Enum):
    """审核决定"""
    APPROVE = "approve"
    REJECT = "reject"
    REVISE = "revise"
    PENDING = "pending"


class ReviewStatusEnum(str, Enum):
    """审核状态"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# ============ 评估请求与响应 ============

class QuestionOption(BaseModel):
    """题目选项"""
    key: str = Field(..., description="选项标识")
    text: str = Field(..., description="选项内容")


class DimensionScore(BaseModel):
    """维度评分"""
    score: float = Field(..., ge=0, le=1, description="评分 0-1")
    reason: str = Field(..., description="评分理由")


class QualityEvaluationRequest(BaseModel):
    """质量评估请求"""
    question_id: Optional[UUID] = Field(None, description="题目ID（有则更新，无则新建）")
    question_content: str = Field(..., min_length=1, max_length=5000, description="题目内容")
    question_type: str = Field(..., pattern="^(single|multiple|fill|essay|calculation)$", description="题型")
    options: Optional[List[QuestionOption]] = Field(None, description="选择题选项")
    answer: Optional[str] = Field(None, description="标准答案")
    difficulty: int = Field(1, ge=1, le=5, description="题目难度")
    cognitive_level: Optional[str] = Field(None, pattern="^L[1-6]$", description="认知层级")
    knowledge_points: List[str] = Field(default_factory=list, description="知识点")
    tags: List[str] = Field(default_factory=list, description="标签")
    has_answer: bool = Field(True, description="是否有预设答案")
    scoring_criteria: Optional[List[Dict]] = Field(None, description="评分标准")
    source: str = Field("manual", description="题目来源")
    evaluation_mode: str = Field("standard", pattern="^(standard|strict)$", description="评估模式")

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
                "question_content": "下列关于二次函数的说法正确的是？",
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
                "source": "ai",
                "evaluation_mode": "standard"
            }
        }
    }


class DimensionScoresResponse(BaseModel):
    """维度评分响应"""
    difficulty: DimensionScore
    clarity: DimensionScore
    cognitive: DimensionScore
    discrimination: DimensionScore
    authenticity: DimensionScore
    answer: DimensionScore


class QualityEvaluationResponse(BaseModel):
    """质量评估响应"""
    question_id: Optional[UUID] = None
    quality_score_id: Optional[UUID] = None
    
    # 综合评分
    overall_score: float = Field(..., ge=0, le=1, description="综合评分 0-1")
    quality_level: str = Field(..., pattern="^[A-D]$", description="质量等级")
    
    # 维度评分
    dimension_scores: Dict[str, DimensionScore]
    
    # 建议
    quality_suggestion: Optional[str] = Field(None, description="质量改进建议")
    approval_suggestion: str = Field(..., description="入库审批建议")
    
    # 评估信息
    evaluation_mode: str
    evaluation_model: Optional[str] = None
    evaluation_time_ms: Optional[int] = None
    
    # 缓存标识
    cached: bool = False

    model_config = {"from_attributes": True}


# ============ 评分查询与响应 ============

class QualityScoreQuery(BaseModel):
    """评分查询参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    
    # 筛选条件
    quality_levels: Optional[List[str]] = Field(None, description="质量等级筛选")
    approval_suggestions: Optional[List[str]] = Field(None, description="审批建议筛选")
    question_types: Optional[List[str]] = Field(None, description="题型筛选")
    sources: Optional[List[str]] = Field(None, description="来源筛选")
    min_score: Optional[float] = Field(None, ge=0, le=1, description="最低评分")
    max_score: Optional[float] = Field(None, ge=0, le=1, description="最高评分")
    
    # 审核状态
    reviewed: Optional[bool] = Field(None, description="是否已审核")
    
    # 排序
    sort_by: str = Field("created_at", description="排序字段")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="排序方向")


class QualityScoreItem(BaseModel):
    """评分项"""
    id: UUID
    question_id: UUID
    question_content: str
    question_type: Optional[str]
    difficulty: Optional[int]
    
    overall_score: float
    quality_level: str
    
    difficulty_score: float
    clarity_score: float
    cognitive_score: float
    discrimination_score: float
    authenticity_score: float
    answer_score: float
    
    approval_suggestion: Optional[str]
    quality_suggestion: Optional[str]
    
    source: str
    reviewed: bool
    reviewed_by: Optional[UUID]
    reviewed_at: Optional[datetime]
    
    evaluation_model: Optional[str]
    created_at: datetime
    
    model_config = {"from_attributes": True}


class QualityScoreListResponse(BaseModel):
    """评分列表响应"""
    items: List[QualityScoreItem]
    total: int
    page: int
    page_size: int
    pages: int


class QualityScoreResponse(BaseModel):
    """评分详情响应"""
    id: UUID
    question_id: UUID
    question_content: str
    question_type: Optional[str]
    difficulty: Optional[int]
    cognitive_level: Optional[str]
    knowledge_points: Optional[List[str]]
    has_answer: bool
    source: str
    
    # 维度评分
    difficulty_score: float
    difficulty_reason: Optional[str]
    
    clarity_score: float
    clarity_reason: Optional[str]
    
    cognitive_score: float
    cognitive_level_evaluated: Optional[str]
    cognitive_reason: Optional[str]
    
    discrimination_score: float
    discrimination_reason: Optional[str]
    
    authenticity_score: float
    authenticity_reason: Optional[str]
    
    answer_score: float
    answer_reason: Optional[str]
    
    # 综合评分
    overall_score: float
    quality_level: str
    quality_suggestion: Optional[str]
    approval_suggestion: Optional[str]
    
    # 评估信息
    evaluation_mode: str
    evaluation_model: Optional[str]
    evaluation_tokens: Optional[int]
    evaluation_time_ms: Optional[int]
    
    # 审核信息
    reviewed: bool
    reviewed_by: Optional[UUID]
    reviewed_at: Optional[datetime]
    review_decision: Optional[str]
    review_comment: Optional[str]
    
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# ============ 批量评估 ============

class BatchEvaluateRequest(BaseModel):
    """批量评估请求"""
    question_ids: List[UUID] = Field(..., min_length=1, max_length=100, description="题目ID列表")
    evaluation_mode: str = Field("standard", pattern="^(standard|strict)$", description="评估模式")
    auto_approve_threshold: float = Field(0.90, ge=0, le=1, description="自动通过阈值")
    auto_reject_threshold: float = Field(0.40, ge=0, le=1, description="自动拒绝阈值")
    update_existing: bool = Field(True, description="是否更新已有评分")


class BatchEvaluateResult(BaseModel):
    """批量评估单项结果"""
    question_id: UUID
    overall_score: Optional[float] = None
    quality_level: Optional[str] = None
    status: str = Field(..., description="completed/failed/skipped")
    error: Optional[str] = None


class BatchEvaluateResponse(BaseModel):
    """批量评估响应"""
    total: int
    completed: int
    pending: int
    failed: int
    auto_approved: int
    auto_rejected: int
    results: List[BatchEvaluateResult]


# ============ 审核队列 ============

class ReviewQueueQuery(BaseModel):
    """审核队列查询"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    
    # 筛选
    priority: Optional[str] = Field(None, pattern="^(high|normal|low)$", description="优先级")
    quality_levels: Optional[List[str]] = Field(None, description="质量等级")
    sources: Optional[List[str]] = Field(None, description="来源")
    
    # 排序
    sort_by: str = Field("priority", description="排序字段")
    sort_order: str = Field("asc", pattern="^(asc|desc)$", description="排序方向")


class ReviewQueueItem(BaseModel):
    """审核队列项"""
    question_id: UUID
    question_content: str
    question_type: str
    difficulty: Optional[int]
    source: str
    
    # 质量评分
    quality_score_id: UUID
    quality_score: float
    quality_level: str
    
    # 维度评分摘要
    dimension_summary: Dict[str, float]
    
    # 审核信息
    priority: str
    queue_position: int
    
    # 来源信息
    ai_generated: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}


class ReviewQueueResponse(BaseModel):
    """审核队列响应"""
    items: List[ReviewQueueItem]
    total: int
    page: int
    page_size: int
    pages: int


class ReviewDecision(BaseModel):
    """审核决策"""
    question_id: UUID
    decision: str = Field(..., pattern="^(approve|reject|revise)$", description="审核决定")
    review_comment: Optional[str] = Field(None, max_length=500, description="审核意见")
    
    # 可选：手动调整评分
    adjusted_score: Optional[float] = Field(None, ge=0, le=1, description="调整后评分")
    override_reason: Optional[str] = Field(None, description="调整原因")


class ReviewDecisionResponse(BaseModel):
    """审核决策响应"""
    success: bool
    question_id: UUID
    decision: str
    review_record_id: Optional[UUID] = None
    message: str


# ============ 质量统计 ============

class QualityDistributionItem(BaseModel):
    """质量分布项"""
    category: str
    count: int
    percentage: float


class QualityStatistics(BaseModel):
    """质量统计"""
    # 总量
    total_evaluated: int = 0
    pending_review: int = 0
    reviewed: int = 0
    
    # 通过率
    pass_rate: float = 0.0
    auto_approve_rate: float = 0.0
    auto_reject_rate: float = 0.0
    
    # 质量分布
    by_level: List[QualityDistributionItem]
    by_source: List[QualityDistributionItem]
    by_type: List[QualityDistributionItem]
    
    # 平均分
    avg_overall_score: float = 0.0
    avg_difficulty_score: float = 0.0
    avg_clarity_score: float = 0.0
    avg_cognitive_score: float = 0.0
    
    # 趋势（近7天）
    trend: Dict[str, List[Dict]]


# ============ 评估 Prompt ============

class EvaluationPromptRequest(BaseModel):
    """评估提示词请求"""
    name: str = Field(..., max_length=100, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    system_prompt: str = Field(..., min_length=10, description="系统提示词")
    user_prompt_template: str = Field(..., min_length=10, description="用户提示词模板")
    dimensions: Optional[Dict] = Field(None, description="评估维度")
    scoring_rules: Optional[Dict] = Field(None, description="评分规则")
    level_thresholds: Optional[Dict] = Field(None, description="等级阈值")
    question_types: Optional[List[str]] = Field(None, description="适用题型")
    evaluation_modes: Optional[List[str]] = Field(None, description="适用模式")
    is_active: bool = Field(True, description="是否启用")


class EvaluationPromptResponse(BaseModel):
    """评估提示词响应"""
    id: UUID
    name: str
    description: Optional[str]
    system_prompt: str
    user_prompt_template: str
    dimensions: Optional[Dict]
    scoring_rules: Optional[Dict]
    level_thresholds: Optional[Dict]
    question_types: Optional[List[str]]
    evaluation_modes: Optional[List[str]]
    is_active: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}
