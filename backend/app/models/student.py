from datetime import datetime, date
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def get_current_academic_year() -> str:
    """获取当前学年，格式: 2025-2026"""
    now = datetime.now()
    year = now.year
    month = now.month
    if month >= 8:
        return f"{year}-{year + 1}"
    return f"{year - 1}-{year}"


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
    enrollment_type = Column(String(20), default="regular")
    grade_id = Column(UUID(as_uuid=True), ForeignKey("grades.id"), nullable=True)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=True)
    status = Column(String(20), default="active")
    photo_url = Column(String(500), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    deleted_at = Column(DateTime, nullable=True)

    enrollment_status = Column(String(20), default="in_school", index=True)
    student_type = Column(String(20), default="regular")
    enrollment_year = Column(Integer, nullable=True, index=True)
    academic_year = Column(String(20), nullable=True)
    graduation_year = Column(Integer, nullable=True)
    diploma_no = Column(String(50), nullable=True)
    last_change_date = Column(DateTime, nullable=True)

    grade = relationship("Grade", back_populates="students")
    class_obj = relationship("Class", back_populates="students")
    class_history = relationship("StudentClassHistory", back_populates="student")
    enrollment_changes = relationship("EnrollmentChange", back_populates="student")

    @property
    def grade_level(self) -> int:
        """根据班级所在年级计算年级（优先按班级）

        学期计算:
        - 上半年(1-6月): 当前年份 - 入学年份 + 1
        - 下半年(7-12月): 当前年份 - 入学年份 + 2

        例如:
        - 2024年秋季入学
        - 2025年上半年 = 2 - 2024 + 1 = 1年级
        - 2025年下半年 = 2 - 2024 + 2 = 2年级
        """
        if self.enrollment_status in ("graduated", "leave"):
            return 0

        if self.class_obj and self.class_obj.grade:
            return self.class_obj.grade.grade_level or 0

        if self.grade:
            return self.grade.grade_level or 0

        if not self.enrollment_year:
            return 0

        now = datetime.now()
        current_year = now.year
        month = now.month

        if month >= 7:
            grade_level = current_year - self.enrollment_year + 2
        else:
            grade_level = current_year - self.enrollment_year + 1

        return max(1, grade_level)

    @property
    def grade_name(self) -> str:
        """按班级获取年级名称: 根据所属班级显示年级"""
        if self.enrollment_status == "graduated":
            return f"{self.graduation_year}届"
        if self.enrollment_status == "leave":
            return "离校"

        if self.class_obj and self.class_obj.grade:
            return self.class_obj.grade.name or ""

        if self.grade:
            return self.grade.name or ""

        level = self.grade_level
        if level == 0:
            return "未知"
        return f"{level}年级"

    @property
    def semester(self) -> str:
        """当前学期: 上半年/下半年"""
        month = datetime.now().month
        if month >= 7:
            return "下半年"
        return "上半年"

    @property
    def semester_label(self) -> str:
        """学期标签: 如"2025上半年" """
        now = datetime.now()
        year = now.year
        semester = self.semester
        return f"{year}{semester}"

    @property
    def grade_display(self) -> str:
        """完整年级显示: 如"2025上半年 1年级" """
        if not self.enrollment_year:
            return "未入学"

        if self.enrollment_status == "graduated":
            return f"{self.graduation_year}届"
        if self.enrollment_status == "leave":
            return "离校"

        return f"{self.semester_label} {self.grade_level}年级"

    @property
    def enrollment_cohort(self) -> str:
        """获取届别标识

        已毕业: 显示 毕业年份（如2024届）
        离校: 显示 离校
        在校生: 不显示
        """
        if self.enrollment_status == "graduated":
            return f"{self.graduation_year}届" if self.graduation_year else "已毕业"
        if self.enrollment_status == "leave":
            return "离校"

        return ""

    @property
    def calculated_grade_info(self) -> dict:
        """获取完整的年级计算信息"""
        return {
            "grade_level": self.grade_level,
            "grade_name": self.grade_name,
            "enrollment_cohort": self.enrollment_cohort,
            "enrollment_year": self.enrollment_year,
            "academic_year": self.academic_year or get_current_academic_year(),
            "enrollment_status": self.enrollment_status,
        }


class StudentClassHistory(Base):
    __tablename__ = "student_class_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    start_date = Column(DateTime, default=datetime.now)
    end_date = Column(DateTime, nullable=True)
    reason = Column(String(50), nullable=True)
    operator_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    student = relationship("Student", back_populates="class_history")
    class_obj = relationship("Class", back_populates="student_history")

    @property
    def change_type_name(self) -> str:
        """变动类型名称"""
        if self.end_date:
            return "离班"
        return "入班"

    @property
    def display_class_name(self) -> str:
        """显示班级名称"""
        if self.class_obj:
            return self.class_obj.display_name or self.class_obj.name
        return ""
