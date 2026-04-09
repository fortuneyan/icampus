"""
排课管理接口
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate
from app.schemas.response import success, page_response
from app.services.schedule_service import ScheduleService

router = APIRouter()


@router.get("", response_model=dict)
async def get_schedules(
    class_id: Optional[UUID] = Query(None),
    teacher_id: Optional[UUID] = Query(None),
    semester: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取排课列表"""
    schedule_service = ScheduleService(db)

    filters = []
    if class_id:
        filters.append(ScheduleService.model.class_id == class_id)
    if teacher_id:
        filters.append(ScheduleService.model.teacher_id == teacher_id)
    if semester:
        filters.append(ScheduleService.model.semester == semester)

    result = await schedule_service.paginate(page, page_size, filters)

    items = [
        {
            "id": str(s.id),
            "course_id": str(s.course_id),
            "class_id": str(s.class_id),
            "teacher_id": str(s.teacher_id),
            "room_id": str(s.room_id) if s.room_id else None,
            "weekday": s.weekday,
            "period_start": s.period_start,
            "period_end": s.period_end,
            "semester": s.semester,
            "week_range": s.week_range,
        }
        for s in result["items"]
    ]

    return page_response(items, result["total"], page, page_size)


@router.get("/class/{class_id}", response_model=dict)
async def get_class_schedule(
    class_id: UUID,
    semester: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取班级课表"""
    schedule_service = ScheduleService(db)
    schedules = await schedule_service.get_class_schedule(class_id, semester)

    items = [
        {
            "id": str(s.id),
            "course_id": str(s.course_id),
            "teacher_id": str(s.teacher_id),
            "room_id": str(s.room_id) if s.room_id else None,
            "weekday": s.weekday,
            "period_start": s.period_start,
            "period_end": s.period_end,
            "week_range": s.week_range,
        }
        for s in schedules
    ]

    return success(items)


@router.get("/teacher/{teacher_id}", response_model=dict)
async def get_teacher_schedule(
    teacher_id: UUID,
    semester: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教师课表"""
    schedule_service = ScheduleService(db)
    schedules = await schedule_service.get_teacher_schedule(teacher_id, semester)

    items = [
        {
            "id": str(s.id),
            "course_id": str(s.course_id),
            "class_id": str(s.class_id),
            "room_id": str(s.room_id) if s.room_id else None,
            "weekday": s.weekday,
            "period_start": s.period_start,
            "period_end": s.period_end,
            "week_range": s.week_range,
        }
        for s in schedules
    ]

    return success(items)


@router.get("/{schedule_id}", response_model=dict)
async def get_schedule(
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取排课详情"""
    schedule_service = ScheduleService(db)
    schedule = await schedule_service.get(schedule_id)

    if not schedule:
        raise NotFoundException("排课不存在")

    return success(
        {
            "id": str(schedule.id),
            "course_id": str(schedule.course_id),
            "class_id": str(schedule.class_id),
            "teacher_id": str(schedule.teacher_id),
            "room_id": str(schedule.room_id) if schedule.room_id else None,
            "weekday": schedule.weekday,
            "period_start": schedule.period_start,
            "period_end": schedule.period_end,
            "semester": schedule.semester,
            "week_range": schedule.week_range,
        }
    )


@router.post("", response_model=dict)
async def create_schedule(
    data: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建排课"""
    schedule_service = ScheduleService(db)
    schedule = await schedule_service.create_schedule(data.model_dump())
    return success({"id": str(schedule.id)}, "排课创建成功")


@router.put("/{schedule_id}", response_model=dict)
async def update_schedule(
    schedule_id: UUID,
    data: ScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新排课"""
    schedule_service = ScheduleService(db)
    schedule = await schedule_service.update_schedule(
        schedule_id, data.model_dump(exclude_unset=True)
    )
    return success({"id": str(schedule.id)}, "排课更新成功")


@router.delete("/{schedule_id}", response_model=dict)
async def delete_schedule(
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除排课"""
    schedule_service = ScheduleService(db)
    await schedule_service.delete_schedule(schedule_id)
    return success(message="排课删除成功")
