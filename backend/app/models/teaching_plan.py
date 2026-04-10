"""
教学计划模型
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class TeachingPlan(Base):
    __tablename__ = "teaching_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    teacher_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    course_id = Column(UUID(as_uuid=True), nullable=True)
    grade_id = Column(UUID(as_uuid=True), nullable=True)

    title = Column(String(200), nullable=False)
    objectives = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    methodology = Column(Text, nullable=True)

    total_periods = Column(String(50), nullable=True)
    academic_year = Column(String(20), nullable=True)
    semester = Column(String(20), nullable=True)

    status = Column(String(20), default="draft")
    approver_id = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approval_comment = Column(Text, nullable=True)

    attachments = Column(Text, nullable=True)
    remarks = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_teaching_plan_teacher", "teacher_id"),
        Index("idx_teaching_plan_status", "status"),
    )
