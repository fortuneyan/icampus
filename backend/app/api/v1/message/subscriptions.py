"""
消息订阅接口
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.message_subscription import MessageSubscription
from app.schemas.response import success, page_response

router = APIRouter()


class SubscriptionCreate(BaseModel):
    channel: str
    message_type: Optional[str] = None
    is_enabled: Optional[str] = "true"


class SubscriptionUpdate(BaseModel):
    message_type: Optional[str] = None
    is_enabled: Optional[str] = None


@router.get("", response_model=dict)
async def get_subscriptions(
    channel: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取订阅列表"""
    query = (
        select(MessageSubscription)
        .where(MessageSubscription.user_id == current_user.id)
        .order_by(MessageSubscription.created_at.desc())
    )

    if channel:
        query = query.where(MessageSubscription.channel == channel)

    total_result = await db.execute(query)
    total = len(total_result.scalars().all())

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    subs = result.scalars().all()

    items = [
        {
            "id": str(s.id),
            "channel": s.channel,
            "message_type": s.message_type,
            "is_enabled": s.is_enabled,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in subs
    ]

    return page_response(items, total, page, page_size)


@router.post("", response_model=dict)
async def create_subscription(
    data: SubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建订阅"""
    existing = await db.execute(
        select(MessageSubscription).where(
            and_(
                MessageSubscription.user_id == current_user.id,
                MessageSubscription.channel == data.channel,
            )
        )
    )
    if existing.scalar_one_or_none():
        return success(message="已经订阅过该渠道")

    sub = MessageSubscription(
        user_id=current_user.id,
        channel=data.channel,
        message_type=data.message_type,
        is_enabled=data.is_enabled,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return success({"id": str(sub.id)}, "订阅成功")


@router.delete("/{subscription_id}", response_model=dict)
async def delete_subscription(
    subscription_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取消订阅"""
    result = await db.execute(
        select(MessageSubscription).where(
            and_(
                MessageSubscription.id == subscription_id,
                MessageSubscription.user_id == current_user.id,
            )
        )
    )
    sub = result.scalar_one_or_none()

    if sub:
        await db.delete(sub)
        await db.commit()

    return success(message="取消订阅成功")


@router.put("/{subscription_id}", response_model=dict)
async def update_subscription(
    subscription_id: UUID,
    data: SubscriptionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新订阅"""
    result = await db.execute(
        select(MessageSubscription).where(
            and_(
                MessageSubscription.id == subscription_id,
                MessageSubscription.user_id == current_user.id,
            )
        )
    )
    sub = result.scalar_one_or_none()

    if not sub:
        return success(message="订阅不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(sub, key, value)

    await db.commit()
    return success(message="订阅更新成功")
