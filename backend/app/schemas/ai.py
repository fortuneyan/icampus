"""
AI 相关 Schemas
"""

from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: Optional[UUID] = None
    message: str = Field(..., max_length=4000)
    model_type: str = "deepseek"
    knowledge_base_id: Optional[str] = Field(None, description="知识库ID，用于RAG增强")
    use_rag: bool = Field(False, description="是否启用RAG增强")


class ChatResponse(BaseModel):
    session_id: UUID
    message: str
    created_at: str


class SessionCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    model_type: str = "deepseek"


class SessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: Optional[str] = None
    model_type: str
    status: str
    created_at: str


class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    created_at: str


class AIConfigUpdate(BaseModel):
    model_type: str
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    temperature: int = Field(80, ge=0, le=100)
    max_tokens: int = Field(2000, ge=100, le=4000)
    status: str = "active"


# ==================== 能力画像 ====================


class AbilityDimension(BaseModel):
    """能力维度"""

    name: str  # 维度名称，如 "计算能力"、"逻辑推理"
    score: float = Field(..., ge=0, le=100)  # 得分 0-100
    level: str  # 等级：薄弱/一般/良好/优秀
    trend: str  # 趋势：up/down/stable
    evidence: Optional[List[str]] = None  # 支撑证据


class AbilityProfile(BaseModel):
    """能力画像"""

    student_id: str
    overall_score: float  # 综合能力分
    dimensions: List[AbilityDimension]
    strengths: List[str]  # 优势领域
    weaknesses: List[str]  # 待提升领域
    improvement_suggestions: List[str]
    generated_at: str


# ==================== 知识图谱 ====================


class KnowledgeNode(BaseModel):
    """知识节点"""

    node_id: str
    name: str
    parent_id: Optional[str] = None
    mastery: float = Field(..., ge=0, le=100)  # 掌握度 0-100
    difficulty: float = Field(..., ge=0, le=5)  # 难度 1-5
    importance: float = Field(..., ge=0, le=100)  # 重要度 0-100
    prerequisites: List[str] = []  # 前置知识节点ID
    tags: List[str] = []
    exam_frequency: Optional[float] = None  # 考试频率


class KnowledgeEdge(BaseModel):
    """知识边（节点关系）"""

    source: str  # 源节点ID
    target: str  # 目标节点ID
    relation: str  # 关系：prerequisite/related/same_module


class KnowledgeGraph(BaseModel):
    """知识图谱"""

    student_id: str
    course_id: Optional[str] = None
    course_name: Optional[str] = None
    nodes: List[KnowledgeNode]
    edges: List[KnowledgeEdge]
    weakest_nodes: List[str]  # 最薄弱节点ID列表
    learning_frontier: List[str]  # 最近学习区（可开始学习的节点）
    generated_at: str


# ==================== 能力雷达图 ====================


class RadarIndicator(BaseModel):
    """雷达图指标"""

    name: str
    value: float = Field(..., ge=0, le=100)


class AbilityRadarData(BaseModel):
    """能力雷达图数据"""

    student_id: str
    indicators: List[RadarIndicator]
    avg_score: float  # 平均分
    highest_dimension: str  # 最高分维度
    lowest_dimension: str  # 最低分维度
    comparison_with_class: Optional[float] = None  # 与班级平均比较


# ==================== 诊断报告 ====================


class DiagnosisReportRequest(BaseModel):
    student_id: UUID
    course_id: Optional[UUID] = None
    include_ability: bool = True
    include_knowledge_graph: bool = True
    include_recommendations: bool = True


class DiagnosisReport(BaseModel):
    """综合诊断报告"""

    student_id: str
    report_id: str
    ability_profile: Optional[AbilityProfile] = None
    knowledge_graph: Optional[KnowledgeGraph] = None
    radar_data: Optional[AbilityRadarData] = None
    exam_analysis: Optional[dict] = None  # 考试成绩分析
    recommendations: List[dict]  # 综合建议
    report_date: str


# ==================== AI 出题系统 ====================


class QuestionOption(BaseModel):
    """选择题选项"""

    label: str  # A/B/C/D
    content: str  # 选项内容
    is_correct: bool = False


class QuestionOutput(BaseModel):
    """生成的题目"""

    question_id: Optional[str] = None  # 保存后返回
    content: str  # 题目内容
    question_type: str = "single"  # single/multiple/fill/essay/calculation
    options: Optional[List[QuestionOption]] = None  # 选择题选项
    answer: Optional[str] = None  # 答案（填空/解答）
    analysis: Optional[str] = None  # 解析
    difficulty: int = Field(1, ge=1, le=5)  # 难度 1-5
    score: float = Field(5, ge=0, le=100)  # 分值
    knowledge_points: List[str] = []  # 知识点标签
    source: str = "ai"  # ai/manual
    saved: bool = False  # 是否已保存到数据库


class QuestionSetOutput(BaseModel):
    """生成的题目集"""

    set_id: str  # 题目集标识
    title: str  # 集标题
    course_name: str  # 课程名称
    grade_level: str  # 年级
    topic: str  # 课题
    total_count: int  # 总题数
    questions: List[QuestionOutput]  # 题目列表
    generated_at: str  # 生成时间
    saved_count: int = 0  # 已保存到数据库的题目数


class QuestionGenerateRequest(BaseModel):
    """AI 出题请求"""

    course_name: str = Field(..., description="课程名称")
    grade_level: str = Field(..., description="年级")
    topic: str = Field(..., description="课题/知识点")
    question_types: List[str] = Field(
        default=["single"],
        description="题型列表: single/multiple/fill/essay/calculation",
    )
    difficulty: int = Field(default=2, ge=1, le=5, description="难度 1-5")
    count: int = Field(default=5, ge=1, le=50, description="题目数量")
    knowledge_points: Optional[List[str]] = Field(
        default=None, description="指定知识点"
    )
    requirements: Optional[str] = Field(default=None, description="特殊要求")
