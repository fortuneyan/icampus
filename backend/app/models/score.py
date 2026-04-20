from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Score(Base):
    __tablename__ = "scores"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "course_id", "semester", "exam_type", name="uq_score"
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    semester = Column(String(20), nullable=True)
    exam_type = Column(String(20), nullable=True)
    score = Column(Numeric(5, 2), nullable=True)
    full_score = Column(Numeric(5, 2), default=100)
    grade_letter = Column(String(5), nullable=True)
    rank = Column(Integer, nullable=True)
    exam_date = Column(DateTime, nullable=True)
    remarks = Column(String(500), nullable=True)
    recorded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    recorded_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
