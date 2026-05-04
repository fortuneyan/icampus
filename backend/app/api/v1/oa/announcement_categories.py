"""
公告分类API
"""

from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.oa.announcement_category import (
    AnnouncementCategoryCreate,
    AnnouncementCategoryUpdate,
    AnnouncementCategoryResponse,
)
from app.schemas.response import success, page_response
from app.services.oa.announcement_category_svc import AnnouncementCategoryService

router = APIRouter()


@router.get("", response_model=dict)
async def get_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取公告分类列表"""
    service = AnnouncementCategoryService(db)
    categories = await service.get_list()
    return success(categories)


@router.get("/{category_id}", response_model=dict)
async def get_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取分类详情"""
    service = AnnouncementCategoryService(db)
    category = await service.get_by_id(category_id)
    return success(category)


@router.post("", response_model=dict)
async def create_category(
    data: AnnouncementCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建公告分类"""
    service = AnnouncementCategoryService(db)
    category = await service.create(data.model_dump())
    return success({"id": str(category.id)}, "分类创建成功")


@router.put("/{category_id}", response_model=dict)
async def update_category(
    category_id: UUID,
    data: AnnouncementCategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新分类"""
    service = AnnouncementCategoryService(db)
    category = await service.update(category_id, data.model_dump(exclude_unset=True))
    return success({"id": str(category.id)}, "分类更新成功")


@router.delete("/{category_id}", response_model=dict)
async def delete_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除分类"""
    service = AnnouncementCategoryService(db)
    await service.delete(category_id)
    return success(message="分类删除成功")
