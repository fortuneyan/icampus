from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class RecruitmentPlan(Base):
    __tablename__ = "recruitment_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(200), nullable=False)
    year = Column(Integer, nullable=False)
    grade_id = Column(UUID(as_uuid=True), ForeignKey("grades.id"), nullable=True)
    quota = Column(Integer, default=0)
    enrolled_count = Column(Integer, default=0)
    tuition = Column(Numeric(10, 2), default=0)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    status = Column(String(20), default="draft")
    
    is_public = Column(Boolean, default=False)
    announcement_id = Column(UUID(as_uuid=True), ForeignKey("notifications.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Applicant(Base):
    __tablename__ = "applicants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_name = Column(String(100), nullable=False)
    gender = Column(String(10), nullable=True)
    birth_date = Column(DateTime, nullable=True)
    phone = Column(String(20), nullable=False)
    guardian_name = Column(String(100), nullable=True)
    guardian_phone = Column(String(20), nullable=True)
    id_card = Column(String(18), nullable=True)
    id_card_front = Column(String(500), nullable=True)
    id_card_back = Column(String(500), nullable=True)
    address = Column(String(255), nullable=True)
    current_school = Column(String(200), nullable=True)
    source = Column(String(50), default="offline")
    status = Column(String(20), default="pending")
    recruitment_plan_id = Column(UUID(as_uuid=True), ForeignKey("recruitment_plans.id"), nullable=True)
    is_off_plan = Column(Boolean, default=False)
    application_year = Column(Integer, nullable=True)
    enrollment_batch = Column(String(50), nullable=True)
    remarks = Column(Text, nullable=True)
    is_enrolled = Column(Boolean, default=False)
    enrolled_class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=True)
    enrolled_at = Column(DateTime, nullable=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ApplicantFollowUp(Base):
    __tablename__ = "applicant_follow_ups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    applicant_id = Column(UUID(as_uuid=True), ForeignKey("applicants.id"), nullable=False)
    follow_type = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    next_follow_date = Column(DateTime, nullable=True)
    operator_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
