# -*- coding: utf-8 -*-
"""
T5: 智能排课
API接口 - 数据库持久化版本

提供排课相关的RESTful API接口，基于数据库持久化。
"""

from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.scheduling_db_service import SchedulingDBService
from app.schemas.scheduling import (
    SemesterCreate, SemesterUpdate, SemesterResponse,
    CycleCreate, CycleUpdate, CycleResponse,
    CalendarMapCreate, CalendarMapUpdate, CalendarMapResponse, CalendarMapQuery,
    TemplateCreate, TemplateUpdate, TemplateResponse,
    PeriodCreate, PeriodResponse,
    PlanCreate, PlanUpdate, PlanResponse,
    ResultCreate, ResultUpdate, ResultResponse,
    PatchCreate, PatchUpdate, PatchResponse,
    ConstraintCreate, ConstraintUpdate, ConstraintResponse,
    EventCreate, EventUpdate, EventResponse,
    ReplaceCreate, ReplaceResponse,
    DragAdjustRequest,
    ClassScheduleResponse, TeacherScheduleResponse
)
from app.api.v1.utils import success, page_response


router = APIRouter(tags=["智能排课"])


def get_service(db: AsyncSession = Depends(get_db)) -> SchedulingDBService:
    """获取服务实例"""
    return SchedulingDBService(db)


# ============ 学期管理 ============

@router.get("/semesters", response_model=dict)
async def list_semesters(
    status: Optional[str] = Query(None, description="状态"),
    service: SchedulingDBService = Depends(get_service)
):
    """获取学期列表"""
    semesters = await service.get_semesters(status)
    items = [SemesterResponse.model_validate(s).model_dump() for s in semesters]
    return success(data={"semesters": items, "total": len(items)})


@router.get("/semesters/{semester_id}", response_model=dict)
async def get_semester(
    semester_id: str,
    service: SchedulingDBService = Depends(get_service)
):
    """获取学期详情"""
    semester = await service.get_semester(semester_id)
    if not semester:
        raise HTTPException(status_code=404, detail="学期不存在")
    return success(data=SemesterResponse.model_validate(semester).model_dump())


@router.post("/semesters", response_model=dict)
async def create_semester(
    data: SemesterCreate,
    service: SchedulingDBService = Depends(get_service)
):
    """创建学期"""
    semester = await service.create_semester(data)
    return success(data=SemesterResponse.model_validate(semester).model_dump())


# ============ 周次组合管理 ============

@router.get("/cycles", response_model=dict)
async def list_cycles(
    semester_id: Optional[str] = Query(None, description="学期ID"),
    service: SchedulingDBService = Depends(get_service)
):
    """获取周次组合列表"""
    cycles = await service.get_cycles(semester_id)
    items = [CycleResponse.model_validate(c).model_dump() for c in cycles]
    return success(data={"cycles": items, "total": len(items)})


@router.get("/cycles/{cycle_id}", response_model=dict)
async def get_cycle(
    cycle_id: str,
    service: SchedulingDBService = Depends(get_service)
):
    """获取周次组合详情"""
    cycles = await service.get_cycles()
    cycle = next((c for c in cycles if c.id == cycle_id), None)
    if not cycle:
        raise HTTPException(status_code=404, detail="周次组合不存在")
    return success(data=CycleResponse.model_validate(cycle).model_dump())


@router.post("/cycles", response_model=dict)
async def create_cycle(
    data: CycleCreate,
    service: SchedulingDBService = Depends(get_service)
):
    """创建周次组合"""
    cycle = await service.create_cycle(data)
    return success(data=CycleResponse.model_validate(cycle).model_dump())


@router.put("/cycles/{cycle_id}/set-current", response_model=dict)
async def set_current_cycle(
    cycle_id: str,
    service: SchedulingDBService = Depends(get_service)
):
    """设置当前生效的周次组合"""
    await service.set_current_cycle(cycle_id)
    return success(message="设置成功")


# ============ 日历映射管理 ============

@router.get("/calendar-maps", response_model=dict)
async def list_calendar_maps(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    is_holiday: Optional[bool] = Query(None, description="是否放假"),
    service: SchedulingDBService = Depends(get_service)
):
    """获取日历映射列表"""
    maps = await service.get_calendar_maps(start_date, end_date, is_holiday)
    items = [CalendarMapResponse.model_validate(m).model_dump() for m in maps]
    return success(data={"calendar_maps": items, "total": len(items)})


@router.get("/calendar-maps/{natural_date}", response_model=dict)
async def get_calendar_map(
    natural_date: date,
    service: SchedulingDBService = Depends(get_service)
):
    """获取指定日期的日历映射"""
    calendar_map = await service.get_calendar_map(natural_date)
    if not calendar_map:
        return success(data=None)
    return success(data=CalendarMapResponse.model_validate(calendar_map).model_dump())


@router.post("/calendar-maps", response_model=dict)
async def create_calendar_map(
    data: CalendarMapCreate,
    service: SchedulingDBService = Depends(get_service)
):
    """创建日历映射"""
    calendar_map = await service.create_calendar_map(data)
    return success(data=CalendarMapResponse.model_validate(calendar_map).model_dump())


@router.post("/calendar-maps/batch", response_model=dict)
async def batch_create_calendar_maps(
    items: List[CalendarMapCreate],
    service: SchedulingDBService = Depends(get_service)
):
    """批量创建日历映射"""
    maps = await service.batch_create_calendar_maps(items)
    return success(data={"count": len(maps), "message": f"成功创建{len(maps)}条记录"})


@router.put("/calendar-maps/{natural_date}", response_model=dict)
async def update_calendar_map(
    natural_date: date,
    data: CalendarMapUpdate,
    service: SchedulingDBService = Depends(get_service)
):
    """更新日历映射"""
    calendar_map = await service.update_calendar_map(
        natural_date,
        cycle_id=data.cycle_id,
        exec_day=data.exec_day,
        is_workday=data.is_workday,
        is_holiday=data.is_holiday
    )
    if not calendar_map:
        raise HTTPException(status_code=404, detail="日历映射不存在")
    return success(data=CalendarMapResponse.model_validate(calendar_map).model_dump())


# ============ 课表模板管理 ============

@router.get("/templates", response_model=dict)
async def list_templates(
    semester_id: str = Query(..., description="学期ID"),
    service: SchedulingDBService = Depends(get_service)
):
    """获取课表模板列表"""
    templates = await service.get_templates(semester_id)
    items = [TemplateResponse.model_validate(t).model_dump() for t in templates]
    return success(data={"templates": items, "total": len(items)})


@router.post("/templates", response_model=dict)
async def create_template(
    data: TemplateCreate,
    service: SchedulingDBService = Depends(get_service)
):
    """创建课表模板"""
    template = await service.create_template(data)
    return success(data=TemplateResponse.model_validate(template).model_dump())


@router.post("/templates/{template_id}/periods", response_model=dict)
async def create_period(
    template_id: UUID,
    data: PeriodCreate,
    service: SchedulingDBService = Depends(get_service)
):
    """创建节次"""
    period = await service.create_period(data)
    return success(data=PeriodResponse.model_validate(period).model_dump())


@router.get("/templates/{template_id}/periods", response_model=dict)
async def list_periods(
    template_id: UUID,
    service: SchedulingDBService = Depends(get_service)
):
    """获取模板的节次列表"""
    periods = await service.get_periods(template_id)
    items = [PeriodResponse.model_validate(p).model_dump() for p in periods]
    return success(data={"periods": items, "total": len(items)})


# ============ 课程规划管理 ============

@router.get("/plans", response_model=dict)
async def list_plans(
    cycle_id: Optional[str] = Query(None, description="周次组合ID"),
    class_id: Optional[UUID] = Query(None, description="班级ID"),
    teacher_id: Optional[UUID] = Query(None, description="教师ID"),
    service: SchedulingDBService = Depends(get_service)
):
    """获取课程规划列表"""
    plans = await service.get_plans(cycle_id, class_id, teacher_id)
    items = [PlanResponse.model_validate(p).model_dump() for p in plans]
    return success(data={"plans": items, "total": len(items)})


@router.post("/plans", response_model=dict)
async def create_plan(
    data: PlanCreate,
    service: SchedulingDBService = Depends(get_service)
):
    """创建课程规划"""
    plan = await service.create_plan(data)
    return success(data=PlanResponse.model_validate(plan).model_dump())


@router.post("/plans/batch", response_model=dict)
async def batch_create_plans(
    items: List[PlanCreate],
    service: SchedulingDBService = Depends(get_service)
):
    """批量创建课程规划"""
    plans = await service.batch_create_plans(items)
    return success(data={"count": len(plans), "message": f"成功创建{len(plans)}条记录"})


# ============ 排课结果管理 ============

@router.get("/results", response_model=dict)
async def list_results(
    cycle_id: Optional[str] = Query(None, description="周次组合ID"),
    class_id: Optional[UUID] = Query(None, description="班级ID"),
    teacher_id: Optional[UUID] = Query(None, description="教师ID"),
    day_index: Optional[int] = Query(None, ge=1, le=7, description="星期几"),
    service: SchedulingDBService = Depends(get_service)
):
    """获取排课结果列表"""
    results = await service.get_results(cycle_id, class_id, teacher_id, day_index)
    items = [ResultResponse.model_validate(r).model_dump() for r in results]
    return success(data={"results": items, "total": len(items)})


@router.post("/results", response_model=dict)
async def create_result(
    data: ResultCreate,
    service: SchedulingDBService = Depends(get_service)
):
    """创建排课结果"""
    result = await service.create_result(data)
    return success(data=ResultResponse.model_validate(result).model_dump())


@router.post("/results/batch", response_model=dict)
async def batch_create_results(
    items: List[ResultCreate],
    service: SchedulingDBService = Depends(get_service)
):
    """批量创建排课结果"""
    results = await service.batch_create_results(items)
    return success(data={"count": len(results), "message": f"成功创建{len(results)}条记录"})


@router.put("/results/{result_id}", response_model=dict)
async def update_result(
    result_id: UUID,
    data: ResultUpdate,
    service: SchedulingDBService = Depends(get_service)
):
    """更新排课结果"""
    result = await service.update_result(
        result_id,
        day_index=data.day_index,
        period_index=data.period_index,
        is_locked=data.is_locked
    )
    if not result:
        raise HTTPException(status_code=404, detail="排课结果不存在")
    return success(data=ResultResponse.model_validate(result).model_dump())


@router.delete("/results/{cycle_id}", response_model=dict)
async def delete_results(
    cycle_id: str,
    locked_only: bool = Query(False, description="仅删除未锁定的"),
    service: SchedulingDBService = Depends(get_service)
):
    """删除周次组合的排课结果"""
    count = await service.delete_results_by_cycle(cycle_id, locked_only)
    return success(data={"count": count}, message=f"成功删除{count}条记录")


# ============ 调课补丁管理 ============

@router.get("/patches", response_model=dict)
async def list_patches(
    natural_date: Optional[date] = Query(None, description="日期"),
    class_id: Optional[UUID] = Query(None, description="班级ID"),
    status: Optional[str] = Query(None, description="状态"),
    service: SchedulingDBService = Depends(get_service)
):
    """获取调课补丁列表"""
    patches = await service.get_patches(natural_date, class_id, status)
    items = [PatchResponse.model_validate(p).model_dump() for p in patches]
    return success(data={"patches": items, "total": len(items)})


@router.post("/patches", response_model=dict)
async def create_patch(
    data: PatchCreate,
    service: SchedulingDBService = Depends(get_service)
):
    """创建调课补丁"""
    patch = await service.create_patch(data)
    return success(data=PatchResponse.model_validate(patch).model_dump())


@router.put("/patches/{patch_id}/cancel", response_model=dict)
async def cancel_patch(
    patch_id: UUID,
    service: SchedulingDBService = Depends(get_service)
):
    """取消调课补丁"""
    patch = await service.cancel_patch(patch_id)
    if not patch:
        raise HTTPException(status_code=404, detail="调课补丁不存在")
    return success(data=PatchResponse.model_validate(patch).model_dump())


# ============ 冲突检测 ============

@router.get("/conflicts", response_model=dict)
async def check_conflicts(
    cycle_id: str = Query(..., description="周次组合ID"),
    class_id: Optional[UUID] = Query(None, description="班级ID"),
    teacher_id: Optional[UUID] = Query(None, description="教师ID"),
    service: SchedulingDBService = Depends(get_service)
):
    """检测排课冲突"""
    has_conflicts, conflicts = await service.check_conflicts(cycle_id, class_id, teacher_id)
    return success(data={
        "has_conflicts": has_conflicts,
        "conflicts": conflicts,
        "total": len(conflicts)
    })


# ============ 课表查询 ============

@router.get("/schedule/class/{class_id}", response_model=dict)
async def get_class_schedule(
    class_id: UUID,
    cycle_id: Optional[str] = Query(None, description="周次组合ID"),
    natural_date: Optional[date] = Query(None, description="日期"),
    service: SchedulingDBService = Depends(get_service)
):
    """获取班级课表"""
    schedule = await service.get_class_schedule(class_id, cycle_id, natural_date)
    return success(data=schedule)


@router.get("/schedule/teacher/{teacher_id}", response_model=dict)
async def get_teacher_schedule(
    teacher_id: UUID,
    cycle_id: Optional[str] = Query(None, description="周次组合ID"),
    natural_date: Optional[date] = Query(None, description="日期"),
    service: SchedulingDBService = Depends(get_service)
):
    """获取教师课表"""
    schedule = await service.get_teacher_schedule(teacher_id, cycle_id, natural_date)
    return success(data=schedule)


# ============ 拖拽调整 ============

@router.post("/drag-adjust", response_model=dict)
async def drag_adjust(
    request: DragAdjustRequest,
    service: SchedulingDBService = Depends(get_service)
):
    """拖拽调整课程"""
    result = await service.drag_adjust(request)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return success(data=result)


# ============ 事件管理 ============

@router.get("/events", response_model=dict)
async def list_events(
    semester_id: str = Query(..., description="学期ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    service: SchedulingDBService = Depends(get_service)
):
    """获取事件列表"""
    events = await service.get_events(semester_id, start_date, end_date)
    items = [EventResponse.model_validate(e).model_dump() for e in events]
    return success(data={"events": items, "total": len(items)})


@router.post("/events", response_model=dict)
async def create_event(
    data: EventCreate,
    service: SchedulingDBService = Depends(get_service)
):
    """创建批量事件"""
    event = await service.create_event(data)
    return success(data=EventResponse.model_validate(event).model_dump())


# ============ 长期代课管理 ============

@router.post("/replaces", response_model=dict)
async def create_replace(
    data: ReplaceCreate,
    service: SchedulingDBService = Depends(get_service)
):
    """创建长期代课"""
    replace = await service.create_replace(data)
    return success(data=ReplaceResponse.model_validate(replace).model_dump())


# ============ 约束管理 ============

@router.get("/constraints", response_model=dict)
async def list_constraints(
    semester_id: Optional[str] = Query(None, description="学期ID"),
    constraint_type: Optional[str] = Query(None, description="约束类型"),
    service: SchedulingDBService = Depends(get_service)
):
    """获取约束列表"""
    constraints = await service.get_constraints(semester_id, constraint_type)
    items = [ConstraintResponse.model_validate(c).model_dump() for c in constraints]
    return success(data={"constraints": items, "total": len(items)})


@router.post("/constraints", response_model=dict)
async def create_constraint(
    data: ConstraintCreate,
    service: SchedulingDBService = Depends(get_service)
):
    """创建约束"""
    constraint = await service.create_constraint(data)
    return success(data=ConstraintResponse.model_validate(constraint).model_dump())


# ============ 辅助接口 ============

@router.get("/classes", response_model=dict)
async def list_classes_for_scheduling(
    service: SchedulingDBService = Depends(get_service)
):
    """获取班级列表（用于排课）"""
    from sqlalchemy import select
    from app.models.class_model import Class
    from app.models.grade_model import Grade

    result = await service.db.execute(
        select(Class, Grade.grade_level)
        .outerjoin(Grade, Class.grade_id == Grade.id)
        .order_by(Class.name)
    )
    rows = result.all()
    items = [{
        "id": str(cls.id),
        "name": cls.name,
        "grade_level": grade_level if rows else None,
    } for cls, grade_level in rows]
    return success(data={"classes": items, "total": len(items)})


@router.get("/courses", response_model=dict)
async def list_courses_for_scheduling(
    service: SchedulingDBService = Depends(get_service)
):
    """获取课程列表（用于排课）"""
    from sqlalchemy import select
    from app.models.course import Course

    result = await service.db.execute(
        select(Course).order_by(Course.name)
    )
    courses = result.scalars().all()
    items = [{
        "id": str(c.id),
        "name": c.name,
        "code": c.code,
        "teacher_id": str(c.teacher_id) if c.teacher_id else None,
        "teacher_ids": [str(t) for t in (c.teacher_ids or [])],
        "grade_id": str(c.grade_id) if c.grade_id else None,
        "grade_levels": list(c.grade_levels) if c.grade_levels else [],
        "semester": c.semester,
        "course_type": c.course_type.value if hasattr(c.course_type, 'value') else str(c.course_type),
    } for c in courses]
    return success(data={"courses": items, "total": len(items)})


@router.get("/teachers", response_model=dict)
async def list_teachers_for_scheduling(
    service: SchedulingDBService = Depends(get_service)
):
    """获取教师列表（用于排课）"""
    from sqlalchemy import select
    from app.models.user import User
    from app.models.teacher_profile import TeacherProfile

    result = await service.db.execute(
        select(User, TeacherProfile)
        .join(TeacherProfile, User.id == TeacherProfile.user_id)
        .order_by(User.real_name)
    )
    rows = result.all()
    items = [{"id": str(u.id), "name": u.real_name or u.username} for u, _ in rows]
    return success(data={"teachers": items, "total": len(items)})


@router.get("/classrooms", response_model=dict)
async def list_classrooms_for_scheduling(
    service: SchedulingDBService = Depends(get_service)
):
    """获取教室列表（用于排课）"""
    from sqlalchemy import select
    from app.models.schedule import Classroom

    result = await service.db.execute(
        select(Classroom).where(Classroom.status == "active").order_by(Classroom.building, Classroom.room_no)
    )
    classrooms = result.scalars().all()
    items = [{"id": str(c.id), "name": f"{c.building or ''}{c.room_no}", "capacity": c.capacity} for c in classrooms]
    return success(data={"classrooms": items, "total": len(items)})
