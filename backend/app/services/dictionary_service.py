"""
字典管理服务
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dictionary import DictionaryType, DictionaryItem
from app.services.base_service import BaseService


class DictionaryTypeService(BaseService[DictionaryType]):
    """字典类型服务"""

    def __init__(self, db: AsyncSession):
        super().__init__(DictionaryType, db)

    async def get_by_code(self, code: str) -> Optional[DictionaryType]:
        """根据编码获取字典类型"""
        stmt = select(DictionaryType).where(DictionaryType.code == code)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_items(self, type_id: UUID) -> Optional[DictionaryType]:
        """获取字典类型及其项"""
        stmt = select(DictionaryType).where(DictionaryType.id == type_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


class DictionaryItemService(BaseService[DictionaryItem]):
    """字典项服务"""

    def __init__(self, db: AsyncSession):
        super().__init__(DictionaryItem, db)

    async def get_by_type(self, type_id: UUID, status: str = None) -> List[DictionaryItem]:
        """获取字典类型的所有项"""
        filters = [DictionaryItem.type_id == type_id]
        if status:
            filters.append(DictionaryItem.status == status)
        
        stmt = select(DictionaryItem).where(*filters).order_by(DictionaryItem.sort_order)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_type_code(self, type_code: str, status: str = None) -> List[dict]:
        """根据字典类型编码获取字典项"""
        type_service = DictionaryTypeService(self.db)
        dict_type = await type_service.get_by_code(type_code)
        
        if not dict_type:
            return []
        
        items = await self.get_by_type(dict_type.id, status)
        return [
            {
                "label": item.label,
                "value": item.value,
                "sort_order": item.sort_order,
                "remark": item.remark
            }
            for item in items
        ]
