"""
教室预约Schema
"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class MeetingRoomBase(BaseModel):
    """会议室基础Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="会议室名称")
    code: str = Field(..., min_length=1, max_length=50, description="会议室编码")
    location: str = Field(..., max_length=200, description="位置")
    capacity: int = Field(..., ge=1, le=1000, description="容纳人数")
    equipment: Optional[List[str]] = Field(default=None, description="设备清单")
    description: Optional[str] = Field(default=None, max_length=500, description="描述")
    booking_rules: Optional[dict] = Field(default=None, description="预约规则")


class MeetingRoomCreate(MeetingRoomBase):
    """创建会议室Schema"""
    pass


class MeetingRoomUpdate(BaseModel):
    """更新会议室Schema"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    location: Optional[str] = Field(default=None, max_length=200)
    capacity: Optional[int] = Field(default=None, ge=1, le=1000)
    equipment: Optional[List[str]] = Field(default=None)
    description: Optional[str] = Field(default=None, max_length=500)
    booking_rules: Optional[dict] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)


class MeetingRoomRead(MeetingRoomBase):
    """会议室读取Schema"""
    id: UUID
    code: str
    is_active: bool = Field(default=True)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoomBookingBase(BaseModel):
    """预约基础Schema"""
    room_id: UUID = Field(..., description="会议室ID")
    title: str = Field(..., min_length=1, max_length=200, description="预约主题")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    attendees: Optional[List[UUID]] = Field(default=None, description="参与人员")
    description: Optional[str] = Field(default=None, max_length=1000, description="说明")
    recurring: Optional[dict] = Field(default=None, description="重复规则")


class RoomBookingCreate(RoomBookingBase):
    """创建预约Schema"""
    pass


class RoomBookingUpdate(BaseModel):
    """更新预约Schema"""
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    start_time: Optional[datetime] = Field(default=None)
    end_time: Optional[datetime] = Field(default=None)
    attendees: Optional[List[UUID]] = Field(default=None)
    description: Optional[str] = Field(default=None, max_length=1000)
    recurring: Optional[dict] = Field(default=None)


class RoomBookingRead(RoomBookingBase):
    """预约读取Schema"""
    id: UUID
    applicant_id: UUID
    applicant_name: Optional[str] = None
    room_name: Optional[str] = None
    status: str = Field(description="状态: pending/approved/rejected/cancelled")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoomBookingListItem(BaseModel):
    """预约列表项Schema"""
    id: UUID
    title: str
    room_name: str
    start_time: datetime
    end_time: datetime
    status: str
    applicant_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AvailableSlot(BaseModel):
    """可用时间段Schema"""
    start_time: datetime
    end_time: datetime
    is_available: bool = True


class BookingConflict(BaseModel):
    """预约冲突Schema"""
    has_conflict: bool
    conflicts: Optional[List[RoomBookingRead]] = None
