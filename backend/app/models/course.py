from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=True)
    credit = Column(Numeric(3, 1), nullable=True)
    hours = Column(Integer, nullable=True)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    grade_id = Column(UUID(as_uuid=True), ForeignKey("grades.id"), nullable=True)
    semester = Column(String(20), nullable=True)
    exam_type = Column(String(20), nullable=True)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
