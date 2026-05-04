"""
工作日志分类API
路径: /oa/worklog-categories/*
"""

from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.response import success
from app.services.oa.worklog_svc import WorkLogService

router = APIRouter()


@router.get("", response_model=dict)
async def get_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取工作日志分类列表"""
    service = WorkLogService(db)
    categories = await service.get_categories()
    return success(categories)


@router.post("", response_model=dict)
async def create_category(
    name: str,
    color: Optional[str] = "#1890ff",
    icon: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建工作日志分类"""
    service = WorkLogService(db)
    category = await service.create_category(
        name=name,
        color=color,
        icon=icon,
        user_id=current_user.id,
    )
    return success({"id": str(category["id"])}, "分类创建成功")


@router.put("/{category_id}", response_model=dict)
async def update_category(
    category_id: UUID,
    name: Optional[str] = None,
    color: Optional[str] = None,
    icon: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新工作日志分类"""
    service = WorkLogService(db)
    category = await service.update_category(
        category_id=category_id,
        name=name,
        color=color,
        icon=icon,
    )
    return success({"id": str(category["id"])}, "分类更新成功")


@router.delete("/{category_id}", response_model=dict)
async def delete_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除工作日志分类"""
    service = WorkLogService(db)
    await service.delete_category(category_id)
    return success(message="分类删除成功")
