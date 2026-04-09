from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Grade(Base):
    __tablename__ = "grades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    academic_year = Column(String(20), nullable=False)
    year = Column(Integer, nullable=True)
    grade_level = Column(Integer, nullable=True)
    head_teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    student_count = Column(Integer, default=0)
    class_count = Column(Integer, default=0)
    status = Column(String(20), default="active")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    students = relationship("Student", back_populates="grade")
    classes = relationship("Class", back_populates="grade")
