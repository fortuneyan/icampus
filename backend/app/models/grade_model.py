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
    enrollment_year = Column(Integer, nullable=True, index=True)
    head_teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    student_count = Column(Integer, default=0)
    class_count = Column(Integer, default=0)
    status = Column(String(20), default="active")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    students = relationship("Student", back_populates="grade")
    classes = relationship("Class", back_populates="grade")

    @property
    def display_name(self) -> str:
        """显示名称: YYYY级"""
        if self.enrollment_year:
            return f"{self.enrollment_year}级"
        return self.name

    @property
    def display_code(self) -> str:
        """显示编号: GYY"""
        if self.enrollment_year and self.grade_level:
            year_suffix = str(self.enrollment_year)[-2:]
            return f"G{year_suffix}"
        return self.code

    @property
    def semester(self) -> str:
        """当前学期: 上半年/下半年"""
        month = datetime.now().month
        if month >= 7:
            return "下学期"
        return "上学期"

    @property
    def semester_label(self) -> str:
        """学期标签"""
        now = datetime.now()
        year = now.year
        return f"{year}{self.semester}"

    @property
    def current_grade_level(self) -> int:
        """当前学期应计算的实际年级

        上半年(1-6月): 当前年份 - 入学年份
        下半年(7-12月): 当前年份 - 入学年份 + 1
        """
        if not self.enrollment_year:
            return 0

        now = datetime.now()
        current_year = now.year
        month = now.month

        if month >= 7:
            return current_year - self.enrollment_year + 1
        else:
            return current_year - self.enrollment_year
