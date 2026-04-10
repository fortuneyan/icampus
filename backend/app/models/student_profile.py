"""
学生扩展信息模型
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    student_no = Column(String(50), unique=True, nullable=False, index=True)

    enrollment_date = Column(DateTime, nullable=True)
    graduation_date = Column(DateTime, nullable=True)
    student_status = Column(String(20), default="active")

    guardian_name = Column(String(100), nullable=True)
    guardian_phone = Column(String(20), nullable=True)
    guardian_id_card = Column(String(18), nullable=True)
    guardian_relation = Column(String(20), nullable=True)

    province = Column(String(50), nullable=True)
    city = Column(String(50), nullable=True)
    district = Column(String(50), nullable=True)
    address = Column(String(255), nullable=True)

    is_left_behind = Column(Boolean, default=False)
    is_orphan = Column(Boolean, default=False)
    is_disabled = Column(Boolean, default=False)
    is_poor = Column(Boolean, default=False)

    profile_json = Column(Text, default="{}")
    remarks = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
