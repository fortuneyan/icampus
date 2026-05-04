"""
工作日志Schema
"""

from typing import Optional, List
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field


class WorklogCategoryBase(BaseModel):
    """日志分类基础Schema"""
    name: str = Field(..., min_length=1, max_length=50)
    icon: Optional[str] = Field(default=None)
    color: Optional[str] = Field(default=None)
    sort_order: int = Field(default=0)


class WorklogCategoryCreate(WorklogCategoryBase):
    """创建分类Schema"""


class WorklogCategoryUpdate(BaseModel):
    """更新分类Schema"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    icon: Optional[str] = None
    color: Optional[str] = None
    sort_order: Optional[int] = None


class WorklogCategoryRead(WorklogCategoryBase):
    """分类读取Schema"""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class WorklogBase(BaseModel):
    """日志基础Schema"""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    log_date: date = Field(..., description="日志日期")
    category_id: Optional[UUID] = Field(default=None)
    attachments: Optional[List[str]] = Field(default=None)


class WorklogCreate(WorklogBase):
    """创建日志Schema"""
    pass


class WorklogUpdate(BaseModel):
    """更新日志Schema"""
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content: Optional[str] = Field(default=None, min_length=1)
    category_id: Optional[UUID] = None
    attachments: Optional[List[str]] = None


class WorklogRead(WorklogBase):
    """日志读取Schema"""
    id: UUID
    user_id: UUID
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
    category_name: Optional[str] = None
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    is_liked: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorklogListItem(BaseModel):
    """日志列表项Schema"""
    id: UUID
    title: str
    content_preview: Optional[str] = None
    log_date: date
    category_name: Optional[str] = None
    user_name: Optional[str] = None
    view_count: int
    like_count: int
    comment_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class WorklogCommentCreate(BaseModel):
    """评论Schema"""
    content: str = Field(..., min_length=1, max_length=1000)


class WorklogCommentRead(BaseModel):
    """评论读取Schema"""
    id: UUID
    content: str
    user_id: UUID
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WorklogStats(BaseModel):
    """统计Schema"""
    monthly_count: int
    weekly_count: int
    daily_count: int
    total_words: int
    streak_days: int
    avg_words_per_day: float


class WorklogWeeklyReport(BaseModel):
    """周报Schema"""
    week_start: date
    week_end: date
    total_logs: int
    total_words: int
    categories: List[dict]
    daily_summary: List[dict]
