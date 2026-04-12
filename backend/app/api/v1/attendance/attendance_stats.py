# -*- coding: utf-8 -*-
"""
T4: 考勤统计报表
API接口

提供考勤统计数据的查询、报表生成和导出功能。
"""

from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any

try:
    from fastapi import APIRouter, Query, HTTPException, Depends
    from pydantic import BaseModel, Field, field_validator
    HAS_APP = True
except ImportError:
    HAS_APP = False

# ============== Pydantic Models ==============

class StatQuery(BaseModel):
    """统计查询参数"""
    stat_type: str = Field(..., description="统计类型: daily, weekly, monthly, term, yearly")
    dimension: str = Field(..., description="统计维度: student, class, teacher, course, department")
    start_date: str = Field(..., description="开始日期 YYYY-MM-DD")
    end_date: str = Field(..., description="结束日期 YYYY-MM-DD")
    dimension_id: Optional[int] = Field(None, description="维度ID (学生ID/班级ID等)")
    class_id: Optional[int] = Field(None, description="班级ID")
    teacher_id: Optional[int] = Field(None, description="教师ID")

    @field_validator('stat_type')
    @classmethod
    def validate_stat_type(cls, v):
        valid_types = ['daily', 'weekly', 'monthly', 'term', 'yearly']
        if v not in valid_types:
            raise ValueError(f'stat_type必须是: {valid_types}')
        return v

    @field_validator('dimension')
    @classmethod
    def validate_dimension(cls, v):
        valid_dimensions = ['student', 'class', 'teacher', 'course', 'department']
        if v not in valid_dimensions:
            raise ValueError(f'dimension必须是: {valid_dimensions}')
        return v


class ReportQuery(BaseModel):
    """报表查询参数"""
    report_type: str = Field(..., description="报表类型: summary, detail, abnormal, comparison")
    start_date: str = Field(..., description="开始日期 YYYY-MM-DD")
    end_date: str = Field(..., description="结束日期 YYYY-MM-DD")
    dimension: str = Field("class", description="统计维度")
    class_id: Optional[int] = Field(None, description="班级ID")
    teacher_id: Optional[int] = Field(None, description="教师ID")
    include_abnormal: bool = Field(True, description="是否包含异常记录")
    compare_with_previous: bool = Field(False, description="是否与上期对比")

    @field_validator('report_type')
    @classmethod
    def validate_report_type(cls, v):
        valid_types = ['summary', 'detail', 'abnormal', 'comparison']
        if v not in valid_types:
            raise ValueError(f'report_type必须是: {valid_types}')
        return v


class AttendanceStatRecordResponse(BaseModel):
    """考勤统计记录响应"""
    id: int
    stat_type: str
    dimension: str
    dimension_id: int
    dimension_name: str
    stat_date: str
    total_count: int
    normal_count: int
    late_count: int
    early_leave_count: int
    absent_count: int
    leave_count: int
    normal_rate: float
    attendance_rate: float
    avg_early_minutes: float
    avg_late_minutes: float


class AbnormalRecordResponse(BaseModel):
    """异常记录响应"""
    id: int
    student_id: int
    student_name: str
    class_id: int
    class_name: str
    abnormal_type: str
    course_id: Optional[int]
    course_name: Optional[str]
    record_date: str
    late_minutes: int
    early_minutes: int
    severity: str
    status: str
    reason: Optional[str]


class ReportSummary(BaseModel):
    """报表汇总"""
    total_students: int
    total_normal: int
    total_late: int
    total_early_leave: int
    total_absent: int
    total_leave: int
    overall_normal_rate: float
    overall_attendance_rate: float


class AttendanceReportResponse(BaseModel):
    """考勤报表响应"""
    id: int
    report_type: str
    title: str
    start_date: str
    end_date: str
    stat_dimension: str
    stat_records: List[Dict[str, Any]]
    summary: ReportSummary
    trend: Optional[str]
    abnormal_records: List[Dict[str, Any]]
    created_at: str


class RankingItemResponse(BaseModel):
    """排名项响应"""
    rank: int
    dimension_id: int
    dimension_name: str
    normal_rate: float
    attendance_rate: float
    late_count: int
    absent_count: int
    trend: Optional[str]


class ApiResponse(BaseModel):
    """通用API响应"""
    success: bool
    message: str
    data: Optional[Any] = None


# ============== Mock Data ==============

def generate_mock_stats(
    stat_type: str,
    dimension: str,
    start_date: date,
    end_date: date,
    dimension_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """生成模拟统计数据"""
    records = []
    current_date = start_date
    record_id = 1

    dimension_names = {
        "student": ["张三", "李四", "王五", "赵六", "钱七"],
        "class": ["初一(1)班", "初一(2)班", "初二(1)班", "初二(2)班", "初三(1)班"],
        "teacher": ["张老师", "李老师", "王老师", "赵老师", "刘老师"],
    }

    while current_date <= end_date:
        if stat_type == "daily":
            dates_to_process = [current_date]
        elif stat_type == "weekly":
            dates_to_process = [current_date + timedelta(days=i) for i in range(7) if current_date + timedelta(days=i) <= end_date]
        elif stat_type == "monthly":
            dates_to_process = [current_date + timedelta(days=i) for i in range(30) if current_date + timedelta(days=i) <= end_date]
        else:
            dates_to_process = [current_date]

        for d in dates_to_process:
            names = dimension_names.get(dimension, ["未知"])
            for idx, name in enumerate(names):
                did = dimension_id or (idx + 1)

                # 生成随机但合理的考勤数据
                total = 30
                normal = int(total * 0.85)
                late = int(total * 0.08)
                early_leave = int(total * 0.04)
                absent = int(total * 0.02)
                leave = int(total * 0.01)

                normal_rate = round(normal / total * 100, 2)
                attendance_rate = round((total - absent) / total * 100, 2)

                records.append({
                    "id": record_id,
                    "stat_type": stat_type,
                    "dimension": dimension,
                    "dimension_id": did,
                    "dimension_name": name,
                    "stat_date": d.isoformat(),
                    "total_count": total,
                    "normal_count": normal,
                    "late_count": late,
                    "early_leave_count": early_leave,
                    "absent_count": absent,
                    "leave_count": leave,
                    "normal_rate": normal_rate,
                    "attendance_rate": attendance_rate,
                    "avg_early_minutes": 5.2,
                    "avg_late_minutes": 8.5,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                })
                record_id += 1

        # 移动到下一个周期
        if stat_type == "daily":
            current_date += timedelta(days=1)
        elif stat_type == "weekly":
            current_date += timedelta(weeks=1)
        elif stat_type == "monthly":
            # 移动到下个月
            if current_date.month == 12:
                current_date = date(current_date.year + 1, 1, 1)
            else:
                current_date = date(current_date.year, current_date.month + 1, 1)
        elif stat_type == "term":
            current_date = end_date + timedelta(days=1)
        elif stat_type == "yearly":
            current_date = date(current_date.year + 1, current_date.month, current_date.day)

        if current_date > end_date:
            break

    return records


def generate_mock_abnormal_records(
    start_date: date,
    end_date: date,
    class_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """生成模拟异常记录"""
    records = []
    current_date = start_date

    abnormal_types = ["late", "early_leave", "absent"]
    students = [
        {"id": 1, "name": "张三", "class_id": 1, "class_name": "初一(1)班"},
        {"id": 2, "name": "李四", "class_id": 1, "class_name": "初一(1)班"},
        {"id": 3, "name": "王五", "class_id": 2, "class_name": "初一(2)班"},
        {"id": 4, "name": "赵六", "class_id": 2, "class_name": "初一(2)班"},
        {"id": 5, "name": "钱七", "class_id": 3, "class_name": "初二(1)班"},
    ]

    record_id = 1
    while current_date <= end_date:
        # 每天随机生成1-3条异常记录
        import random
        num_records = random.randint(1, 3)

        for _ in range(num_records):
            student = random.choice(students)
            abnormal_type = random.choice(abnormal_types)

            late_minutes = random.randint(5, 45) if abnormal_type == "late" else 0
            early_minutes = random.randint(5, 30) if abnormal_type == "early_leave" else 0

            # 计算严重程度
            if abnormal_type == "absent":
                severity = "high"
            elif late_minutes >= 30 or early_minutes >= 30:
                severity = "medium"
            else:
                severity = "low"

            records.append({
                "id": record_id,
                "student_id": student["id"],
                "student_name": student["name"],
                "class_id": student["class_id"],
                "class_name": student["class_name"],
                "abnormal_type": abnormal_type,
                "course_id": random.randint(1, 6),
                "course_name": random.choice(["语文", "数学", "英语", "物理", "化学", "历史"]),
                "teacher_id": random.randint(1, 5),
                "teacher_name": random.choice(["张老师", "李老师", "王老师", "赵老师", "刘老师"]),
                "record_date": current_date.isoformat(),
                "check_in_time": None,
                "check_out_time": None,
                "scheduled_time": None,
                "late_minutes": late_minutes,
                "early_minutes": early_minutes,
                "reason": None,
                "status": random.choice(["pending", "handled"]),
                "severity": severity,
                "handled_by": random.randint(1, 5) if random.random() > 0.5 else None,
                "handled_at": datetime.now().isoformat() if random.random() > 0.5 else None,
                "handle_result": random.choice(["已联系家长", "已核实情况", "已请假"]) if random.random() > 0.5 else None,
                "created_at": datetime.now().isoformat(),
            })
            record_id += 1

        current_date += timedelta(days=1)

    return records


# ============== API Functions ==============

def get_attendance_stats(
    stat_type: str,
    dimension: str,
    start_date: str,
    end_date: str,
    dimension_id: Optional[int] = None,
    class_id: Optional[int] = None,
    teacher_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    """
    获取考勤统计数据

    根据指定条件查询考勤统计数据。
    """
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError:
        raise ValueError("日期格式无效，请使用 YYYY-MM-DD")

    # 生成模拟数据
    records = generate_mock_stats(stat_type, dimension, start, end, dimension_id)

    # 分页
    total = len(records)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_records = records[start_idx:end_idx]

    return {
        "success": True,
        "message": "获取成功",
        "data": {
            "records": paginated_records,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
    }


def get_attendance_summary(
    start_date: str,
    end_date: str,
    dimension: str = "class",
    class_id: Optional[int] = None,
    teacher_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    获取考勤汇总数据

    返回指定时间段内的考勤汇总统计。
    """
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError:
        raise ValueError("日期格式无效，请使用 YYYY-MM-DD")

    # 生成汇总数据
    total_students = 150
    total_normal = int(total_students * 0.85)
    total_late = int(total_students * 0.08)
    total_early_leave = int(total_students * 0.04)
    total_absent = int(total_students * 0.02)
    total_leave = int(total_students * 0.01)

    overall_normal_rate = round(total_normal / total_students * 100, 2)
    overall_attendance_rate = round((total_students - total_absent) / total_students * 100, 2)

    # 按维度分组统计
    dimension_stats = []
    dimension_names = ["初一(1)班", "初一(2)班", "初二(1)班", "初二(2)班", "初三(1)班"]

    for idx, name in enumerate(dimension_names):
        students = 30
        normal = int(students * (0.82 + idx * 0.01))
        late = int(students * 0.08)
        early_leave = int(students * 0.05)
        absent = int(students * (0.02 + idx * 0.005))
        leave = students - normal - late - early_leave - absent

        dimension_stats.append({
            "dimension_id": idx + 1,
            "dimension_name": name,
            "total_count": students,
            "normal_count": normal,
            "late_count": late,
            "early_leave_count": early_leave,
            "absent_count": absent,
            "leave_count": leave,
            "normal_rate": round(normal / students * 100, 2),
            "attendance_rate": round((students - absent) / students * 100, 2),
        })

    return {
        "success": True,
        "message": "获取成功",
        "data": {
            "period": {
                "start_date": start_date,
                "end_date": end_date,
            },
            "summary": {
                "total_students": total_students,
                "total_normal": total_normal,
                "total_late": total_late,
                "total_early_leave": total_early_leave,
                "total_absent": total_absent,
                "total_leave": total_leave,
                "overall_normal_rate": overall_normal_rate,
                "overall_attendance_rate": overall_attendance_rate,
            },
            "dimension_stats": dimension_stats,
        }
    }


def get_abnormal_records(
    start_date: str,
    end_date: str,
    class_id: Optional[int] = None,
    teacher_id: Optional[int] = None,
    abnormal_type: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    """
    获取考勤异常记录

    查询指定条件下的考勤异常记录。
    """
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError:
        raise ValueError("日期格式无效，请使用 YYYY-MM-DD")

    # 生成模拟数据
    records = generate_mock_abnormal_records(start, end, class_id)

    # 过滤
    if abnormal_type:
        records = [r for r in records if r["abnormal_type"] == abnormal_type]
    if severity:
        records = [r for r in records if r["severity"] == severity]
    if status:
        records = [r for r in records if r["status"] == status]

    # 统计
    by_type = {}
    by_severity = {"high": 0, "medium": 0, "low": 0}
    by_status = {"pending": 0, "handled": 0}

    for r in records:
        abnormal_type = r["abnormal_type"]
        by_type[abnormal_type] = by_type.get(abnormal_type, 0) + 1
        by_severity[r["severity"]] += 1
        by_status[r["status"]] += 1

    # 分页
    total = len(records)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_records = records[start_idx:end_idx]

    return {
        "success": True,
        "message": "获取成功",
        "data": {
            "records": paginated_records,
            "statistics": {
                "total": total,
                "by_type": by_type,
                "by_severity": by_severity,
                "by_status": by_status,
            },
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
    }


def generate_report(
    report_type: str,
    start_date: str,
    end_date: str,
    dimension: str = "class",
    class_id: Optional[int] = None,
    teacher_id: Optional[int] = None,
    include_abnormal: bool = True,
    compare_with_previous: bool = False
) -> Dict[str, Any]:
    """
    生成考勤报表

    根据指定条件生成考勤统计报表。
    """
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError:
        raise ValueError("日期格式无效，请使用 YYYY-MM-DD")

    # 生成报表标题
    report_titles = {
        "summary": "考勤汇总报表",
        "detail": "考勤明细报表",
        "abnormal": "考勤异常报表",
        "comparison": "考勤对比报表",
    }

    # 获取统计数据
    stats = generate_mock_stats("daily", dimension, start, end, class_id)

    # 计算汇总
    total_students = sum(r["total_count"] for r in stats) if stats else 0
    total_normal = sum(r["normal_count"] for r in stats) if stats else 0
    total_late = sum(r["late_count"] for r in stats) if stats else 0
    total_early_leave = sum(r["early_leave_count"] for r in stats) if stats else 0
    total_absent = sum(r["absent_count"] for r in stats) if stats else 0
    total_leave = sum(r["leave_count"] for r in stats) if stats else 0

    overall_normal_rate = round(total_normal / total_students * 100, 2) if total_students > 0 else 0
    overall_attendance_rate = round((total_students - total_absent) / total_students * 100, 2) if total_students > 0 else 0

    # 判断趋势
    if overall_attendance_rate >= 95:
        trend = "normal"
    elif overall_attendance_rate >= 85:
        trend = "improving"
    else:
        trend = "deteriorating"

    # 获取异常记录
    abnormal_records = []
    if include_abnormal:
        abnormal_records = generate_mock_abnormal_records(start, end, class_id)[:10]

    # 对比数据
    comparison_data = None
    if compare_with_previous:
        # 生成上期对比数据
        period_days = (end - start).days
        prev_start = start - timedelta(days=period_days)
        prev_end = start - timedelta(days=1)

        comparison_data = {
            "period": {
                "start_date": prev_start.isoformat(),
                "end_date": prev_end.isoformat(),
            },
            "summary": {
                "total_students": total_students,
                "overall_normal_rate": round(overall_normal_rate - 1.5, 2),
                "overall_attendance_rate": round(overall_attendance_rate - 2.3, 2),
            }
        }

    return {
        "success": True,
        "message": "报表生成成功",
        "data": {
            "id": int(datetime.now().timestamp()),
            "report_type": report_type,
            "title": report_titles.get(report_type, "考勤报表"),
            "start_date": start_date,
            "end_date": end_date,
            "stat_dimension": dimension,
            "stat_records": stats[:10] if stats else [],
            "summary": {
                "total_students": total_students,
                "total_normal": total_normal,
                "total_late": total_late,
                "total_early_leave": total_early_leave,
                "total_absent": total_absent,
                "total_leave": total_leave,
                "overall_normal_rate": overall_normal_rate,
                "overall_attendance_rate": overall_attendance_rate,
            },
            "trend": trend,
            "abnormal_records": abnormal_records,
            "comparison_data": comparison_data,
            "generated_by": 1,
            "created_at": datetime.now().isoformat(),
        }
    }


def get_attendance_ranking(
    dimension: str,
    start_date: str,
    end_date: str,
    ranking_type: str = "attendance",
    limit: int = 10
) -> Dict[str, Any]:
    """
    获取考勤排名

    按指定维度返回考勤排名数据。
    """
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError:
        raise ValueError("日期格式无效，请使用 YYYY-MM-DD")

    # 模拟排名数据
    dimension_names = {
        "class": ["初一(1)班", "初一(2)班", "初二(1)班", "初二(2)班", "初三(1)班"],
        "student": ["张三", "李四", "王五", "赵六", "钱七"],
        "teacher": ["张老师", "李老师", "王老师", "赵老师", "刘老师"],
    }

    names = dimension_names.get(dimension, ["未知"])
    ranking_data = []

    for idx, name in enumerate(names):
        # 生成排名数据 (逆序以模拟不同排名)
        base_rate = 98 - idx * 2
        normal_rate = base_rate - 1
        attendance_rate = base_rate

        ranking_data.append({
            "rank": idx + 1,
            "dimension_id": idx + 1,
            "dimension_name": name,
            "normal_rate": round(normal_rate, 2),
            "attendance_rate": round(attendance_rate, 2),
            "late_count": idx * 2,
            "absent_count": idx,
            "trend": "improving" if idx % 2 == 0 else "normal",
        })

    # 按排名排序
    if ranking_type == "attendance":
        ranking_data.sort(key=lambda x: x["attendance_rate"], reverse=True)
    elif ranking_type == "normal":
        ranking_data.sort(key=lambda x: x["normal_rate"], reverse=True)
    elif ranking_type == "late":
        ranking_data.sort(key=lambda x: x["late_count"])
    elif ranking_type == "absent":
        ranking_data.sort(key=lambda x: x["absent_count"])

    # 更新排名
    for idx, item in enumerate(ranking_data):
        item["rank"] = idx + 1

    return {
        "success": True,
        "message": "获取成功",
        "data": {
            "dimension": dimension,
            "ranking_type": ranking_type,
            "period": {
                "start_date": start_date,
                "end_date": end_date,
            },
            "ranking": ranking_data[:limit],
        }
    }


def export_report(
    report_id: int,
    export_format: str = "excel"
) -> Dict[str, Any]:
    """
    导出考勤报表

    导出指定格式的考勤报表。
    """
    valid_formats = ["excel", "pdf", "csv"]

    if export_format not in valid_formats:
        raise ValueError(f"导出格式无效，支持: {valid_formats}")

    # 返回导出信息 (实际导出需要后端处理)
    return {
        "success": True,
        "message": f"报表正在导出，格式: {export_format}",
        "data": {
            "report_id": report_id,
            "export_format": export_format,
            "download_url": f"/api/v1/attendance/export/{report_id}.{export_format}",
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
        }
    }


# ============== API Router Setup ==============

if HAS_APP:
    router = APIRouter(prefix="/attendance", tags=["考勤统计"])

    @router.get("/stats", response_model=ApiResponse)
    async def get_stats(
        stat_type: str = Query(..., description="统计类型"),
        dimension: str = Query(..., description="统计维度"),
        start_date: str = Query(..., description="开始日期"),
        end_date: str = Query(..., description="结束日期"),
        dimension_id: Optional[int] = Query(None, description="维度ID"),
        class_id: Optional[int] = Query(None, description="班级ID"),
        teacher_id: Optional[int] = Query(None, description="教师ID"),
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    ):
        """获取考勤统计数据"""
        return get_attendance_stats(
            stat_type, dimension, start_date, end_date,
            dimension_id, class_id, teacher_id, page, page_size
        )

    @router.get("/summary", response_model=ApiResponse)
    async def get_summary(
        start_date: str = Query(..., description="开始日期"),
        end_date: str = Query(..., description="结束日期"),
        dimension: str = Query("class", description="统计维度"),
        class_id: Optional[int] = Query(None, description="班级ID"),
        teacher_id: Optional[int] = Query(None, description="教师ID"),
    ):
        """获取考勤汇总"""
        return get_attendance_summary(start_date, end_date, dimension, class_id, teacher_id)

    @router.get("/abnormal", response_model=ApiResponse)
    async def get_abnormal(
        start_date: str = Query(..., description="开始日期"),
        end_date: str = Query(..., description="结束日期"),
        class_id: Optional[int] = Query(None, description="班级ID"),
        teacher_id: Optional[int] = Query(None, description="教师ID"),
        abnormal_type: Optional[str] = Query(None, description="异常类型"),
        severity: Optional[str] = Query(None, description="严重程度"),
        status: Optional[str] = Query(None, description="处理状态"),
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    ):
        """获取考勤异常记录"""
        return get_abnormal_records(
            start_date, end_date, class_id, teacher_id,
            abnormal_type, severity, status, page, page_size
        )

    @router.get("/report", response_model=ApiResponse)
    async def generate_report_api(
        report_type: str = Query(..., description="报表类型"),
        start_date: str = Query(..., description="开始日期"),
        end_date: str = Query(..., description="结束日期"),
        dimension: str = Query("class", description="统计维度"),
        class_id: Optional[int] = Query(None, description="班级ID"),
        teacher_id: Optional[int] = Query(None, description="教师ID"),
        include_abnormal: bool = Query(True, description="包含异常记录"),
        compare_with_previous: bool = Query(False, description="与上期对比"),
    ):
        """生成考勤报表"""
        return generate_report(
            report_type, start_date, end_date, dimension,
            class_id, teacher_id, include_abnormal, compare_with_previous
        )

    @router.get("/ranking", response_model=ApiResponse)
    async def get_ranking(
        dimension: str = Query("class", description="统计维度"),
        start_date: str = Query(..., description="开始日期"),
        end_date: str = Query(..., description="结束日期"),
        ranking_type: str = Query("attendance", description="排名类型"),
        limit: int = Query(10, ge=1, le=100, description="返回数量"),
    ):
        """获取考勤排名"""
        return get_attendance_ranking(dimension, start_date, end_date, ranking_type, limit)

    @router.get("/export/{report_id}", response_model=ApiResponse)
    async def export_report_api(
        report_id: int,
        export_format: str = Query("excel", description="导出格式"),
    ):
        """导出考勤报表"""
        return export_report(report_id, export_format)
