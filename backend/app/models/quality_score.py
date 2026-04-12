"""
题库质量评分模块 - 数据模型

包含：
1. QuestionQualityScore - 题目质量评分模型
2. QualityReviewRecord - 审核记录模型
3. QualityStatistics - 质量统计聚合
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
    Numeric,
    JSON,
    Boolean,
    Index,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from enum import Enum

from app.core.database import Base


class QualityLevel(str, Enum):
    """质量等级枚举"""
    A_EXCELLENT = "A"  # 优秀：>=0.90
    B_GOOD = "B"       # 良好：>=0.75
    C_AVERAGE = "C"     # 一般：>=0.55
    D_POOR = "D"       # 较差：<0.55


class ApprovalSuggestion(str, Enum):
    """审批建议枚举"""
    AUTO_APPROVE = "auto_approve"       # 自动通过
    CONDITIONAL_PASS = "conditional_pass"  # 有条件通过
    NEEDS_REVIEW = "needs_review"       # 需要人工审核
    AUTO_REJECT = "auto_reject"         # 自动拒绝


class ReviewPriority(str, Enum):
    """审核优先级"""
    HIGH = "high"       # 高优先级
    NORMAL = "normal"   # 正常
    LOW = "low"         # 低优先级


class EvaluationMode(str, Enum):
    """评估模式"""
    STANDARD = "standard"  # 标准评估
    STRICT = "strict"      # 严格评估


class QuestionQualityScore(Base):
    """
    题目质量评分模型

    记录每个题目的AI质量评估结果，包含6个维度的评分：
    1. difficulty_score - 难度适当性
    2. clarity_score - 表述清晰度
    3. cognitive_score - 认知层级匹配度
    4. discrimination_score - 区分度
    5. authenticity_score - 原创性/真实性
    6. answer_score - 答案准确性
    """
    __tablename__ = "question_quality_scores"

    # 主键与关联
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    question_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("questions.id", ondelete="CASCADE"), 
        nullable=False,
        unique=True,
        comment="关联题目ID"
    )
    
    # 题目基本信息（冗余存储，便于查询）
    question_content = Column(Text, nullable=False, comment="题目内容摘要")
    question_type = Column(String(20), comment="题型")
    difficulty = Column(Integer, comment="题目原始难度")
    cognitive_level = Column(String(10), comment="认知层级")
    knowledge_points = Column(JSON, comment="知识点")
    has_answer = Column(Boolean, default=True, comment="是否有答案")
    source = Column(String(20), default="manual", comment="题目来源")

    # ============ 难度适当性评分 ============
    difficulty_score = Column(
        Numeric(4, 2), 
        nullable=False, 
        comment="难度适当性评分 0-1"
    )
    difficulty_reason = Column(Text, comment="难度评分理由")

    # ============ 表述清晰度评分 ============
    clarity_score = Column(
        Numeric(4, 2), 
        nullable=False, 
        comment="表述清晰度评分 0-1"
    )
    clarity_reason = Column(Text, comment="清晰度评分理由")

    # ============ 认知层级评分 ============
    cognitive_score = Column(
        Numeric(4, 2), 
        nullable=False, 
        comment="认知层级匹配度评分 0-1"
    )
    cognitive_level_evaluated = Column(String(10), comment="评估的认知层级")
    cognitive_reason = Column(Text, comment="认知层级评分理由")

    # ============ 区分度评分 ============
    discrimination_score = Column(
        Numeric(4, 2), 
        nullable=False, 
        comment="区分度评分 0-1"
    )
    discrimination_reason = Column(Text, comment="区分度评分理由")

    # ============ 原创性评分 ============
    authenticity_score = Column(
        Numeric(4, 2), 
        nullable=False, 
        comment="原创性/真实性评分 0-1"
    )
    authenticity_reason = Column(Text, comment="原创性评分理由")

    # ============ 答案准确性评分 ============
    answer_score = Column(
        Numeric(4, 2), 
        nullable=False, 
        comment="答案准确性评分 0-1"
    )
    answer_reason = Column(Text, comment="答案评分理由")

    # ============ 综合评分 ============
    overall_score = Column(
        Numeric(4, 2), 
        nullable=False, 
        comment="综合质量评分 0-1"
    )
    quality_level = Column(
        String(1), 
        nullable=False, 
        comment="质量等级 A/B/C/D"
    )
    quality_suggestion = Column(Text, comment="质量改进建议")
    
    # 审批建议
    approval_suggestion = Column(
        String(30), 
        comment="入库审批建议"
    )

    # ============ 评估元数据 ============
    evaluation_mode = Column(
        String(20), 
        default="standard", 
        comment="评估模式"
    )
    evaluation_model = Column(
        String(50), 
        comment="评估使用的模型"
    )
    evaluation_tokens = Column(
        Integer, 
        comment="评估消耗的token数"
    )
    evaluation_time_ms = Column(
        Integer, 
        comment="评估耗时(毫秒)"
    )

    # ============ 审核信息 ============
    reviewed = Column(Boolean, default=False, comment="是否已审核")
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), comment="审核人")
    reviewed_at = Column(DateTime, comment="审核时间")
    review_decision = Column(String(20), comment="审核决定")
    review_comment = Column(Text, comment="审核意见")

    # ============ 审计字段 ============
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    question = relationship("Question", backref="quality_score")
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    # 索引
    __table_args__ = (
        Index("idx_quality_question_id", "question_id"),
        Index("idx_quality_level", "quality_level"),
        Index("idx_quality_score", "overall_score"),
        Index("idx_quality_reviewed", "reviewed"),
        Index("idx_quality_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<QualityScore(question={self.question_id}, level={self.quality_level}, score={self.overall_score})>"


class QualityReviewRecord(Base):
    """
    质量审核记录模型
    
    记录每次人工审核的操作历史
    """
    __tablename__ = "quality_review_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    quality_score_id = Column(
        UUID(as_uuid=True),
        ForeignKey("question_quality_scores.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联评分ID"
    )
    question_id = Column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联题目ID"
    )

    # 审核前状态
    previous_score = Column(Numeric(4, 2), comment="审核前评分")
    previous_level = Column(String(1), comment="审核前等级")
    previous_decision = Column(String(20), comment="审核前决定")

    # 审核后状态
    new_score = Column(Numeric(4, 2), comment="审核后评分")
    new_level = Column(String(1), comment="审核后等级")
    decision = Column(String(20), nullable=False, comment="审核决定")

    # 审核详情
    review_type = Column(String(20), default="manual", comment="审核类型")
    override_reason = Column(Text, comment="修改原因")
    review_comment = Column(Text, comment="审核意见")

    # 审核人
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 审计
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    reviewer = relationship("User", foreign_keys=[reviewer_id])

    __table_args__ = (
        Index("idx_review_record_question_id", "question_id"),
        Index("idx_review_record_score_id", "quality_score_id"),
        Index("idx_review_record_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<ReviewRecord(score={self.id}, decision={self.decision})>"


class QualityEvaluationPrompt(Base):
    """
    质量评估提示词模板
    
    存储可配置的评估提示词模板
    """
    __tablename__ = "quality_evaluation_prompts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    name = Column(String(100), nullable=False, unique=True, comment="模板名称")
    description = Column(Text, comment="模板描述")
    
    # 提示词内容
    system_prompt = Column(Text, nullable=False, comment="系统提示词")
    user_prompt_template = Column(Text, nullable=False, comment="用户提示词模板")
    
    # 评估维度配置
    dimensions = Column(JSON, comment="评估维度配置")
    
    # 评分规则
    scoring_rules = Column(JSON, comment="评分规则")
    
    # 质量等级阈值
    level_thresholds = Column(JSON, comment="等级阈值配置")
    
    # 使用范围
    question_types = Column(JSON, comment="适用的题型")
    evaluation_modes = Column(JSON, comment="适用的评估模式")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 审计
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_prompt_name", "name"),
        Index("idx_prompt_active", "is_active"),
    )

    def __repr__(self):
        return f"<EvaluationPrompt(name={self.name})>"
