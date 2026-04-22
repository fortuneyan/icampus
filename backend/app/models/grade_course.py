from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.core.database import Base


class SelectionTargetType(str, enum.Enum):
    GRADE = "grade"
    CLASS = "class"
    STUDENT = "student"


class CourseType(str, enum.Enum):
    REQUIRED = "REQUIRED"
    ELECTIVE = "ELECTIVE"


class GradeCourseSettings(Base):
    __tablename__ = "grade_course_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    grade_level = Column(Integer, nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    course_type = Column(SQLEnum(CourseType), default=CourseType.ELECTIVE, nullable=False)
    academic_year = Column(String(20), nullable=True)
    semester = Column(String(20), nullable=True)
    is_active = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class CourseSelection(Base):
    __tablename__ = "course_selections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)

    target_type = Column(SQLEnum(SelectionTargetType), nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=False)

    academic_year = Column(String(20), nullable=True)
    semester = Column(String(20), nullable=True)
    status = Column(String(20), default="pending")

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
