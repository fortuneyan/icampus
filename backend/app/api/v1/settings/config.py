"""
系统设置接口
"""

from typing import Optional, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.settings import SettingUpdate, LogQuery
from app.schemas.response import success, page_response
from app.services.settings_service import SettingsService

router = APIRouter()


@router.get("/config", response_model=dict)
async def get_config(
    key: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SettingsService(db)
    if key:
        setting = await service.get_setting(key)
        if setting:
            return success(
                {
                    "setting_key": setting.setting_key,
                    "setting_value": setting.setting_value,
                    "value_type": setting.value_type,
                }
            )
        return success(None)
    settings = await service.get_all_settings()
    items = [
        {
            "setting_key": s.setting_key,
            "setting_value": s.setting_value,
            "value_type": s.value_type,
        }
        for s in settings
    ]
    return success(items)


@router.put("/config", response_model=dict)
async def update_config(
    data: SettingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SettingsService(db)
    setting = await service.update_setting(
        data.setting_key, data.setting_value, data.value_type
    )
    return success({"setting_key": setting.setting_key}, "更新成功")


@router.get("/system-info", response_model=dict)
async def get_system_info(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    service = SettingsService(db)
    info = await service.get_system_info()
    return success(info)


@router.get("/logs", response_model=dict)
async def get_logs(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import datetime

    service = SettingsService(db)
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    result = await service.get_logs(start, end, level, page, page_size)
    return page_response(result["items"], result["total"], page, page_size)
