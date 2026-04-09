"""
设置服务
"""

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dashboard import SystemSetting


class SettingsService:
    """设置服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_setting(self, key: str) -> Optional[SystemSetting]:
        """获取配置"""
        result = await self.db.execute(
            select(SystemSetting).where(SystemSetting.setting_key == key)
        )
        return result.scalar_one_or_none()

    async def get_all_settings(self) -> List[SystemSetting]:
        """获取所有配置"""
        result = await self.db.execute(select(SystemSetting))
        return list(result.scalars().all())

    async def update_setting(
        self, key: str, value: Any, value_type: str = "string"
    ) -> SystemSetting:
        """更新配置"""
        setting = await self.get_setting(key)
        if setting:
            setting.setting_value = (
                str(value) if value_type in ["string", "int", "boolean"] else str(value)
            )
            setting.value_type = value_type
        else:
            setting = SystemSetting(
                setting_key=key, setting_value=str(value), value_type=value_type
            )
            self.db.add(setting)

        await self.db.commit()
        await self.db.refresh(setting)
        return setting

    async def get_system_info(self) -> dict:
        """获取系统信息"""
        return {
            "app_version": "1.0.0",
            "python_version": "3.14.0",
            "database_type": "PostgreSQL",
            "os_type": "Windows",
            "server_time": datetime.now().isoformat(),
        }

    async def get_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        level: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """获取系统日志"""
        logs = [
            {
                "id": "1",
                "level": "INFO",
                "message": "系统启动",
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": "2",
                "level": "INFO",
                "message": "用户登录",
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": "3",
                "level": "WARNING",
                "message": "登录失败",
                "created_at": datetime.now().isoformat(),
            },
        ]
        return {"items": logs, "total": len(logs), "page": page, "page_size": page_size}
