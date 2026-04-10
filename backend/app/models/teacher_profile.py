"""
教师扩展信息模型
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class TeacherProfile(Base):
    __tablename__ = "teacher_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    employee_no = Column(String(50), unique=True, nullable=False, index=True)

    hire_date = Column(DateTime, nullable=True)
    position = Column(String(100), nullable=True)
    title = Column(String(50), nullable=True)
    employment_type = Column(String(20), default="full_time")

    subject = Column(String(50), nullable=True)
    teaching_grade = Column(String(50), nullable=True)

    teacher_certificate = Column(String(50), nullable=True)
    education = Column(String(20), nullable=True)
    degree = Column(String(20), nullable=True)

    emergency_contact = Column(String(100), nullable=True)
    emergency_phone = Column(String(20), nullable=True)

    profile_json = Column(Text, default="{}")
    remarks = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
