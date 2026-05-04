"""
教室预约记录API
路径: /oa/room-bookings/*
"""

from typing import Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.oa.room import RoomBookingCreate as BookingCreate
from app.schemas.response import success, page_response
from app.services.oa.room_booking_svc import RoomBookingService

router = APIRouter()


@router.get("", response_model=dict)
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


@router.get("/{booking_id}", response_model=dict)
async def get_booking_detail(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取预约详情"""
    service = RoomBookingService(db)
    booking = await service.get_booking_detail(booking_id)
    return success(booking)


@router.post("", response_model=dict)
async def create_booking(
    data: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发起预约申请"""
    service = RoomBookingService(db)
    booking = await service.create_booking(data.model_dump(), current_user.id)
    return success({"id": str(booking.id)}, "预约申请已提交")


@router.post("/{booking_id}/cancel", response_model=dict)
async def cancel_booking(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取消预约"""
    service = RoomBookingService(db)
    booking = await service.cancel_booking(booking_id, current_user.id)
    return success({"id": str(booking.id)}, "预约已取消")


@router.post("/{booking_id}/remind", response_model=dict)
async def remind_approval(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """催审批"""
    service = RoomBookingService(db)
    await service.remind_approval(booking_id, current_user.id)
    return success(message="催审批已发送")


# 我的预约
@router.get("/my/list", response_model=dict)
async def get_my_bookings(
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我的预约"""
    service = RoomBookingService(db)
    bookings = await service.get_my_bookings(current_user.id, status)
    return success(bookings)


@router.get("/my/history", response_model=dict)
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
