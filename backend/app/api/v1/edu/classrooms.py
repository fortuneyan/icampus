"""
教室管理接口
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.models.schedule import Classroom

router = APIRouter()


class ClassroomCreate(BaseModel):
    """创建教室请求"""
    building: str
    room_no: str
    capacity: int = 0
    room_type: str = "普通教室"


class ClassroomUpdate(BaseModel):
    """更新教室请求"""
    building: Optional[str] = None
    room_no: Optional[str] = None
    capacity: Optional[int] = None
    room_type: Optional[str] = None
    status: Optional[str] = None


@router.get("", response_model=dict)
async def get_classrooms(
    building: Optional[str] = Query(None),
    room_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教室列表"""
    query = select(Classroom)
    if building:
        query = query.where(Classroom.building == building)
    if room_type:
        query = query.where(Classroom.room_type == room_type)
    if status:
        query = query.where(Classroom.status == status)

    query = query.order_by(Classroom.building, Classroom.room_no)

    total_result = await db.execute(query)
    total = len(total_result.scalars().all())

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    classrooms = result.scalars().all()

    items = [
        {
            "id": str(c.id),
            "building": c.building,
            "room_no": c.room_no,
            "capacity": c.capacity,
            "room_type": c.room_type,
            "status": c.status,
        }
        for c in classrooms
    ]

    from app.schemas.response import page_response
    return page_response(items, total, page, page_size)


@router.get("/options", response_model=dict)
async def get_classroom_options(
    status: str = Query("active"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教室下拉选项"""
    result = await db.execute(select(Classroom).where(Classroom.status == status))
    classrooms = result.scalars().all()
    options = [
        {"value": str(c.id), "label": f"{c.building}-{c.room_no}"} for c in classrooms
    ]
    from app.schemas.response import success
    return success(options)


@router.get("/buildings")
async def get_buildings(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """获取教学楼列表"""
    from app.schemas.response import success
    result = await db.execute(select(Classroom.building).distinct())
    buildings = [r[0] for r in result.fetchall() if r[0]]
    return success(buildings)


@router.get("/{classroom_id}", response_model=dict)
async def get_classroom(
    classroom_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教室详情"""
    result = await db.execute(select(Classroom).where(Classroom.id == classroom_id))
    classroom = result.scalar_one_or_none()

    if not classroom:
        raise NotFoundException("教室不存在")

    from app.schemas.response import success
    return success({
        "id": str(classroom.id),
        "building": classroom.building,
        "room_no": classroom.room_no,
        "capacity": classroom.capacity,
        "room_type": classroom.room_type,
        "status": classroom.status,
    })


@router.post("")
async def create_classroom(
    data: ClassroomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建教室"""
    from app.schemas.response import success
    classroom = Classroom(
        building=data.building,
        room_no=data.room_no,
        capacity=data.capacity,
        room_type=data.room_type,
        status="active",
    )
    db.add(classroom)
    await db.commit()
    await db.refresh(classroom)
    return success({"id": str(classroom.id)})


@router.put("/{classroom_id}")
async def update_classroom(
    classroom_id: UUID,
    data: ClassroomUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新教室"""
    from app.schemas.response import success
    result = await db.execute(select(Classroom).where(Classroom.id == classroom_id))
    classroom = result.scalar_one_or_none()

    if not classroom:
        raise NotFoundException("教室不存在")

    if data.building is not None:
        classroom.building = data.building
    if data.room_no is not None:
        classroom.room_no = data.room_no
    if data.capacity is not None:
        classroom.capacity = data.capacity
    if data.room_type is not None:
        classroom.room_type = data.room_type
    if data.status is not None:
        classroom.status = data.status

    await db.commit()
    await db.refresh(classroom)
    return success({"id": str(classroom.id)})


@router.delete("/{classroom_id}")
async def delete_classroom(
    classroom_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除教室"""
    from app.schemas.response import success
    result = await db.execute(select(Classroom).where(Classroom.id == classroom_id))
    classroom = result.scalar_one_or_none()

    if not classroom:
        raise NotFoundException("教室不存在")

    await db.delete(classroom)
    await db.commit()
    return success(None)
