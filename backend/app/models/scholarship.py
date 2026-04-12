"""
奖助学金模型
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Scholarship(Base):
    """奖学金项目"""
    __tablename__ = "scholarships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    scholarship_no = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    
    scholarship_type = Column(String(20), nullable=False)  # scholarship/grant/aid
    level = Column(String(20), nullable=True)  # national/school/society
    source = Column(String(100), nullable=True)
    
    amount = Column(Integer, nullable=False)  # 金额（分）
    quota = Column(Integer, nullable=True)  # 名额
    
    academic_year = Column(String(20), nullable=False)
    semester = Column(String(20), nullable=True)
    
    requirements = Column(Text, nullable=True)
    materials = Column(Text, nullable=True)
    
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    review_date = Column(DateTime, nullable=True)
    
    status = Column(String(20), default="open")  # draft/open/closed
    created_by = Column(UUID(as_uuid=True), nullable=True)
    
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_scholarship_year", "academic_year"),
        Index("idx_scholarship_status", "status"),
    )


class ScholarshipApplication(Base):
    """奖学金申请"""
    __tablename__ = "scholarship_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    scholarship_id = Column(UUID(as_uuid=True), ForeignKey("scholarships.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    academic_year = Column(String(20), nullable=False)
    semester = Column(String(20), nullable=True)
    
    gpa = Column(String(10), nullable=True)  # 平均绩点
    rank = Column(Integer, nullable=True)  # 年级排名
    total_students = Column(Integer, nullable=True)  # 年级总人数
    
    application_reason = Column(Text, nullable=True)
    materials = Column(Text, nullable=True)
    
    status = Column(String(20), default="submitted")  # draft/submitted/reviewing/approved/rejected
    
    reviewer_id = Column(UUID(as_uuid=True), nullable=True)
    review_comment = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_application_scholarship", "scholarship_id"),
        Index("idx_application_student", "student_id"),
        Index("idx_application_status", "status"),
    )


class GrantRecord(Base):
    """资助发放记录"""
    __tablename__ = "grant_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("scholarship_applications.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    scholarship_name = Column(String(200), nullable=False)
    amount = Column(Integer, nullable=False)  # 金额（分）
    
    grant_date = Column(DateTime, nullable=True)
    grant_type = Column(String(20), default="card")  # card/cash/transfer
    grant_account = Column(String(100), nullable=True)
    
    status = Column(String(20), default="pending")  # pending/paid/failed
    paid_by = Column(UUID(as_uuid=True), nullable=True)
    paid_at = Column(DateTime, nullable=True)
    
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class PoorStudent(Base):
    """贫困生认定"""
    __tablename__ = "poor_students"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    
    poor_level = Column(String(20), nullable=True)  # special/ordinary
    poor_type = Column(String(50), nullable=True)  # 困难类型
    
    id_card_no = Column(String(50), nullable=True)
    family_address = Column(Text, nullable=True)
    family_phone = Column(String(50), nullable=True)
    
    annual_income = Column(String(50), nullable=True)
    family_members = Column(Integer, nullable=True)
    
    certificate_no = Column(String(50), nullable=True)
    certificate_url = Column(String(500), nullable=True)
    
    academic_year = Column(String(20), nullable=False)
    status = Column(String(20), default="approved")  # pending/approved/rejected
    
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    remarks = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
