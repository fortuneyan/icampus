from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.notification import NotificationCreate, NotificationUpdate
from app.schemas.response import success, page_response
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("", response_model=dict)
async def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NotificationService(db)
    result = await service.get_user_notifications(current_user.id, page, page_size)
    
    items = [
        {
            "id": str(n.id),
            "title": n.title,
            "content": n.content,
            "notification_type": n.notification_type,
            "is_urgent": n.is_urgent,
            "published_at": n.published_at.isoformat() if n.published_at else None,
            "created_at": n.created_at.isoformat(),
        }
        for n in result["items"]
    ]
    
    return page_response(items, result["total"], page, page_size)


@router.get("/admin", response_model=dict)
async def get_notifications_admin(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import select, func
    from app.models.notification import Notification
    
    query = select(Notification).order_by(Notification.created_at.desc())
    
    if status:
        query = query.where(Notification.status == status)
    
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    total = len(notifications)
    offset = (page - 1) * page_size
    items = notifications[offset:offset + page_size]
    
    return page_response([
        {
            "id": str(n.id),
            "title": n.title,
            "notification_type": n.notification_type,
            "scope_type": n.scope_type,
            "status": n.status,
            "published_at": n.published_at.isoformat() if n.published_at else None,
            "created_at": n.created_at.isoformat(),
        }
        for n in items
    ], total, page, page_size)


@router.post("", response_model=dict)
async def create_notification(
    data: NotificationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NotificationService(db)
    notification = await service.create_notification(data.model_dump(), current_user.id)
    return success({"id": str(notification.id)}, "通知创建成功")


@router.get("/{notification_id}", response_model=dict)
async def get_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NotificationService(db)
    notification = await service.get(notification_id)
    
    if not notification:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("通知不存在")
    
    return success({
        "id": str(notification.id),
        "title": notification.title,
        "content": notification.content,
        "notification_type": notification.notification_type,
        "scope_type": notification.scope_type,
        "is_urgent": notification.is_urgent,
        "status": notification.status,
        "published_at": notification.published_at.isoformat() if notification.published_at else None,
        "created_at": notification.created_at.isoformat(),
    })


@router.put("/{notification_id}", response_model=dict)
async def update_notification(
    notification_id: UUID,
    data: NotificationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NotificationService(db)
    notification = await service.get(notification_id)
    
    if not notification:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("通知不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(notification, key, value)
    
    await db.commit()
    await db.refresh(notification)
    
    return success({"id": str(notification.id)}, "通知更新成功")


@router.delete("/{notification_id}", response_model=dict)
async def delete_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NotificationService(db)
    notification = await service.get(notification_id)
    
    if not notification:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("通知不存在")
    
    await service.delete(notification_id)
    
    return success(message="通知删除成功")


@router.post("/{notification_id}/send", response_model=dict)
async def send_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NotificationService(db)
    notification = await service.send_notification(notification_id)
    
    if not notification:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("通知不存在")
    
    return success(message="通知发送成功")


@router.get("/{notification_id}/reads", response_model=dict)
async def get_read_status(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NotificationService(db)
    reads = await service.get_read_status(notification_id)
    return success(reads)


@router.post("/{notification_id}/read", response_model=dict)
async def mark_as_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = NotificationService(db)
    result = await service.mark_as_read(notification_id, current_user.id)
    
    if result:
        return success(message="标记已读")
    return success(message="无需标记")