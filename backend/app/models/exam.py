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
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ExamPaper(Base):
    """试卷模型"""

    __tablename__ = "exam_papers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(200), nullable=False)
    paper_type = Column(String(20), default="practice")
    total_score = Column(Numeric(5, 1), default=100)
    duration = Column(Integer, default=90)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=True)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status = Column(String(20), default="draft")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Question(Base):
    """
    题目模型（扩展版）

    支持题型：
    - single: 单选题
    - multiple: 多选题
    - fill: 填空题
    - essay: 解答题
    - calculation: 计算题
    """

    __tablename__ = "questions"

    # 主键
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 题目内容
    content = Column(Text, nullable=False, comment="题目内容")
    question_type = Column(String(20), nullable=False, comment="题型")
    options = Column(JSON, comment="选择题选项")

    # 答案相关
    answer = Column(Text, comment="标准答案")
    has_answer = Column(Boolean, default=True, comment="是否有预设答案")
    scoring_criteria = Column(JSON, comment="评分标准")

    # 元数据
    analysis = Column(Text, comment="题目解析")
    difficulty = Column(Integer, default=2, comment="难度 1-5")
    cognitive_level = Column(String(20), comment="认知层级 L1-L6")
    score = Column(Numeric(5, 1), default=5.0, comment="分值")

    # 标注信息
    knowledge_points = Column(JSON, default=list, comment="知识点标签")
    error_causes = Column(JSON, default=list, comment="易错点标注")
    tags = Column(JSON, default=list, comment="自定义标签")

    # 来源与审核
    source = Column(String(20), default="manual", comment="来源")
    source_ref = Column(String(200), comment="来源参考")
    review_status = Column(String(20), default="pending", comment="审核状态")
    review_comment = Column(Text, comment="审核意见")
    reviewed_by = Column(UUID, comment="审核人")
    reviewed_at = Column(DateTime, comment="审核时间")

    # 质量指标
    usage_count = Column(Integer, default=0, comment="使用次数")
    correct_rate = Column(Numeric(5, 2), comment="正确率")
    avg_time = Column(Numeric(5, 1), comment="平均作答时间")
    discrimination = Column(Numeric(5, 2), comment="区分度")

    # 相似度
    similarity_hash = Column(String(64), comment="相似度哈希")

    # 审计字段
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = Column(Boolean, default=False, comment="软删除")

    # 索引
    __table_args__ = (
        Index("idx_question_type", "question_type"),
        Index("idx_difficulty", "difficulty"),
        Index("idx_review_status", "review_status"),
        Index("idx_created_at", "created_at"),
        Index("idx_is_deleted", "is_deleted"),
    )

    # 关系
    annotations = relationship(
        "QuestionAnnotation", back_populates="question", cascade="all, delete-orphan"
    )


class QuestionAnnotation(Base):
    """题目标注文模型"""

    __tablename__ = "question_annotations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    question_id = Column(
        UUID, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )

    annotation_type = Column(String(30), nullable=False, comment="标注类型")
    key = Column(String(50), comment="标注键")
    value = Column(JSON, comment="标注值")
    confidence = Column(Numeric(3, 2), comment="置信度")

    annotated_by = Column(UUID, ForeignKey("users.id"))
    annotation_method = Column(String(20), default="manual")

    created_at = Column(DateTime, default=datetime.now)

    # 关系
    question = relationship("Question", back_populates="annotations")

    __table_args__ = (Index("idx_annotation_question_id", "question_id"),)


class PaperQuestion(Base):
    """试卷-题目关联表"""

    __tablename__ = "paper_questions"

    paper_id = Column(
        UUID(as_uuid=True), ForeignKey("exam_papers.id"), primary_key=True
    )
    question_id = Column(
        UUID(as_uuid=True), ForeignKey("questions.id"), primary_key=True
    )
    order_num = Column(Integer, default=0)
    score = Column(Numeric(5, 1), default=5)


class SimilarityCheckRecord(Base):
    """相似度检测记录"""

    __tablename__ = "similarity_check_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    content_hash = Column(String(64))
    content_preview = Column(Text)
    is_duplicate = Column(Boolean, default=False)
    similarity_score = Column(Numeric(5, 4))
    similar_question_ids = Column(JSON)
    threshold = Column(Numeric(3, 2), default=0.8)
    checked_by = Column(UUID)
    checked_at = Column(DateTime, default=datetime.now)
