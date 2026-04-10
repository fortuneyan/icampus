"""
排课管理接口
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.schedule import Schedule
from app.schemas.response import success, page_response

router = APIRouter()


def parse_uuid(value: Optional[str]) -> Optional[UUID]:
    """解析UUID参数"""
    if not value:
        return None
    try:
        return UUID(value)
    except (ValueError, AttributeError):
        return None


@router.get("", response_model=dict)
async def get_schedules(
    class_id: Optional[str] = Query(None, description="班级ID"),
    teacher_id: Optional[str] = Query(None, description="教师ID"),
    course_id: Optional[str] = Query(None, description="课程ID"),
    weekday: Optional[int] = Query(None, description="星期"),
    week: Optional[int] = Query(None, description="周次"),
    semester: Optional[str] = Query(None, description="学期"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取排课列表"""
    query = select(Schedule).order_by(Schedule.created_at.desc())

    if class_id:
        uid = parse_uuid(class_id)
        if uid:
            query = query.where(Schedule.class_id == uid)

    if teacher_id:
        uid = parse_uuid(teacher_id)
        if uid:
            query = query.where(Schedule.teacher_id == uid)

    if course_id:
        uid = parse_uuid(course_id)
        if uid:
            query = query.where(Schedule.course_id == uid)

    if weekday:
        query = query.where(Schedule.weekday == weekday)

    if week:
        query = query.where(Schedule.week == week)

    if semester:
        query = query.where(Schedule.semester == semester)

    total_result = await db.execute(query)
    total = len(total_result.scalars().all())

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    schedules = result.scalars().all()

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
            "week": s.week,
            "semester": s.semester,
            "week_range": s.week_range,
        }
        for s in schedules
    ]

    return page_response(items, total, page, page_size)


@router.get("/class/{class_id}", response_model=dict)
async def get_class_schedule(
    class_id: str,
    semester: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取班级课表"""
    uid = parse_uuid(class_id)
    if not uid:
        return success([])

    query = select(Schedule).where(Schedule.class_id == uid)
    if semester:
        query = query.where(Schedule.semester == semester)

    result = await db.execute(query)
    schedules = result.scalars().all()

    items = [
        {
            "id": str(s.id),
            "course_id": str(s.course_id),
            "teacher_id": str(s.teacher_id),
            "room_id": str(s.room_id) if s.room_id else None,
            "weekday": s.weekday,
            "period_start": s.period_start,
            "period_end": s.period_end,
            "week": s.week,
        }
        for s in schedules
    ]

    return success(items)


@router.get("/teacher/{teacher_id}", response_model=dict)
async def get_teacher_schedule(
    teacher_id: str,
    semester: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教师课表"""
    uid = parse_uuid(teacher_id)
    if not uid:
        return success([])

    query = select(Schedule).where(Schedule.teacher_id == uid)
    if semester:
        query = query.where(Schedule.semester == semester)

    result = await db.execute(query)
    schedules = result.scalars().all()

    items = [
        {
            "id": str(s.id),
            "course_id": str(s.course_id),
            "class_id": str(s.class_id),
            "weekday": s.weekday,
            "period_start": s.period_start,
            "period_end": s.period_end,
            "week": s.week,
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
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()

    if not schedule:
        return success(None)

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
            "week": schedule.week,
            "semester": schedule.semester,
            "week_range": schedule.week_range,
        }
    )


@router.post("", response_model=dict)
async def create_schedule(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建排课"""
    schedule = Schedule(**data)
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return success({"id": str(schedule.id)}, "排课创建成功")


@router.put("/{schedule_id}", response_model=dict)
async def update_schedule(
    schedule_id: UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新排课"""
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()

    if not schedule:
        return success(message="排课不存在")

    for key, value in data.items():
        setattr(schedule, key, value)

    await db.commit()
    return success({"id": str(schedule.id)}, "排课更新成功")


@router.delete("/{schedule_id}", response_model=dict)
async def delete_schedule(
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除排课"""
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()

    if schedule:
        await db.delete(schedule)
        await db.commit()

    return success(message="排课删除成功")
