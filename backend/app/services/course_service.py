"""
课程服务
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course
from app.core.exceptions import NotFoundException, ConflictException
from app.services.base_service import BaseService


class CourseService(BaseService[Course]):
    """课程服务"""

    def __init__(self, db: AsyncSession):
        super().__init__(Course, db)

    async def get_by_code(self, code: str) -> Optional[Course]:
        """根据课程代码获取课程"""
        return await self.get_by_field("code", code)

    async def create_course(self, data: dict) -> Course:
        """创建课程"""
        if await self.get_by_code(data["code"]):
            raise ConflictException("课程代码已存在")

        return await self.create(data)

    async def update_course(self, course_id: UUID, data: dict) -> Course:
        """更新课程"""
        course = await self.get(course_id)
        if not course:
            raise NotFoundException("课程不存在")

        return await self.update(course_id, data)

    async def get_course_options(self, grade_id: Optional[UUID] = None) -> List[dict]:
        """获取课程下拉选项"""
        filters = [Course.status == "active"]
        if grade_id:
            filters.append(Course.grade_id == grade_id)

        courses = await self.get_all(filters)
        return [{"id": str(c.id), "label": f"{c.code} - {c.name}", "value": str(c.id)} for c in courses]
