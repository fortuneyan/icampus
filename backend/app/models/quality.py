"""
综合素质记录模型
五维评价：思想品德、学业水平、身心健康、艺术素养、社会实践/劳动教育
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class QualityRecord(Base):
    __tablename__ = "quality_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    dimension = Column(String(50), nullable=False)

    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    evidence_url = Column(String(500), nullable=True)

    self_rating = Column(Integer, nullable=True)
    teacher_rating = Column(Integer, nullable=True)
    final_rating = Column(Integer, nullable=True)

    record_date = Column(DateTime, nullable=True)
    academic_year = Column(String(20), nullable=True)
    semester = Column(String(20), nullable=True)

    status = Column(String(20), default="draft")

    evaluator_id = Column(UUID(as_uuid=True), nullable=True)

    remarks = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_quality_student_dimension", "student_id", "dimension"),
        Index("idx_quality_academic_year", "academic_year", "semester"),
    )
