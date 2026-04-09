"""
仪表盘接口
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.response import success
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/overview", response_model=dict)
async def get_overview(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    service = DashboardService(db)
    data = await service.get_overview()
    return success(data)


@router.get("/statistics", response_model=dict)
async def get_statistics(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    service = DashboardService(db)
    data = await service.get_statistics()
    return success(data)


@router.get("/charts", response_model=dict)
async def get_charts(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    service = DashboardService(db)
    data = await service.get_charts()
    return success(data)


@router.get("/quick-actions", response_model=dict)
async def get_quick_actions(current_user: User = Depends(get_current_user)):
    from app.services.dashboard_service import DashboardService
    from unittest.mock import MagicMock

    service = DashboardService(MagicMock())
    actions = await service.get_quick_actions(current_user.id)
    return success(actions)
