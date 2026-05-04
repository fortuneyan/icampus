"""
公告通知API
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.oa.announcement import AnnouncementCreate, AnnouncementUpdate
from app.schemas.response import success, page_response
from app.services.oa.announcement_svc import AnnouncementService

router = APIRouter()


@router.get("/categories", response_model=dict)
async def get_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取公告分类列表"""
    service = AnnouncementService(db)
    categories = await service.get_categories()
    return success(categories)


@router.get("", response_model=dict)
async def get_announcements(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取公告列表"""
    service = AnnouncementService(db)
    result = await service.get_list(
        page=page,
        page_size=page_size,
        status=status,
        category=category,
        keyword=keyword,
        current_user=current_user,
    )
    return page_response(result["items"], result["total"], page, page_size)


@router.get("/unread-count", response_model=dict)
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取未读公告数量"""
    service = AnnouncementService(db)
    count = await service.get_unread_count(current_user.id)
    return success({"count": count})


@router.get("/{announcement_id}", response_model=dict)
async def get_announcement_detail(
    announcement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取公告详情"""
    service = AnnouncementService(db)
    detail = await service.get_detail(announcement_id, current_user)
    return success(detail)


@router.post("", response_model=dict)
async def create_announcement(
    data: AnnouncementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建公告"""
    service = AnnouncementService(db)
    announcement = await service.create(data.model_dump(), current_user.id)
    return success({"id": str(announcement.id)}, "公告创建成功")


@router.put("/{announcement_id}", response_model=dict)
async def update_announcement(
    announcement_id: UUID,
    data: AnnouncementUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新公告"""
    service = AnnouncementService(db)
    announcement = await service.update(announcement_id, data.model_dump(exclude_unset=True))
    return success({"id": str(announcement.id)}, "公告更新成功")


@router.delete("/{announcement_id}", response_model=dict)
async def delete_announcement(
    announcement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除公告"""
    service = AnnouncementService(db)
    await service.delete(announcement_id, current_user.id)
    return success(message="公告删除成功")


@router.post("/{announcement_id}/publish", response_model=dict)
async def publish_announcement(
    announcement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发布公告"""
    service = AnnouncementService(db)
    announcement = await service.publish(announcement_id)
    return success({"id": str(announcement.id), "status": announcement.status}, "公告发布成功")


@router.post("/{announcement_id}/archive", response_model=dict)
async def archive_announcement(
    announcement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """归档公告"""
    service = AnnouncementService(db)
    announcement = await service.archive(announcement_id)
    return success({"id": str(announcement.id), "status": announcement.status}, "公告归档成功")


@router.post("/{announcement_id}/pin", response_model=dict)
async def pin_announcement(
    announcement_id: UUID,
    pin: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """置顶/取消置顶公告"""
    service = AnnouncementService(db)
    announcement = await service.pin(announcement_id, pin)
    return success({"id": str(announcement.id), "pin_top": announcement.pin_top}, "操作成功")


@router.post("/{announcement_id}/read", response_model=dict)
async def mark_as_read(
    announcement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """标记已读"""
    service = AnnouncementService(db)
    await service.mark_read(announcement_id, current_user.id)
    return success(message="标记成功")


@router.get("/{announcement_id}/stats", response_model=dict)
async def get_read_stats(
    announcement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取阅读统计"""
    service = AnnouncementService(db)
    stats = await service.get_read_stats(announcement_id)
    return success(stats)


@router.get("/{announcement_id}/comments", response_model=dict)
async def get_comments(
    announcement_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取评论列表"""
    service = AnnouncementService(db)
    result = await service.get_comments(announcement_id, page, page_size)
    return page_response(result["items"], result["total"], page, page_size)


@router.post("/{announcement_id}/comments", response_model=dict)
async def add_comment(
    announcement_id: UUID,
    content: str,
    parent_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加评论"""
    service = AnnouncementService(db)
    comment = await service.add_comment(
        announcement_id=announcement_id,
        user_id=current_user.id,
        content=content,
        parent_id=UUID(parent_id) if parent_id else None,
    )
    return success({"id": str(comment.id)}, "评论成功")


@router.delete("/comments/{comment_id}", response_model=dict)
async def delete_comment(
    comment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除评论"""
    service = AnnouncementService(db)
    await service.delete_comment(comment_id, current_user.id)
    return success(message="评论删除成功")