from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Numeric, Text, Table, ForeignKeyConstraint, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class CourseType(str, enum.Enum):
    REQUIRED = "REQUIRED"   # 必修
    ELECTIVE = "ELECTIVE"  # 选修


class Course(Base):
    __tablename__ = "courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=True)
    credit = Column(Numeric(3, 1), nullable=True)
    hours = Column(Integer, nullable=True)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    teacher_ids = Column(ARRAY(UUID), default=[], nullable=True)
    grade_id = Column(UUID(as_uuid=True), ForeignKey("grades.id"), nullable=True)
    semester = Column(String(20), nullable=True)
    exam_type = Column(String(20), nullable=True)
    status = Column(String(20), default="active")

    grade_levels = Column(ARRAY(Integer), default=[], nullable=True)
    course_type = Column(SQLEnum(CourseType), default=CourseType.REQUIRED, nullable=True)
    prerequisite_course_ids = Column(ARRAY(UUID), default=[], nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    @property
    def teacher_list(self):
        if self.teacher_ids and len(self.teacher_ids) > 0:
            return self.teacher_ids
        elif self.teacher_id:
            return [self.teacher_id]
        return []
