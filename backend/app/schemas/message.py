"""
消息相关 Schemas
"""

from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class MessageCreate(BaseModel):
    user_id: UUID
    title: str = Field(..., max_length=200)
    content: Optional[str] = None
    msg_type: str = "system"
    priority: int = 0


class MessageResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    content: Optional[str] = None
    msg_type: str
    priority: int
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UnreadCount(BaseModel):
    total: int
    system: int
    notice: int
    task: int
