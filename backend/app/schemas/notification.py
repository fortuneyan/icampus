from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime


class NotificationCreate(BaseModel):
    title: str = Field(..., max_length=200)
    content: str
    notification_type: str = "notice"
    scope_type: str = "all"
    scope_ids: Optional[list] = None
    is_urgent: bool = False


class NotificationUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = None
    notification_type: Optional[str] = None
    scope_type: Optional[str] = None
    scope_ids: Optional[list] = None
    is_urgent: Optional[bool] = None


class NotificationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    title: str
    content: str
    notification_type: Optional[str] = None
    sender_id: Optional[UUID] = None
    scope_type: Optional[str] = None
    scope_ids: Optional[list] = None
    is_urgent: bool = False
    status: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: datetime