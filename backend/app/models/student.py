from datetime import datetime, date
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_no = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    gender = Column(String(10), nullable=True)
    birth_date = Column(DateTime, nullable=True)
    id_card = Column(String(18), nullable=True)
    nation = Column(String(50), nullable=True)
    origin_type = Column(String(20), nullable=True)
    address = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    guardian_name = Column(String(100), nullable=True)
    guardian_phone = Column(String(20), nullable=True)
    enrollment_date = Column(DateTime, nullable=True)
    grade_id = Column(UUID(as_uuid=True), ForeignKey("grades.id"), nullable=True)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=True)
    status = Column(String(20), default="active")
    photo_url = Column(String(500), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    deleted_at = Column(DateTime, nullable=True)

    grade = relationship("Grade", back_populates="students")
    class_obj = relationship("Class", back_populates="students")
