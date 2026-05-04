"""
公告分类服务
"""

from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.oa.announcement_category import AnnouncementCategory


class AnnouncementCategoryService:
    """公告分类服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_list(self) -> List[Dict[str, Any]]:
        """获取分类列表"""
        # 先尝试从数据库获取
        result = await self.db.execute(
            select(AnnouncementCategory)
            .where(AnnouncementCategory.is_active == True)
            .order_by(AnnouncementCategory.sort_order, AnnouncementCategory.created_at)
        )
        categories = result.scalars().all()

        if categories:
            return [
                {
                    "id": str(cat.id),
                    "name": cat.name,
                    "code": cat.code,
                    "color": cat.color,
                    "icon": cat.icon,
                    "sort_order": cat.sort_order,
                    "description": cat.description,
                    "is_active": cat.is_active,
                    "created_at": cat.created_at.isoformat() if cat.created_at else None,
                    "updated_at": cat.updated_at.isoformat() if cat.updated_at else None,
                }
                for cat in categories
            ]

        # 如果数据库为空，返回默认分类
        return [
            {"id": "notice", "name": "通知公告", "code": "notice", "color": "#1890ff", "sort_order": 1},
            {"id": "activity", "name": "活动通知", "code": "activity", "color": "#52c41a", "sort_order": 2},
            {"id": "urgent", "name": "紧急通知", "code": "urgent", "color": "#f5222d", "sort_order": 3},
            {"id": "academic", "name": "学术通知", "code": "academic", "color": "#722ed1", "sort_order": 4},
            {"id": "exam", "name": "考试通知", "code": "exam", "color": "#fa8c16", "sort_order": 5},
        ]

    async def get_by_id(self, category_id: UUID) -> Optional[Dict[str, Any]]:
        """获取分类详情"""
        result = await self.db.execute(
            select(AnnouncementCategory).where(AnnouncementCategory.id == category_id)
        )
        category = result.scalar_one_or_none()

        if not category:
            return None

        return {
            "id": str(category.id),
            "name": category.name,
            "code": category.code,
            "color": category.color,
            "icon": category.icon,
            "sort_order": category.sort_order,
            "description": category.description,
            "is_active": category.is_active,
            "created_at": category.created_at.isoformat() if category.created_at else None,
            "updated_at": category.updated_at.isoformat() if category.updated_at else None,
        }

    async def create(self, data: Dict[str, Any]) -> AnnouncementCategory:
        """创建分类"""
        category = AnnouncementCategory(
            id=uuid4(),
            name=data["name"],
            code=data["code"],
            color=data.get("color", "#1890ff"),
            icon=data.get("icon"),
            sort_order=data.get("sort_order", 0),
            description=data.get("description"),
            is_active=data.get("is_active", True),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def update(self, category_id: UUID, data: Dict[str, Any]) -> Optional[AnnouncementCategory]:
        """更新分类"""
        result = await self.db.execute(
            select(AnnouncementCategory).where(AnnouncementCategory.id == category_id)
        )
        category = result.scalar_one_or_none()

        if not category:
            return None

        for key, value in data.items():
            if value is not None and hasattr(category, key):
                setattr(category, key, value)

        category.updated_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def delete(self, category_id: UUID) -> bool:
        """删除分类"""
        result = await self.db.execute(
            select(AnnouncementCategory).where(AnnouncementCategory.id == category_id)
        )
        category = result.scalar_one_or_none()

        if not category:
            return False

        await self.db.delete(category)
        await self.db.commit()
        return True

    async def exists(self, code: str) -> bool:
        """检查分类编码是否存在"""
        result = await self.db.execute(
            select(AnnouncementCategory).where(AnnouncementCategory.code == code)
        )
        return result.scalar_one_or_none() is not None
