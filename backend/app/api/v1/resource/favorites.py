"""
资源收藏接口
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.resource_favorite import ResourceFavorite
from app.schemas.response import success, page_response

router = APIRouter()


class FavoriteCreate(BaseModel):
    resource_id: UUID
    resource_type: Optional[str] = None
    resource_name: Optional[str] = None


@router.get("", response_model=dict)
async def get_favorites(
    resource_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取收藏列表"""
    query = (
        select(ResourceFavorite)
        .where(ResourceFavorite.user_id == current_user.id)
        .order_by(desc(ResourceFavorite.created_at))
    )

    if resource_type:
        query = query.where(ResourceFavorite.resource_type == resource_type)

    total_result = await db.execute(query)
    total = len(total_result.scalars().all())

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    favorites = result.scalars().all()

    items = [
        {
            "id": str(f.id),
            "resource_id": str(f.resource_id),
            "resource_type": f.resource_type,
            "resource_name": f.resource_name,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in favorites
    ]

    return page_response(items, total, page, page_size)


@router.post("", response_model=dict)
async def add_favorite(
    data: FavoriteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加收藏"""
    existing = await db.execute(
        select(ResourceFavorite).where(
            and_(
                ResourceFavorite.user_id == current_user.id,
                ResourceFavorite.resource_id == data.resource_id,
            )
        )
    )
    if existing.scalar_one_or_none():
        return success(message="已经收藏过该资源")

    favorite = ResourceFavorite(
        user_id=current_user.id,
        resource_id=data.resource_id,
        resource_type=data.resource_type,
        resource_name=data.resource_name,
    )
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)
    return success({"id": str(favorite.id)}, "收藏成功")


@router.delete("/{resource_id}", response_model=dict)
async def remove_favorite(
    resource_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取消收藏"""
    result = await db.execute(
        select(ResourceFavorite).where(
            and_(
                ResourceFavorite.user_id == current_user.id,
                ResourceFavorite.resource_id == resource_id,
            )
        )
    )
    favorite = result.scalar_one_or_none()

    if favorite:
        await db.delete(favorite)
        await db.commit()

    return success(message="取消收藏成功")


@router.get("/check/{resource_id}", response_model=dict)
async def check_favorite(
    resource_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """检查是否已收藏"""
    result = await db.execute(
        select(ResourceFavorite).where(
            and_(
                ResourceFavorite.user_id == current_user.id,
                ResourceFavorite.resource_id == resource_id,
            )
        )
    )
    is_favorited = result.scalar_one_or_none() is not None
    return success({"is_favorited": is_favorited})
