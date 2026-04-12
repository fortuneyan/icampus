# -*- coding: utf-8 -*-
"""
T4: 考勤统计报表
后端数据模型

考勤统计功能，提供多维度的考勤数据统计和报表生成能力。
支持按学生/班级/教师/日期范围等维度进行统计。
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional, List, Dict, Any


class AttendanceStatType(str, Enum):
    """考勤统计类型"""
    DAILY = "daily"           # 日统计
    WEEKLY = "weekly"          # 周统计
    MONTHLY = "monthly"        # 月统计
    TERM = "term"              # 学期统计
    YEARLY = "yearly"          # 年度统计


class AttendanceStatDimension(str, Enum):
    """统计维度"""
    STUDENT = "student"        # 按学生
    CLASS = "class"            # 按班级
    TEACHER = "teacher"        # 按教师
    COURSE = "course"          # 按课程
    DEPARTMENT = "department"  # 按部门


class AttendanceTrend(str, Enum):
    """考勤趋势"""
    NORMAL = "normal"          # 正常
    IMPROVING = "improving"    # 改善中
    DETERIORATING = "deteriorating"  # 恶化中


class AttendanceReportType(str, Enum):
    """报表类型"""
    SUMMARY = "summary"        # 汇总报表
    DETAIL = "detail"          # 明细报表
    ABNORMAL = "abnormal"       # 异常报表
    COMPARISON = "comparison"  # 对比报表


class AttendanceStatRecord:
    """
    考勤统计记录

    用于存储单个统计维度的考勤汇总数据。
    """

    def __init__(
        self,
        id: int,
        stat_type: AttendanceStatType,
        dimension: AttendanceStatDimension,
        dimension_id: int,
        dimension_name: str,
        stat_date: date,
        total_count: int,
        normal_count: int,
        late_count: int,
        early_leave_count: int,
        absent_count: int,
        leave_count: int,
        normal_rate: float,
        attendance_rate: float,
        avg_early_minutes: float = 0.0,
        avg_late_minutes: float = 0.0,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.stat_type = stat_type
        self.dimension = dimension
        self.dimension_id = dimension_id
        self.dimension_name = dimension_name
        self.stat_date = stat_date
        self.total_count = total_count
        self.normal_count = normal_count
        self.late_count = late_count
        self.early_leave_count = early_leave_count
        self.absent_count = absent_count
        self.leave_count = leave_count
        self.normal_rate = normal_rate
        self.attendance_rate = attendance_rate
        self.avg_early_minutes = avg_early_minutes
        self.avg_late_minutes = avg_late_minutes
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "stat_type": self.stat_type.value if isinstance(self.stat_type, Enum) else self.stat_type,
            "dimension": self.dimension.value if isinstance(self.dimension, Enum) else self.dimension,
            "dimension_id": self.dimension_id,
            "dimension_name": self.dimension_name,
            "stat_date": self.stat_date.isoformat() if isinstance(self.stat_date, date) else self.stat_date,
            "total_count": self.total_count,
            "normal_count": self.normal_count,
            "late_count": self.late_count,
            "early_leave_count": self.early_leave_count,
            "absent_count": self.absent_count,
            "leave_count": self.leave_count,
            "normal_rate": round(self.normal_rate, 2),
            "attendance_rate": round(self.attendance_rate, 2),
            "avg_early_minutes": round(self.avg_early_minutes, 2),
            "avg_late_minutes": round(self.avg_late_minutes, 2),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<AttendanceStatRecord(id={self.id}, dimension={self.dimension.value}, "
            f"date={self.stat_date}, normal_rate={self.normal_rate:.1f}%)>"
        )


class AttendanceAbnormalRecord:
    """
    考勤异常记录

    记录考勤异常情况，包括迟到、早退、缺勤等。
    """

    def __init__(
        self,
        id: int,
        student_id: int,
        student_name: str,
        class_id: int,
        class_name: str,
        abnormal_type: str,
        course_id: Optional[int] = None,
        course_name: Optional[str] = None,
        teacher_id: Optional[int] = None,
        teacher_name: Optional[str] = None,
        record_date: date = None,
        check_in_time: Optional[datetime] = None,
        check_out_time: Optional[datetime] = None,
        scheduled_time: Optional[datetime] = None,
        late_minutes: int = 0,
        early_minutes: int = 0,
        reason: Optional[str] = None,
        status: str = "pending",
        handled_by: Optional[int] = None,
        handled_at: Optional[datetime] = None,
        handle_result: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.student_id = student_id
        self.student_name = student_name
        self.class_id = class_id
        self.class_name = class_name
        self.abnormal_type = abnormal_type
        self.course_id = course_id
        self.course_name = course_name
        self.teacher_id = teacher_id
        self.teacher_name = teacher_name
        self.record_date = record_date
        self.check_in_time = check_in_time
        self.check_out_time = check_out_time
        self.scheduled_time = scheduled_time
        self.late_minutes = late_minutes
        self.early_minutes = early_minutes
        self.reason = reason
        self.status = status
        self.handled_by = handled_by
        self.handled_at = handled_at
        self.handle_result = handle_result
        self.created_at = created_at or datetime.now()

    @property
    def severity(self) -> str:
        """获取严重程度"""
        if self.abnormal_type == "absent":
            return "high"
        elif self.abnormal_type == "late" and self.late_minutes >= 30:
            return "medium"
        elif self.abnormal_type == "early_leave" and self.early_minutes >= 30:
            return "medium"
        return "low"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": self.student_name,
            "class_id": self.class_id,
            "class_name": self.class_name,
            "abnormal_type": self.abnormal_type,
            "course_id": self.course_id,
            "course_name": self.course_name,
            "teacher_id": self.teacher_id,
            "teacher_name": self.teacher_name,
            "record_date": self.record_date.isoformat() if isinstance(self.record_date, date) else self.record_date,
            "check_in_time": self.check_in_time.isoformat() if self.check_in_time else None,
            "check_out_time": self.check_out_time.isoformat() if self.check_out_time else None,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "late_minutes": self.late_minutes,
            "early_minutes": self.early_minutes,
            "reason": self.reason,
            "status": self.status,
            "severity": self.severity,
            "handled_by": self.handled_by,
            "handled_at": self.handled_at.isoformat() if self.handled_at else None,
            "handle_result": self.handle_result,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<AttendanceAbnormalRecord(id={self.id}, student={self.student_name}, "
            f"type={self.abnormal_type}, severity={self.severity})>"
        )


class AttendanceReport:
    """
    考勤报表

    用于生成各类考勤统计报表。
    """

    def __init__(
        self,
        id: int,
        report_type: AttendanceReportType,
        title: str,
        start_date: date,
        end_date: date,
        stat_dimension: AttendanceStatDimension,
        stat_records: List[AttendanceStatRecord],
        total_students: int = 0,
        total_normal: int = 0,
        total_late: int = 0,
        total_early_leave: int = 0,
        total_absent: int = 0,
        total_leave: int = 0,
        overall_normal_rate: float = 0.0,
        overall_attendance_rate: float = 0.0,
        trend: Optional[AttendanceTrend] = None,
        abnormal_records: Optional[List[AttendanceAbnormalRecord]] = None,
        comparison_data: Optional[Dict[str, Any]] = None,
        generated_by: Optional[int] = None,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.report_type = report_type
        self.title = title
        self.start_date = start_date
        self.end_date = end_date
        self.stat_dimension = stat_dimension
        self.stat_records = stat_records
        self.total_students = total_students
        self.total_normal = total_normal
        self.total_late = total_late
        self.total_early_leave = total_early_leave
        self.total_absent = total_absent
        self.total_leave = total_leave
        self.overall_normal_rate = overall_normal_rate
        self.overall_attendance_rate = overall_attendance_rate
        self.trend = trend
        self.abnormal_records = abnormal_records or []
        self.comparison_data = comparison_data
        self.generated_by = generated_by
        self.created_at = created_at or datetime.now()

    def calculate_totals(self) -> None:
        """计算汇总数据"""
        if not self.stat_records:
            return

        self.total_students = sum(r.total_count for r in self.stat_records)
        self.total_normal = sum(r.normal_count for r in self.stat_records)
        self.total_late = sum(r.late_count for r in self.stat_records)
        self.total_early_leave = sum(r.early_leave_count for r in self.stat_records)
        self.total_absent = sum(r.absent_count for r in self.stat_records)
        self.total_leave = sum(r.leave_count for r in self.stat_records)

        if self.total_students > 0:
            self.overall_normal_rate = round(self.total_normal / self.total_students * 100, 2)
            self.overall_attendance_rate = round(
                (self.total_students - self.total_absent) / self.total_students * 100, 2
            )

    def analyze_trend(self, previous_report: Optional['AttendanceReport'] = None) -> AttendanceTrend:
        """分析考勤趋势"""
        if not previous_report:
            # 无对比数据，根据当前出勤率判断
            if self.overall_attendance_rate >= 95:
                return AttendanceTrend.NORMAL
            elif self.overall_attendance_rate >= 85:
                return AttendanceTrend.IMPROVING
            else:
                return AttendanceTrend.DETERIORATING

        # 有对比数据，比较变化
        rate_change = self.overall_attendance_rate - previous_report.overall_attendance_rate

        if rate_change >= 2:
            return AttendanceTrend.IMPROVING
        elif rate_change <= -2:
            return AttendanceTrend.DETERIORATING
        else:
            return AttendanceTrend.NORMAL

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "report_type": self.report_type.value if isinstance(self.report_type, Enum) else self.report_type,
            "title": self.title,
            "start_date": self.start_date.isoformat() if isinstance(self.start_date, date) else self.start_date,
            "end_date": self.end_date.isoformat() if isinstance(self.end_date, date) else self.end_date,
            "stat_dimension": self.stat_dimension.value if isinstance(self.stat_dimension, Enum) else self.stat_dimension,
            "stat_records": [r.to_dict() for r in self.stat_records],
            "summary": {
                "total_students": self.total_students,
                "total_normal": self.total_normal,
                "total_late": self.total_late,
                "total_early_leave": self.total_early_leave,
                "total_absent": self.total_absent,
                "total_leave": self.total_leave,
                "overall_normal_rate": self.overall_normal_rate,
                "overall_attendance_rate": self.overall_attendance_rate,
            },
            "trend": self.trend.value if self.trend else None,
            "abnormal_records": [r.to_dict() for r in self.abnormal_records],
            "comparison_data": self.comparison_data,
            "generated_by": self.generated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<AttendanceReport(id={self.id}, type={self.report_type.value}, "
            f"period={self.start_date}~{self.end_date}, rate={self.overall_attendance_rate:.1f}%)>"
        )


class AttendanceRankItem:
    """
    考勤排名项

    用于班级或学生考勤排名。
    """

    def __init__(
        self,
        rank: int,
        dimension_id: int,
        dimension_name: str,
        normal_rate: float,
        attendance_rate: float,
        late_count: int = 0,
        absent_count: int = 0,
        trend: Optional[AttendanceTrend] = None,
    ):
        self.rank = rank
        self.dimension_id = dimension_id
        self.dimension_name = dimension_name
        self.normal_rate = normal_rate
        self.attendance_rate = attendance_rate
        self.late_count = late_count
        self.absent_count = absent_count
        self.trend = trend

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "rank": self.rank,
            "dimension_id": self.dimension_id,
            "dimension_name": self.dimension_name,
            "normal_rate": round(self.normal_rate, 2),
            "attendance_rate": round(self.attendance_rate, 2),
            "late_count": self.late_count,
            "absent_count": self.absent_count,
            "trend": self.trend.value if self.trend else None,
        }


# 辅助函数

def calculate_attendance_rate(total: int, absent: int) -> float:
    """计算出勤率"""
    if total == 0:
        return 0.0
    return round((total - absent) / total * 100, 2)


def calculate_normal_rate(total: int, abnormal: int) -> float:
    """计算正常率"""
    if total == 0:
        return 0.0
    return round((total - abnormal) / total * 100, 2)


def calculate_late_severity(minutes: int) -> str:
    """计算迟到严重程度"""
    if minutes < 10:
        return "light"
    elif minutes < 30:
        return "medium"
    else:
        return "severe"
