"""
消息中心接口
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.message import MessageCreate
from app.schemas.response import success, page_response
from app.services.message_service import MessageService

router = APIRouter()


@router.get("/list", response_model=dict)
async def get_messages(
    is_read: Optional[bool] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = MessageService(db)
    result = await service.get_user_messages(current_user.id, page, page_size, is_read)
    items = [
        {
            "id": str(m.id),
            "title": m.title,
            "content": m.content,
            "msg_type": m.msg_type,
            "is_read": m.is_read,
            "created_at": m.created_at.isoformat(),
        }
        for m in result["items"]
    ]
    return page_response(items, result["total"], page, page_size)


@router.get("/unread-count", response_model=dict)
async def get_unread_count(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    service = MessageService(db)
    count = await service.get_unread_count(current_user.id)
    return success(count)


@router.post("/{id}/read", response_model=dict)
async def mark_as_read(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = MessageService(db)
    await service.mark_as_read(id, current_user.id)
    return success(message="标记成功")


@router.post("/mark-all-read", response_model=dict)
async def mark_all_read(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    service = MessageService(db)
    await service.mark_all_as_read(current_user.id)
    return success(message="全部已读")


@router.delete("/{id}", response_model=dict)
async def delete_message(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = MessageService(db)
    await service.delete_message(id, current_user.id)
    return success(message="删除成功")
