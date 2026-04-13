"""
通知公告接口
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.notice import NoticeCreate, NoticeUpdate
from app.schemas.response import success, page_response
from app.services.notice_service import NoticeService

router = APIRouter()


@router.get("/notices", response_model=dict)
async def get_notices(
    page: int = Query(1),
    page_size: int = Query(20),
    status: Optional[str] = Query(None, description="状态筛选: draft/published/archived"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NoticeService(db)
    result = await service.get_user_notices(current_user.id, page, page_size, status)
    items = [
        {
            "id": str(n.id),
            "title": n.title,
            "notice_type": n.notice_type,
            "priority": n.priority,
            "status": n.status,
            "published_at": n.published_at.isoformat() if n.published_at else None,
            "is_read": False,
        }
        for n in result["items"]
    ]
    return page_response(items, result["total"], page, page_size)


@router.get("/notices/unread-count", response_model=dict)
async def get_unread_count(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    service = NoticeService(db)
    count = await service.get_unread_count(current_user.id)
    return success({"count": count})


@router.post("/notices", response_model=dict)
async def create_notice(
    data: NoticeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NoticeService(db)
    notice = await service.create_notice(data.model_dump(), current_user.id)
    return success({"id": str(notice.id)}, "创建成功")


@router.put("/notices/{id}", response_model=dict)
async def update_notice(
    id: UUID,
    data: NoticeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NoticeService(db)
    notice = await service.update(id, data.model_dump(exclude_unset=True))
    return success({"id": str(notice.id)}, "更新成功")


@router.delete("/notices/{id}", response_model=dict)
async def delete_notice(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NoticeService(db)
    await service.soft_delete(id)
    return success(message="删除成功")


@router.post("/notices/{id}/read", response_model=dict)
async def mark_as_read(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NoticeService(db)
    await service.mark_as_read(id, current_user.id)
    return success(message="标记成功")


@router.post("/notices/{id}/publish", response_model=dict)
async def publish_notice(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发布通知（将草稿状态改为已发布）"""
    service = NoticeService(db)
    notice = await service.publish_notice(id)
    return success({"id": str(notice.id), "status": notice.status}, "发布成功")


@router.post("/notices/{id}/archive", response_model=dict)
async def archive_notice(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """归档通知（将已发布状态改为已归档）"""
    service = NoticeService(db)
    notice = await service.archive_notice(id)
    return success({"id": str(notice.id), "status": notice.status}, "归档成功")
