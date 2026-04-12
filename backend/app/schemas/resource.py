"""
资源相关 Schemas
"""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class ResourceCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    resource_type: Optional[str] = Field(None, max_length=50)
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    duration: Optional[int] = None
    category_id: Optional[UUID] = None
    course_id: Optional[UUID] = None
    tags: Optional[str] = Field(None, max_length=200)
    status: str = "published"


class ResourceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    resource_type: Optional[str] = None
    file_url: Optional[str] = None
    category_id: Optional[UUID] = None
    tags: Optional[str] = None
    status: Optional[str] = None


class ResourceResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    resource_type: Optional[str] = None
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    duration: Optional[int] = None
    category_id: Optional[UUID] = None
    course_id: Optional[UUID] = None
    teacher_id: Optional[UUID] = None
    view_count: int
    like_count: int
    collect_count: int
    status: str
    tags: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CategoryCreate(BaseModel):
    name: str = Field(..., max_length=100)
    parent_id: Optional[UUID] = None
    sort_order: int = 0
    icon: Optional[str] = Field(None, max_length=50)


class CategoryResponse(BaseModel):
    id: UUID
    name: str
    parent_id: Optional[UUID] = None
    sort_order: int
    icon: Optional[str] = None
    status: str

    model_config = ConfigDict(from_attributes=True)
