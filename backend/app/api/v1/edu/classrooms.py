"""
教室管理接口
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.models.schedule import Classroom

router = APIRouter()


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

    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        },
        "timestamp": datetime.now().isoformat(),
    }


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
    return {"code": 200, "message": "success", "data": options}


@router.get("/buildings", response_model=dict)
async def get_buildings(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """获取教学楼列表"""
    result = await db.execute(select(Classroom.building).distinct())
    buildings = [r[0] for r in result.fetchall() if r[0]]
    return {"code": 200, "message": "success", "data": buildings}


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

    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": str(classroom.id),
            "building": classroom.building,
            "room_no": classroom.room_no,
            "capacity": classroom.capacity,
            "room_type": classroom.room_type,
            "status": classroom.status,
        },
    }


@router.post("", response_model=dict)
async def create_classroom(
    building: str = Query(...),
    room_no: str = Query(...),
    capacity: int = Query(0),
    room_type: str = Query("普通教室"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建教室"""
    classroom = Classroom(
        building=building,
        room_no=room_no,
        capacity=capacity,
        room_type=room_type,
        status="active",
    )
    db.add(classroom)
    await db.commit()
    await db.refresh(classroom)
    return {"code": 200, "message": "教室创建成功", "data": {"id": str(classroom.id)}}


@router.put("/{classroom_id}", response_model=dict)
async def update_classroom(
    classroom_id: UUID,
    building: Optional[str] = Query(None),
    room_no: Optional[str] = Query(None),
    capacity: Optional[int] = Query(None),
    room_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新教室"""
    result = await db.execute(select(Classroom).where(Classroom.id == classroom_id))
    classroom = result.scalar_one_or_none()

    if not classroom:
        raise NotFoundException("教室不存在")

    if building is not None:
        classroom.building = building
    if room_no is not None:
        classroom.room_no = room_no
    if capacity is not None:
        classroom.capacity = capacity
    if room_type is not None:
        classroom.room_type = room_type
    if status is not None:
        classroom.status = status

    await db.commit()
    await db.refresh(classroom)
    return {"code": 200, "message": "教室更新成功", "data": {"id": str(classroom.id)}}


@router.delete("/{classroom_id}", response_model=dict)
async def delete_classroom(
    classroom_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除教室"""
    result = await db.execute(select(Classroom).where(Classroom.id == classroom_id))
    classroom = result.scalar_one_or_none()

    if not classroom:
        raise NotFoundException("教室不存在")

    await db.delete(classroom)
    await db.commit()
    return {"code": 200, "message": "教室删除成功"}


from datetime import datetime
