"""
资源服务
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resource import Resource, ResourceCategory
from app.core.exceptions import NotFoundException
from app.services.base_service import BaseService


class ResourceService(BaseService[Resource]):
    """资源服务"""

    def __init__(self, db: AsyncSession):
        super().__init__(Resource, db)

    async def create_resource(self, data: dict, teacher_id: UUID) -> Resource:
        data["teacher_id"] = teacher_id
        return await self.create(data)

    async def update_view_count(self, resource_id: UUID) -> None:
        resource = await self.get(resource_id)
        if resource:
            resource.view_count += 1
            await self.db.commit()

    async def search_resources(
        self,
        keyword: Optional[str] = None,
        category_id: Optional[UUID] = None,
        resource_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        filters = [Resource.status == "published"]
        if keyword:
            filters.append(Resource.title.ilike(f"%{keyword}%"))
        if category_id:
            filters.append(Resource.category_id == category_id)
        if resource_type:
            filters.append(Resource.resource_type == resource_type)

        return await self.paginate(page, page_size, filters, "created_at", True)


class CategoryService(BaseService[ResourceCategory]):
    """分类服务"""

    def __init__(self, db: AsyncSession):
        super().__init__(ResourceCategory, db)

    async def get_category_tree(self, parent_id: Optional[UUID] = None) -> List[dict]:
        if parent_id:
            categories = await self.get_all(
                [
                    ResourceCategory.parent_id == parent_id,
                    ResourceCategory.status == "active",
                ]
            )
        else:
            categories = await self.get_all(
                [
                    ResourceCategory.parent_id.is_(None),
                    ResourceCategory.status == "active",
                ]
            )

        tree = []
        for cat in categories:
            children = await self.get_category_tree(cat.id)
            tree.append(
                {
                    "id": str(cat.id),
                    "label": cat.name,
                    "value": str(cat.id),
                    "children": children if children else [],
                }
            )
        return tree
