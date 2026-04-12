"""
考勤相关 Schemas
"""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, time


class RuleCreate(BaseModel):
    name: str = Field(..., max_length=100)
    check_in_start: Optional[time] = None
    check_in_end: Optional[time] = None
    check_out_start: Optional[time] = None
    check_out_end: Optional[time] = None
    location: Optional[str] = Field(None, max_length=200)


class RuleUpdate(BaseModel):
    name: Optional[str] = None
    check_in_start: Optional[time] = None
    check_in_end: Optional[time] = None
    check_out_start: Optional[time] = None
    check_out_end: Optional[time] = None
    location: Optional[str] = None
    status: Optional[str] = None


class RuleResponse(BaseModel):
    id: UUID
    name: str
    check_in_start: Optional[time] = None
    check_in_end: Optional[time] = None
    check_out_start: Optional[time] = None
    check_out_end: Optional[time] = None
    location: Optional[str] = None
    status: str

    model_config = ConfigDict(from_attributes=True)


class CheckInRequest(BaseModel):
    rule_id: Optional[UUID] = None
    photo: Optional[str] = None
    location: Optional[str] = Field(None, max_length=200)


class RecordResponse(BaseModel):
    id: UUID
    user_id: UUID
    rule_id: Optional[UUID] = None
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    check_in_location: Optional[str] = None
    status: str
    remarks: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
