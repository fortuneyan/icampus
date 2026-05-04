"""
公告分类Schema
"""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class AnnouncementCategoryBase(BaseModel):
    """公告分类基础Schema"""
    name: str = Field(..., min_length=1, max_length=50, description="分类名称")
    code: str = Field(..., min_length=1, max_length=30, description="分类编码")
    color: str = Field(default="#1890ff", description="分类颜色")
    icon: Optional[str] = Field(default=None, description="分类图标")
    sort_order: int = Field(default=0, ge=0, description="排序顺序")
    description: Optional[str] = Field(default=None, max_length=200, description="分类描述")
    is_active: bool = Field(default=True, description="是否启用")


class AnnouncementCategoryCreate(AnnouncementCategoryBase):
    """创建公告分类Schema"""
    pass


class AnnouncementCategoryUpdate(BaseModel):
    """更新公告分类Schema"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    code: Optional[str] = Field(default=None, min_length=1, max_length=30)
    color: Optional[str] = Field(default=None)
    icon: Optional[str] = Field(default=None)
    sort_order: Optional[int] = Field(default=None, ge=0)
    description: Optional[str] = Field(default=None, max_length=200)
    is_active: Optional[bool] = Field(default=None)


class AnnouncementCategoryResponse(AnnouncementCategoryBase):
    """公告分类响应Schema"""
    id: UUID
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
