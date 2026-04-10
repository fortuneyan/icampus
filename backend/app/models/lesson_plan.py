"""
教案模型
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class LessonPlan(Base):
    __tablename__ = "lesson_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    teacher_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    course_id = Column(UUID(as_uuid=True), nullable=True)
    grade_id = Column(UUID(as_uuid=True), nullable=True)

    title = Column(String(200), nullable=False)
    lesson_type = Column(String(50), nullable=True)
    teaching_duration = Column(String(50), nullable=True)

    objectives = Column(Text, nullable=True)
    key_points = Column(Text, nullable=True)
    difficult_points = Column(Text, nullable=True)
    teaching_steps = Column(Text, nullable=True)
    homework = Column(Text, nullable=True)
    reflection = Column(Text, nullable=True)

    attachments = Column(Text, nullable=True)

    status = Column(String(20), default="draft")
    reviewer_id = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_comment = Column(Text, nullable=True)

    academic_year = Column(String(20), nullable=True)
    semester = Column(String(20), nullable=True)

    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_lesson_plan_teacher", "teacher_id"),
        Index("idx_lesson_plan_status", "status"),
    )
