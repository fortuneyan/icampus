# 教学进度跟踪数据模型
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Date,
    Text,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.soft_delete import SoftDeleteMixin
from app.models.timestamp import TimestampMixin
import enum


class ProgressStatus(str, enum.Enum):
    """教学进度状态"""

    NOT_STARTED = "not_started"  # 未开始
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    DELAYED = "delayed"  # 已延误
    OVERAHEAD = "ahead"  # 提前完成


class ProgressPeriod(str, enum.Enum):
    """教学周期"""

    FIRST_WEEK = "week_1"  # 第一周
    SECOND_WEEK = "week_2"  # 第二周
    THIRD_WEEK = "week_3"  # 第三周
    FOURTH_WEEK = "week_4"  # 第四周
    MONTH_1 = "month_1"  # 第一个月
    MONTH_2 = "month_2"  # 第二个月
    SEMESTER_1 = "semester_1"  # 上半学期
    SEMESTER_2 = "semester_2"  # 下半学期


class TeachingProgress(Base, TimestampMixin, SoftDeleteMixin):
    """
    教学进度表

    跟踪教师教学进度，记录每个课程章节的完成情况
    """

    __tablename__ = "edu_teaching_progress"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 基本信息
    course_id = Column(
        UUID(as_uuid=True),
        ForeignKey("courses.id"),
        nullable=False,
        index=True,
        comment="课程ID",
    )
    teacher_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, comment="教师ID"
    )
    class_id = Column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=True, comment="班级ID"
    )

    # 进度信息
    chapter = Column(String(100), nullable=True, comment="章节名称")
    chapter_number = Column(Integer, nullable=True, comment="章节序号")
    unit_name = Column(String(100), nullable=True, comment="单元名称")
    unit_number = Column(Integer, nullable=True, comment="单元序号")

    # 计划与实际
    planned_start_date = Column(Date, nullable=True, comment="计划开始日期")
    planned_end_date = Column(Date, nullable=True, comment="计划完成日期")
    actual_start_date = Column(Date, nullable=True, comment="实际开始日期")
    actual_end_date = Column(Date, nullable=True, comment="实际完成日期")

    # 完成情况
    status = Column(
        SQLEnum(ProgressStatus), default=ProgressStatus.NOT_STARTED, comment="状态"
    )
    progress_percentage = Column(Float, default=0.0, comment="完成百分比(0-100)")
    planned_hours = Column(Float, default=0.0, comment="计划课时数")
    actual_hours = Column(Float, default=0.0, comment="实际用时")

    # 教学要点
    key_points = Column(Text, nullable=True, comment="教学重点")
    difficult_points = Column(Text, nullable=True, comment="教学难点")
    teaching_goals = Column(Text, nullable=True, comment="教学目标")

    # 备注
    notes = Column(Text, nullable=True, comment="备注")
    delay_reason = Column(Text, nullable=True, comment="延误原因")

    # 关联关系
    course = relationship("Course")
    teacher = relationship("User")
    class_obj = relationship("Class")

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": str(self.id),
            "course_id": self.course_id,
            "teacher_id": self.teacher_id,
            "class_id": self.class_id,
            "chapter": self.chapter,
            "chapter_number": self.chapter_number,
            "unit_name": self.unit_name,
            "unit_number": self.unit_number,
            "planned_start_date": self.planned_start_date.isoformat()
            if self.planned_start_date
            else None,
            "planned_end_date": self.planned_end_date.isoformat()
            if self.planned_end_date
            else None,
            "actual_start_date": self.actual_start_date.isoformat()
            if self.actual_start_date
            else None,
            "actual_end_date": self.actual_end_date.isoformat()
            if self.actual_end_date
            else None,
            "status": self.status.value if self.status else None,
            "status_text": self._get_status_text(),
            "progress_percentage": self.progress_percentage,
            "planned_hours": self.planned_hours,
            "actual_hours": self.actual_hours,
            "key_points": self.key_points,
            "difficult_points": self.difficult_points,
            "teaching_goals": self.teaching_goals,
            "notes": self.notes,
            "delay_reason": self.delay_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def _get_status_text(self) -> str:
        """获取状态文本"""
        status_map = {
            ProgressStatus.NOT_STARTED: "未开始",
            ProgressStatus.IN_PROGRESS: "进行中",
            ProgressStatus.COMPLETED: "已完成",
            ProgressStatus.DELAYED: "已延误",
            ProgressStatus.OVERAHEAD: "提前完成",
        }
        return status_map.get(self.status, "未知")

    def calculate_progress_percentage(self) -> float:
        """计算进度百分比"""
        if not self.planned_start_date or not self.planned_end_date:
            return 0.0

        from datetime import date

        today = date.today()

        if today < self.planned_start_date:
            return 0.0
        elif today >= self.planned_end_date:
            return 100.0
        else:
            total_days = (self.planned_end_date - self.planned_start_date).days
            elapsed_days = (today - self.planned_start_date).days
            return round(elapsed_days / total_days * 100, 2) if total_days > 0 else 0.0

    def __repr__(self):
        return f"<TeachingProgress(id={self.id}, course_id={self.course_id}, chapter={self.chapter})>"


class ProgressUpdate(Base, TimestampMixin):
    """
    进度更新记录表

    记录每次进度更新日志
    """

    __tablename__ = "edu_progress_updates"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    progress_id = Column(
        Integer,
        ForeignKey("edu_teaching_progress.id"),
        nullable=False,
        comment="进度ID",
    )
    update_type = Column(String(50), nullable=False, comment="更新类型")
    old_value = Column(Text, nullable=True, comment="原值")
    new_value = Column(Text, nullable=True, comment="新值")
    updated_by = Column(String(100), nullable=True, comment="更新人")
    update_reason = Column(Text, nullable=True, comment="更新原因")

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": str(self.id),
            "progress_id": self.progress_id,
            "update_type": self.update_type,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "updated_by": self.updated_by,
            "update_reason": self.update_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<ProgressUpdate(id={self.id}, progress_id={self.progress_id}, type={self.update_type})>"


class ProgressReport(Base, TimestampMixin):
    """
    进度报告表

    周报/月报汇总
    """

    __tablename__ = "edu_progress_reports"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 报告基本信息
    title = Column(String(200), nullable=False, comment="报告标题")
    report_type = Column(
        String(50), nullable=False, comment="报告类型: weekly/monthly/termly"
    )
    teacher_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, comment="教师ID"
    )
    school_year = Column(String(20), nullable=False, comment="学年")
    semester = Column(String(20), nullable=False, comment="学期")
    period_start = Column(Date, nullable=False, comment="统计周期开始")
    period_end = Column(Date, nullable=False, comment="统计周期结束")

    # 统计信息
    total_courses = Column(Integer, default=0, comment="总课程数")
    completed_courses = Column(Integer, default=0, comment="已完成课程数")
    in_progress_courses = Column(Integer, default=0, comment="进行中课程数")
    delayed_courses = Column(Integer, default=0, comment="延误课程数")
    avg_progress = Column(Float, default=0.0, comment="平均进度%")
    planned_vs_actual = Column(Text, nullable=True, comment="计划与实际对比")
    issues = Column(Text, nullable=True, comment="存在问题")
    solutions = Column(Text, nullable=True, comment="解决方案")
    next_plan = Column(Text, nullable=True, comment="下期计划")

    # 审批信息
    status = Column(
        String(20), default="draft", comment="状态: draft/submitted/approved"
    )
    reviewed_by = Column(String(100), nullable=True, comment="审核人")
    reviewed_at = Column(Date, nullable=True, comment="审核时间")
    review_comments = Column(Text, nullable=True, comment="审核意见")

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": str(self.id),
            "title": self.title,
            "report_type": self.report_type,
            "teacher_id": self.teacher_id,
            "school_year": self.school_year,
            "semester": self.semester,
            "period_start": self.period_start.isoformat()
            if self.period_start
            else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "total_courses": self.total_courses,
            "completed_courses": self.completed_courses,
            "in_progress_courses": self.in_progress_courses,
            "delayed_courses": self.delayed_courses,
            "avg_progress": self.avg_progress,
            "planned_vs_actual": self.planned_vs_actual,
            "issues": self.issues,
            "solutions": self.solutions,
            "next_plan": self.next_plan,
            "status": self.status,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "review_comments": self.review_comments,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<ProgressReport(id={self.id}, title={self.title}, type={self.report_type})>"
