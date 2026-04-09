"""
排课相关 Schemas
"""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class ScheduleCreate(BaseModel):
    """创建排课请求"""

    course_id: UUID
    class_id: UUID
    teacher_id: UUID
    room_id: Optional[UUID] = None
    weekday: int = Field(..., ge=1, le=7)
    period_start: int = Field(..., ge=1, le=12)
    period_end: int = Field(..., ge=1, le=12)
    semester: str = Field(..., max_length=20)
    week_range: Optional[str] = Field(None, max_length=50)


class ScheduleUpdate(BaseModel):
    """更新排课请求"""

    course_id: Optional[UUID] = None
    class_id: Optional[UUID] = None
    teacher_id: Optional[UUID] = None
    room_id: Optional[UUID] = None
    weekday: Optional[int] = None
    period_start: Optional[int] = None
    period_end: Optional[int] = None
    semester: Optional[str] = None
    week_range: Optional[str] = None


class ScheduleResponse(BaseModel):
    """排课响应"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    class_id: UUID
    teacher_id: UUID
    room_id: Optional[UUID] = None
    weekday: int
    period_start: int
    period_end: int
    semester: Optional[str] = None
    week_range: Optional[str] = None


class ScheduleQuery(BaseModel):
    """排课查询参数"""

    class_id: Optional[UUID] = None
    teacher_id: Optional[UUID] = None
    semester: Optional[str] = None
