"""
年级服务
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grade_model import Grade
from app.core.exceptions import NotFoundException, ConflictException
from app.services.base_service import BaseService


class GradeService(BaseService[Grade]):
    """年级服务"""

    def __init__(self, db: AsyncSession):
        super().__init__(Grade, db)

    async def get_by_year(self, year: int) -> List[Grade]:
        """根据年份获取年级"""
        return await self.get_all([Grade.year == year])

    async def create_grade(self, data: dict) -> Grade:
        """创建年级"""
        existing = await self.get_all(
            [Grade.year == data["year"], Grade.grade_level == data["grade_level"]]
        )
        if existing:
            raise ConflictException("该年级已存在")

        return await self.create(data)

    async def update_grade(self, grade_id: UUID, data: dict) -> Grade:
        """更新年级"""
        grade = await self.get(grade_id)
        if not grade:
            raise NotFoundException("年级不存在")

        return await self.update(grade_id, data)

    async def get_grade_options(self) -> List[dict]:
        """获取年级下拉选项"""
        grades = await self.get_all([Grade.status == "active"])
        return [{"id": str(g.id), "label": g.name, "value": str(g.id)} for g in grades]
