"""
公告通知Schema
"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class AnnouncementBase(BaseModel):
    """公告基础Schema"""
    title: str = Field(..., min_length=1, max_length=200, description="公告标题")
    content: str = Field(..., min_length=1, description="公告内容(Markdown)")
    category: str = Field(default="general", description="分类: general/important/urgent")
    priority: int = Field(default=0, ge=0, le=100, description="优先级 0-100")
    cover_image: Optional[str] = Field(default=None, description="封面图片URL")
    attachments: Optional[List[str]] = Field(default=None, description="附件列表")
    is_top: bool = Field(default=False, description="是否置顶")
    top_expire_at: Optional[datetime] = Field(default=None, description="置顶过期时间")
    publish_time: Optional[datetime] = Field(default=None, description="定时发布时间")
    expire_time: Optional[datetime] = Field(default=None, description="过期时间")


class AnnouncementCreate(AnnouncementBase):
    """创建公告Schema"""
    target_type: str = Field(default="all", description="目标类型: all/department/role/user")
    target_ids: Optional[List[UUID]] = Field(default=None, description="目标对象ID列表")


class AnnouncementUpdate(BaseModel):
    """更新公告Schema"""
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content: Optional[str] = Field(default=None, min_length=1)
    category: Optional[str] = Field(default=None)
    priority: Optional[int] = Field(default=None, ge=0, le=100)
    cover_image: Optional[str] = Field(default=None)
    attachments: Optional[List[str]] = Field(default=None)
    is_top: Optional[bool] = Field(default=None)
    top_expire_at: Optional[datetime] = Field(default=None)
    expire_time: Optional[datetime] = Field(default=None)


class AnnouncementRead(AnnouncementBase):
    """公告读取Schema"""
    id: UUID
    status: str = Field(description="状态: draft/published/archived")
    publisher_id: UUID
    publisher_name: Optional[str] = Field(default=None)
    view_count: int = Field(default=0)
    read_count: int = Field(default=0)
    comment_count: int = Field(default=0)
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = Field(default=None)

    class Config:
        from_attributes = True


class AnnouncementListItem(BaseModel):
    """公告列表项Schema"""
    id: UUID
    title: str
    category: str
    priority: int
    is_top: bool
    status: str
    publisher_name: Optional[str] = None
    view_count: int
    read_count: int
    created_at: datetime
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnnouncementCommentCreate(BaseModel):
    """创建评论Schema"""
    content: str = Field(..., min_length=1, max_length=2000)
    parent_id: Optional[UUID] = Field(default=None)


class AnnouncementCommentRead(BaseModel):
    """评论读取Schema"""
    id: UUID
    content: str
    user_id: UUID
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
    parent_id: Optional[UUID] = None
    created_at: datetime
    replies: Optional[List['AnnouncementCommentRead']] = None

    class Config:
        from_attributes = True


class AnnouncementStats(BaseModel):
    """公告统计Schema"""
    total_users: int
    read_count: int
    unread_count: int
    read_rate: float


class AnnouncementReadRecord(BaseModel):
    """阅读记录Schema"""
    id: UUID
    user_id: UUID
    user_name: Optional[str] = None
    read_at: datetime

    class Config:
        from_attributes = True
