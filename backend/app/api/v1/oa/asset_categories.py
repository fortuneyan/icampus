"""
资产分类API
路径: /oa/asset-categories/*
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.oa.asset import AssetCategoryCreate, AssetCategoryUpdate
from app.schemas.response import success
from app.services.oa.asset_svc import AssetCategoryService

router = APIRouter()


@router.get("", response_model=dict)
async def get_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取资产分类树"""
    service = AssetCategoryService(db)
    tree = await service.get_category_tree()
    return success(tree)


@router.post("", response_model=dict)
async def create_category(
    data: AssetCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加分类"""
    service = AssetCategoryService(db)
    category = await service.create_category(data.model_dump())
    return success({"id": str(category.id)}, "分类添加成功")


@router.put("/{category_id}", response_model=dict)
async def update_category(
    category_id: UUID,
    data: AssetCategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新分类"""
    service = AssetCategoryService(db)
    category = await service.update_category(category_id, data.model_dump(exclude_unset=True))
    return success({"id": str(category.id)}, "分类更新成功")


@router.delete("/{category_id}", response_model=dict)
async def delete_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除分类"""
    service = AssetCategoryService(db)
    await service.delete_category(category_id)
    return success(message="分类删除成功")
