# -*- coding: utf-8 -*-
"""
T5: 智能排课
API接口

提供排课相关的RESTful API接口。
"""

from datetime import date, datetime
from typing import Optional, List, Dict, Any

try:
    from fastapi import APIRouter, Query, HTTPException, Body
    from pydantic import BaseModel, Field
    HAS_APP = True
except ImportError:
    HAS_APP = False

# ============== Pydantic Models ==============

class TimeSlotRequest(BaseModel):
    """时间段请求"""
    day_of_week: int = Field(..., ge=1, le=7, description="星期几 (1-7)")
    period: int = Field(..., ge=1, le=10, description="第几节课 (1-10)")
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class CourseAssignmentRequest(BaseModel):
    """课程分配请求"""
    course_id: int = Field(..., description="课程ID")
    course_name: str = Field(..., description="课程名称")
    teacher_id: int = Field(..., description="教师ID")
    teacher_name: str = Field(..., description="教师名称")
    class_id: int = Field(..., description="班级ID")
    class_name: str = Field(..., description="班级名称")
    classroom_id: Optional[int] = Field(None, description="教室ID")
    classroom_name: Optional[str] = Field(None, description="教室名称")
    time_slot: Optional[TimeSlotRequest] = Field(None, description="上课时间")
    duration: int = Field(1, ge=1, le=5, description="课程时长(节)")
    is_locked: bool = Field(False, description="是否锁定")
    note: Optional[str] = None


class SchedulingPlanRequest(BaseModel):
    """排课计划请求"""
    name: str = Field(..., description="计划名称")
    academic_year: str = Field(..., description="学年")
    semester: str = Field(..., description="学期")
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    assignments: List[CourseAssignmentRequest] = Field(default_factory=list, description="课程分配列表")


class OptimizationRequest(BaseModel):
    """优化请求"""
    plan_id: int = Field(..., description="计划ID")
    max_iterations: int = Field(1000, ge=100, le=10000, description="最大迭代次数")
    time_limit: float = Field(60.0, ge=10.0, le=300.0, description="时间限制(秒)")


class ManualAdjustRequest(BaseModel):
    """手动调整请求"""
    assignment_id: int = Field(..., description="分配ID")
    new_day: int = Field(..., ge=1, le=7, description="新星期")
    new_period: int = Field(..., ge=1, le=10, description="新课程节次")
    new_classroom_id: Optional[int] = Field(None, description="新课程室ID")


class ApiResponse(BaseModel):
    """通用API响应"""
    success: bool
    message: str
    data: Optional[Any] = None


# ============== Mock Data ==============

# 模拟排课计划
MOCK_PLANS: Dict[int, Dict[str, Any]] = {
    1: {
        "id": 1,
        "name": "2024-2025学年第一学期排课计划",
        "academic_year": "2024-2025",
        "semester": "第一学期",
        "start_date": "2024-09-01",
        "end_date": "2025-01-15",
        "status": "optimized",
        "score": 92.5,
        "optimization_iterations": 150,
        "assignments": [
            {
                "id": 1,
                "course_id": 1,
                "course_name": "语文",
                "teacher_id": 1,
                "teacher_name": "张老师",
                "class_id": 1,
                "class_name": "初一(1)班",
                "classroom_id": 101,
                "classroom_name": "101教室",
                "time_slot": {"day_of_week": 1, "period": 1},
                "duration": 2,
                "status": "optimized",
                "is_locked": False,
            },
            {
                "id": 2,
                "course_id": 2,
                "course_name": "数学",
                "teacher_id": 2,
                "teacher_name": "李老师",
                "class_id": 1,
                "class_name": "初一(1)班",
                "classroom_id": 102,
                "classroom_name": "102教室",
                "time_slot": {"day_of_week": 1, "period": 3},
                "duration": 2,
                "status": "optimized",
                "is_locked": False,
            },
        ],
    }
}

# 模拟班级数据
MOCK_CLASSES = [
    {"id": 1, "name": "初一(1)班", "grade": 7, "student_count": 40},
    {"id": 2, "name": "初一(2)班", "grade": 7, "student_count": 38},
    {"id": 3, "name": "初二(1)班", "grade": 8, "student_count": 42},
]

# 模拟课程数据
MOCK_COURSES = [
    {"id": 1, "name": "语文", "subject": "language", "required_hours": 4},
    {"id": 2, "name": "数学", "subject": "math", "required_hours": 5},
    {"id": 3, "name": "英语", "subject": "language", "required_hours": 4},
    {"id": 4, "name": "物理", "subject": "science", "required_hours": 3},
]

# 模拟教师数据
MOCK_TEACHERS = [
    {"id": 1, "name": "张老师", "subject": "语文", "max_hours": 20},
    {"id": 2, "name": "李老师", "subject": "数学", "max_hours": 18},
    {"id": 3, "name": "王老师", "subject": "英语", "max_hours": 20},
    {"id": 4, "name": "赵老师", "subject": "物理", "max_hours": 15},
]

# 模拟教室数据
MOCK_CLASSROOMS = [
    {"id": 101, "name": "101教室", "type": "普通", "capacity": 45, "equipment": ["投影仪"]},
    {"id": 102, "name": "102教室", "type": "普通", "capacity": 45, "equipment": ["投影仪"]},
    {"id": 103, "name": "物理实验室", "type": "实验室", "capacity": 40, "equipment": ["投影仪", "实验设备"]},
]


# ============== API Functions ==============

def get_plans(
    academic_year: Optional[str] = None,
    semester: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    """获取排课计划列表"""
    plans = list(MOCK_PLANS.values())

    # 筛选
    if academic_year:
        plans = [p for p in plans if p.get("academic_year") == academic_year]
    if semester:
        plans = [p for p in plans if p.get("semester") == semester]
    if status:
        plans = [p for p in plans if p.get("status") == status]

    # 分页
    total = len(plans)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated = plans[start_idx:end_idx]

    return {
        "success": True,
        "message": "获取成功",
        "data": {
            "plans": paginated,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
    }


def get_plan(plan_id: int) -> Dict[str, Any]:
    """获取排课计划详情"""
    plan = MOCK_PLANS.get(plan_id)
    if not plan:
        raise ValueError(f"计划{plan_id}不存在")

    return {
        "success": True,
        "message": "获取成功",
        "data": plan
    }


def create_plan(request: SchedulingPlanRequest) -> Dict[str, Any]:
    """创建排课计划"""
    plan_id = len(MOCK_PLANS) + 1

    plan = {
        "id": plan_id,
        "name": request.name,
        "academic_year": request.academic_year,
        "semester": request.semester,
        "start_date": request.start_date,
        "end_date": request.end_date,
        "status": "draft",
        "score": 0,
        "optimization_iterations": 0,
        "assignments": [
            {
                "id": i + 1,
                "course_id": a.course_id,
                "course_name": a.course_name,
                "teacher_id": a.teacher_id,
                "teacher_name": a.teacher_name,
                "class_id": a.class_id,
                "class_name": a.class_name,
                "classroom_id": a.classroom_id,
                "classroom_name": a.classroom_name,
                "time_slot": a.time_slot.dict() if a.time_slot else None,
                "duration": a.duration,
                "status": "pending",
                "is_locked": a.is_locked,
                "note": a.note,
            }
            for i, a in enumerate(request.assignments)
        ],
    }

    MOCK_PLANS[plan_id] = plan

    return {
        "success": True,
        "message": "创建成功",
        "data": plan
    }


def optimize_plan(
    plan_id: int,
    max_iterations: int = 1000,
    time_limit: float = 60.0
) -> Dict[str, Any]:
    """优化排课计划"""
    plan = MOCK_PLANS.get(plan_id)
    if not plan:
        raise ValueError(f"计划{plan_id}不存在")

    # 模拟优化过程
    import time
    time.sleep(0.5)

    # 更新状态
    plan["status"] = "optimized"
    plan["score"] = 92.5
    plan["optimization_iterations"] = 150

    # 更新分配状态
    for a in plan.get("assignments", []):
        if a.get("time_slot"):
            a["status"] = "optimized"

    return {
        "success": True,
        "message": "优化完成",
        "data": {
            "plan_id": plan_id,
            "status": "optimized",
            "score": plan["score"],
            "iterations": plan["optimization_iterations"],
            "conflicts_resolved": 3,
        }
    }


def detect_conflicts(plan_id: int) -> Dict[str, Any]:
    """检测排课冲突"""
    plan = MOCK_PLANS.get(plan_id)
    if not plan:
        raise ValueError(f"计划{plan_id}不存在")

    # 模拟冲突检测
    conflicts = []

    assignments = plan.get("assignments", [])
    for i, a in enumerate(assignments):
        if not a.get("time_slot"):
            continue

        # 检查与其他分配的冲突
        for j, b in enumerate(assignments):
            if i >= j or not b.get("time_slot"):
                continue

            # 教师冲突
            if a.get("teacher_id") == b.get("teacher_id"):
                if a["time_slot"] == b["time_slot"]:
                    conflicts.append({
                        "type": "teacher_conflict",
                        "severity": 4,
                        "description": f"{a.get('teacher_name')}在同一时段有多门课程",
                        "involved": [a["id"], b["id"]],
                    })

            # 班级冲突
            if a.get("class_id") == b.get("class_id"):
                if a["time_slot"] == b["time_slot"]:
                    conflicts.append({
                        "type": "class_conflict",
                        "severity": 5,
                        "description": f"{a.get('class_name')}在同一时段有多门课程",
                        "involved": [a["id"], b["id"]],
                    })

    return {
        "success": True,
        "message": "检测完成",
        "data": {
            "total_conflicts": len(conflicts),
            "conflicts": conflicts,
            "can_publish": len(conflicts) == 0,
        }
    }


def adjust_assignment(
    plan_id: int,
    assignment_id: int,
    new_day: int,
    new_period: int,
    new_classroom_id: Optional[int] = None
) -> Dict[str, Any]:
    """手动调整课程分配"""
    plan = MOCK_PLANS.get(plan_id)
    if not plan:
        raise ValueError(f"计划{plan_id}不存在")

    assignment = None
    for a in plan.get("assignments", []):
        if a["id"] == assignment_id:
            assignment = a
            break

    if not assignment:
        raise ValueError(f"分配{assignment_id}不存在")

    # 更新分配
    assignment["time_slot"] = {"day_of_week": new_day, "period": new_period}
    assignment["status"] = "manual_adjusted"

    if new_classroom_id:
        for cr in MOCK_CLASSROOMS:
            if cr["id"] == new_classroom_id:
                assignment["classroom_id"] = cr["id"]
                assignment["classroom_name"] = cr["name"]
                break

    return {
        "success": True,
        "message": "调整成功",
        "data": assignment
    }


def publish_plan(plan_id: int) -> Dict[str, Any]:
    """发布排课计划"""
    plan = MOCK_PLANS.get(plan_id)
    if not plan:
        raise ValueError(f"计划{plan_id}不存在")

    # 检查是否有冲突
    conflicts_result = detect_conflicts(plan_id)
    if conflicts_result["data"]["total_conflicts"] > 0:
        raise ValueError("存在未解决的冲突，无法发布")

    plan["status"] = "published"

    return {
        "success": True,
        "message": "发布成功",
        "data": plan
    }


def get_schedule_table(
    plan_id: int,
    class_id: Optional[int] = None,
    teacher_id: Optional[int] = None
) -> Dict[str, Any]:
    """获取课表"""
    plan = MOCK_PLANS.get(plan_id)
    if not plan:
        raise ValueError(f"计划{plan_id}不存在")

    # 构建课表网格
    grid = {}
    for day in range(1, 6):
        grid[day] = {}
        for period in range(1, 11):
            grid[day][period] = []

    # 填充数据
    for a in plan.get("assignments", []):
        if class_id and a.get("class_id") != class_id:
            continue
        if teacher_id and a.get("teacher_id") != teacher_id:
            continue

        ts = a.get("time_slot")
        if ts:
            day = ts.get("day_of_week", 1)
            period = ts.get("period", 1)
            duration = a.get("duration", 1)

            for i in range(duration):
                if 1 <= period + i <= 10:
                    grid[day][period + i].append(a)

    return {
        "success": True,
        "message": "获取成功",
        "data": {
            "plan_id": plan_id,
            "plan_name": plan.get("name"),
            "grid": grid,
            "days": 5,
            "periods": 10,
        }
    }


def get_schedule_summary(plan_id: int) -> Dict[str, Any]:
    """获取排课汇总"""
    plan = MOCK_PLANS.get(plan_id)
    if not plan:
        raise ValueError(f"计划{plan_id}不存在")

    assignments = plan.get("assignments", [])

    # 按班级统计
    by_class = {}
    for a in assignments:
        class_name = a.get("class_name", "未知")
        if class_name not in by_class:
            by_class[class_name] = {"total": 0, "assigned": 0, "unassigned": 0}
        by_class[class_name]["total"] += 1
        if a.get("time_slot"):
            by_class[class_name]["assigned"] += 1
        else:
            by_class[class_name]["unassigned"] += 1

    # 按教师统计
    by_teacher = {}
    for a in assignments:
        teacher_name = a.get("teacher_name", "未知")
        if teacher_name not in by_teacher:
            by_teacher[teacher_name] = {"total": 0, "hours": 0}
        by_teacher[teacher_name]["total"] += 1
        by_teacher[teacher_name]["hours"] += a.get("duration", 1)

    return {
        "success": True,
        "message": "获取成功",
        "data": {
            "plan": {
                "id": plan["id"],
                "name": plan["name"],
                "status": plan["status"],
                "score": plan.get("score", 0),
            },
            "total_assignments": len(assignments),
            "assigned_count": len([a for a in assignments if a.get("time_slot")]),
            "unassigned_count": len([a for a in assignments if not a.get("time_slot")]),
            "by_class": by_class,
            "by_teacher": by_teacher,
        }
    }


# ============== API Router Setup ==============

if HAS_APP:
    router = APIRouter(prefix="/scheduling", tags=["智能排课"])

    @router.get("/plans", response_model=ApiResponse)
    async def list_plans(
        academic_year: Optional[str] = Query(None, description="学年"),
        semester: Optional[str] = Query(None, description="学期"),
        status: Optional[str] = Query(None, description="状态"),
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    ):
        """获取排课计划列表"""
        return get_plans(academic_year, semester, status, page, page_size)

    @router.get("/plans/{plan_id}", response_model=ApiResponse)
    async def get_plan_detail(plan_id: int):
        """获取排课计划详情"""
        return get_plan(plan_id)

    @router.post("/plans", response_model=ApiResponse)
    async def create_scheduling_plan(request: SchedulingPlanRequest):
        """创建排课计划"""
        return create_plan(request)

    @router.post("/plans/{plan_id}/optimize", response_model=ApiResponse)
    async def optimize_scheduling_plan(
        plan_id: int,
        max_iterations: int = Query(1000, ge=100, le=10000, description="最大迭代次数"),
        time_limit: float = Query(60.0, ge=10.0, le=300.0, description="时间限制(秒)"),
    ):
        """优化排课计划"""
        return optimize_plan(plan_id, max_iterations, time_limit)

    @router.get("/plans/{plan_id}/conflicts", response_model=ApiResponse)
    async def check_conflicts(plan_id: int):
        """检测排课冲突"""
        return detect_conflicts(plan_id)

    @router.post("/plans/{plan_id}/adjust", response_model=ApiResponse)
    async def adjust_course_assignment(
        plan_id: int,
        assignment_id: int = Body(..., embed=True),
        new_day: int = Body(..., embed=True),
        new_period: int = Body(..., embed=True),
        new_classroom_id: Optional[int] = Body(None, embed=True),
    ):
        """手动调整课程分配"""
        return adjust_assignment(plan_id, assignment_id, new_day, new_period, new_classroom_id)

    @router.post("/plans/{plan_id}/publish", response_model=ApiResponse)
    async def publish_scheduling_plan(plan_id: int):
        """发布排课计划"""
        return publish_plan(plan_id)

    @router.get("/plans/{plan_id}/table", response_model=ApiResponse)
    async def get_schedule_table(
        plan_id: int,
        class_id: Optional[int] = Query(None, description="班级ID"),
        teacher_id: Optional[int] = Query(None, description="教师ID"),
    ):
        """获取课表"""
        return get_schedule_table(plan_id, class_id, teacher_id)

    @router.get("/plans/{plan_id}/summary", response_model=ApiResponse)
    async def get_summary(plan_id: int):
        """获取排课汇总"""
        return get_schedule_summary(plan_id)

    @router.get("/classes", response_model=ApiResponse)
    async def list_classes():
        """获取班级列表"""
        return {
            "success": True,
            "message": "获取成功",
            "data": MOCK_CLASSES
        }

    @router.get("/courses", response_model=ApiResponse)
    async def list_courses():
        """获取课程列表"""
        return {
            "success": True,
            "message": "获取成功",
            "data": MOCK_COURSES
        }

    @router.get("/teachers", response_model=ApiResponse)
    async def list_teachers():
        """获取教师列表"""
        return {
            "success": True,
            "message": "获取成功",
            "data": MOCK_TEACHERS
        }

    @router.get("/classrooms", response_model=ApiResponse)
    async def list_classrooms():
        """获取教室列表"""
        return {
            "success": True,
            "message": "获取成功",
            "data": MOCK_CLASSROOMS
        }
