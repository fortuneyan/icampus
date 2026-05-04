"""
教室预约API
"""

from typing import Optional, List
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.oa.room import MeetingRoomCreate as RoomCreate, MeetingRoomUpdate as RoomUpdate, RoomBookingCreate as BookingCreate
from app.schemas.response import success, page_response
from app.services.oa.room_booking_svc import RoomService, RoomBookingService

router = APIRouter()


# ============ 教室管理 ============

@router.get("", response_model=dict)
async def get_rooms(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    room_type: Optional[str] = Query(None),
    building: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教室列表"""
    service = RoomService(db)
    result = await service.get_room_list(
        page=page,
        page_size=page_size,
        room_type=room_type,
        building=building,
        status=status,
    )
    return page_response(result["items"], result["total"], page, page_size)


@router.get("/{room_id}", response_model=dict)
async def get_room_detail(
    room_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教室详情"""
    service = RoomService(db)
    room = await service.get_room_detail(room_id)
    return success(room)


@router.post("", response_model=dict)
async def create_room(
    data: RoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加教室"""
    service = RoomService(db)
    room = await service.create_room(data.model_dump())
    return success({"id": str(room.id)}, "教室添加成功")


@router.put("/{room_id}", response_model=dict)
async def update_room(
    room_id: UUID,
    data: RoomUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """编辑教室"""
    service = RoomService(db)
    room = await service.update_room(room_id, data.model_dump(exclude_unset=True))
    return success({"id": str(room.id)}, "教室更新成功")


@router.delete("/{room_id}", response_model=dict)
async def delete_room(
    room_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除教室"""
    service = RoomService(db)
    await service.delete_room(room_id)
    return success(message="教室删除成功")


@router.get("/{room_id}/availability", response_model=dict)
async def get_room_availability(
    room_id: UUID,
    query_date: date,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教室可用时间"""
    service = RoomService(db)
    slots = await service.get_room_availability(room_id, query_date)
    return success(slots)


# ============ 预约管理 ============

@router.get("/bookings", response_model=dict)
async def get_bookings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    room_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取预约记录列表"""
    service = RoomBookingService(db)
    result = await service.get_booking_list(
        page=page,
        page_size=page_size,
        status=status,
        room_id=UUID(room_id) if room_id else None,
        current_user=current_user,
    )
    return page_response(result["items"], result["total"], page, page_size)


@router.get("/bookings/{booking_id}", response_model=dict)
async def get_booking_detail(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取预约详情"""
    service = RoomBookingService(db)
    booking = await service.get_booking_detail(booking_id)
    return success(booking)


@router.post("/bookings", response_model=dict)
async def create_booking(
    data: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发起预约申请"""
    service = RoomBookingService(db)
    booking = await service.create_booking(data.model_dump(), current_user.id)
    return success({"id": str(booking.id)}, "预约申请已提交")


@router.post("/bookings/{booking_id}/cancel", response_model=dict)
async def cancel_booking(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取消预约"""
    service = RoomBookingService(db)
    booking = await service.cancel_booking(booking_id, current_user.id)
    return success({"id": str(booking.id)}, "预约已取消")


@router.post("/bookings/{booking_id}/remind", response_model=dict)
async def remind_approval(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """催审批"""
    service = RoomBookingService(db)
    await service.remind_approval(booking_id, current_user.id)
    return success(message="催审批已发送")


# ============ 我的预约 ============

@router.get("/my/bookings", response_model=dict)
async def get_my_bookings(
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我的预约"""
    service = RoomBookingService(db)
    bookings = await service.get_my_bookings(current_user.id, status)
    return success(bookings)


@router.get("/my/bookings/history", response_model=dict)
async def get_my_booking_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取历史预约"""
    service = RoomBookingService(db)
    result = await service.get_my_history(current_user.id, page, page_size)
    return page_response(result["items"], result["total"], page, page_size)