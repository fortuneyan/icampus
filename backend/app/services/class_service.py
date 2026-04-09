"""
班级服务
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.class_model import Class
from app.core.exceptions import NotFoundException, ConflictException
from app.services.base_service import BaseService


class ClassService(BaseService[Class]):
    """班级服务"""

    def __init__(self, db: AsyncSession):
        super().__init__(Class, db)

    async def get_by_grade(self, grade_id: UUID) -> List[Class]:
        """获取年级下的所有班级"""
        return await self.get_all(
            [Class.grade_id == grade_id, Class.status == "active"]
        )

    async def create_class(self, data: dict) -> Class:
        """创建班级"""
        existing = await self.get_all(
            [Class.grade_id == data.get("grade_id"), Class.class_no == data["class_no"]]
        )
        if existing:
            raise ConflictException("该班级已存在")

        return await self.create(data)

    async def update_class(self, class_id: UUID, data: dict) -> Class:
        """更新班级"""
        cls = await self.get(class_id)
        if not cls:
            raise NotFoundException("班级不存在")

        return await self.update(class_id, data)

    async def get_class_tree(self, grade_id: Optional[UUID] = None) -> List[dict]:
        """获取班级树形结构"""
        filters = [Class.status == "active"]
        if grade_id:
            filters.append(Class.grade_id == grade_id)

        classes = await self.get_all(filters)

        tree = []
        for cls in classes:
            tree.append(
                {
                    "id": str(cls.id),
                    "label": cls.name,
                    "value": str(cls.id),
                    "grade_id": str(cls.grade_id) if cls.grade_id else None,
                    "student_count": cls.student_count,
                }
            )

        return tree

    async def get_class_options(self, grade_id: Optional[UUID] = None) -> List[dict]:
        """获取班级下拉选项"""
        filters = [Class.status == "active"]
        if grade_id:
            filters.append(Class.grade_id == grade_id)

        classes = await self.get_all(filters)
        return [{"id": str(c.id), "label": c.name, "value": str(c.id)} for c in classes]
