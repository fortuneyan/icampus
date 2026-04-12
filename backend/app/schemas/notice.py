"""
通知相关 Schemas
"""

from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class NoticeCreate(BaseModel):
    title: str = Field(..., max_length=200)
    content: Optional[str] = None
    notice_type: str = "system"
    priority: int = 0
    target_type: str = "all"
    target_ids: Optional[List[str]] = None
    attachment_url: Optional[str] = None
    status: str = "draft"


class NoticeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    notice_type: Optional[str] = None
    priority: Optional[int] = None
    target_type: Optional[str] = None
    target_ids: Optional[List[str]] = None
    attachment_url: Optional[str] = None
    status: Optional[str] = None


class NoticeResponse(BaseModel):
    id: UUID
    title: str
    content: Optional[str] = None
    notice_type: str
    priority: int
    publisher_id: Optional[UUID] = None
    target_type: str
    attachment_url: Optional[str] = None
    published_at: Optional[datetime] = None
    status: str
    is_read: bool = False

    model_config = ConfigDict(from_attributes=True)
