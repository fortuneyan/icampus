from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Class(Base):
    __tablename__ = "classes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    grade_id = Column(UUID(as_uuid=True), ForeignKey("grades.id"), nullable=True)
    head_teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    student_count = Column(Integer, default=0)
    room_no = Column(String(50), nullable=True)
    academic_year = Column(String(20), nullable=False)
    semester = Column(String(10), nullable=False)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    grade = relationship("Grade", back_populates="classes")
    students = relationship("Student", back_populates="class_obj")
