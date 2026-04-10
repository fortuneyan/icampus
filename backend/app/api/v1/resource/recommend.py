"""
个性化推荐接口
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.recommendation import Recommendation
from app.schemas.response import success, page_response

router = APIRouter()


@router.get("", response_model=dict)
async def get_recommendations(
    resource_type: Optional[str] = Query(None),
    recommendation_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取个性化推荐"""
    query = (
        select(Recommendation)
        .where(Recommendation.user_id == current_user.id)
        .order_by(desc(Recommendation.score), desc(Recommendation.created_at))
    )

    if resource_type:
        query = query.where(Recommendation.resource_type == resource_type)
    if recommendation_type:
        query = query.where(Recommendation.recommendation_type == recommendation_type)

    total_result = await db.execute(query)
    total = len(total_result.scalars().all())

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    recs = result.scalars().all()

    items = [
        {
            "id": str(r.id),
            "resource_type": r.resource_type,
            "resource_id": str(r.resource_id),
            "resource_name": r.resource_name,
            "recommendation_type": r.recommendation_type,
            "score": r.score,
            "reason": r.reason,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in recs
    ]

    return page_response(items, total, page, page_size)


@router.post("", response_model=dict)
async def create_recommendation(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建推荐记录（内部使用）"""
    rec = Recommendation(
        user_id=current_user.id,
        resource_type=data.get("resource_type"),
        resource_id=data.get("resource_id"),
        resource_name=data.get("resource_name"),
        recommendation_type=data.get("recommendation_type"),
        score=data.get("score", 0.0),
        reason=data.get("reason"),
    )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)
    return success({"id": str(rec.id)})


@router.put("/{rec_id}/click", response_model=dict)
async def mark_clicked(
    rec_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """标记推荐点击"""
    result = await db.execute(
        select(Recommendation).where(
            Recommendation.id == rec_id, Recommendation.user_id == current_user.id
        )
    )
    rec = result.scalar_one_or_none()

    if rec:
        rec.is_clicked = "true"
        await db.commit()

    return success(message="标记成功")


@router.get("/popular", response_model=dict)
async def get_popular_resources(
    resource_type: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取热门推荐"""
    query = select(Recommendation).order_by(desc(Recommendation.score))

    if resource_type:
        query = query.where(Recommendation.resource_type == resource_type)

    query = query.limit(limit)
    result = await db.execute(query)
    recs = result.scalars().all()

    items = [
        {
            "resource_type": r.resource_type,
            "resource_id": str(r.resource_id),
            "resource_name": r.resource_name,
            "score": r.score,
        }
        for r in recs
    ]

    return success(items)
