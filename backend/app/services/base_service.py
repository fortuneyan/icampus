"""
通用服务基类
"""

from typing import Generic, TypeVar, Type, Optional, List, Any
from datetime import datetime
from uuid import UUID
from sqlalchemy import select, func, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseService(Generic[ModelType]):
    """通用服务基类"""

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: UUID) -> Optional[ModelType]:
        """获取单条记录"""
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_by_field(self, field_name: str, value: Any) -> Optional[ModelType]:
        """根据字段获取单条记录"""
        field = getattr(self.model, field_name)
        result = await self.db.execute(select(self.model).where(field == value))
        return result.scalar_one_or_none()

    async def get_list(
        self,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[List] = None,
        order_by: Optional[str] = None,
        desc: bool = True,
    ) -> List[ModelType]:
        """获取列表"""
        query = select(self.model)
        if filters:
            query = query.where(and_(*filters))
        if order_by:
            order_field = getattr(self.model, order_by, None)
            if order_field:
                query = query.order_by(
                    order_field.desc() if desc else order_field.asc()
                )
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_all(self, filters: Optional[List] = None) -> List[ModelType]:
        """获取所有记录"""
        query = select(self.model)
        if filters:
            query = query.where(and_(*filters))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count(self, filters: Optional[List] = None) -> int:
        """统计数量"""
        query = select(func.count()).select_from(self.model)
        if filters:
            query = query.where(and_(*filters))
        result = await self.db.execute(query)
        return result.scalar()

    async def create(self, data: dict) -> ModelType:
        """创建记录"""
        instance = self.model(**data)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def update(self, id: UUID, data: dict) -> Optional[ModelType]:
        """更新记录"""
        instance = await self.get(id)
        if instance:
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            if hasattr(instance, "updated_at"):
                instance.updated_at = datetime.now()
            await self.db.commit()
            await self.db.refresh(instance)
        return instance

    async def delete(self, id: UUID) -> bool:
        """删除记录"""
        instance = await self.get(id)
        if instance:
            await self.db.delete(instance)
            await self.db.commit()
            return True
        return False

    async def soft_delete(self, id: UUID) -> Optional[ModelType]:
        """软删除"""
        return await self.update(id, {"deleted_at": datetime.now()})

    async def exists(self, filters: List) -> bool:
        """检查记录是否存在"""
        return await self.count(filters) > 0

    async def paginate(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[List] = None,
        order_by: Optional[str] = "created_at",
        desc: bool = True,
    ) -> dict:
        """分页查询"""
        total = await self.count(filters)
        skip = (page - 1) * page_size
        items = await self.get_list(skip, page_size, filters, order_by, desc)
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
        }
