"""
学生服务
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student
from app.core.exceptions import NotFoundException, ConflictException
from app.services.base_service import BaseService


class StudentService(BaseService[Student]):
    """学生服务"""

    def __init__(self, db: AsyncSession):
        super().__init__(Student, db)

    async def get_by_student_no(self, student_no: str) -> Optional[Student]:
        """根据学号获取学生"""
        return await self.get_by_field("student_no", student_no)

    async def get_by_id_card(self, id_card: str) -> Optional[Student]:
        """根据身份证号获取学生"""
        return await self.get_by_field("id_card", id_card)

    async def create_student(self, data: dict) -> Student:
        """创建学生"""
        if await self.get_by_student_no(data["student_no"]):
            raise ConflictException("学号已存在")

        if data.get("id_card") and await self.get_by_id_card(data["id_card"]):
            raise ConflictException("身份证号已存在")

        return await self.create(data)

    async def update_student(self, student_id: UUID, data: dict) -> Student:
        """更新学生"""
        student = await self.get(student_id)
        if not student:
            raise NotFoundException("学生不存在")

        if data.get("student_no") and data["student_no"] != student.student_no:
            if await self.get_by_student_no(data["student_no"]):
                raise ConflictException("学号已存在")

        return await self.update(student_id, data)

    async def search_students(
        self,
        keyword: Optional[str] = None,
        grade_id: Optional[UUID] = None,
        class_id: Optional[UUID] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """搜索学生"""
        filters = []

        if keyword:
            filters.append(
                or_(
                    Student.student_no.ilike(f"%{keyword}%"),
                    Student.name.ilike(f"%{keyword}%"),
                    Student.phone.ilike(f"%{keyword}%"),
                )
            )

        if grade_id:
            filters.append(Student.grade_id == grade_id)

        if class_id:
            filters.append(Student.class_id == class_id)

        if status:
            filters.append(Student.status == status)

        filters.append(Student.deleted_at.is_(None))

        return await self.paginate(page, page_size, filters, "created_at", True)

    async def assign_class(self, student_id: UUID, class_id: UUID) -> Student:
        """分配班级"""
        student = await self.get(student_id)
        if not student:
            raise NotFoundException("学生不存在")

        return await self.update(student_id, {"class_id": class_id})

    async def get_student_options(self, grade_id: Optional[UUID] = None, class_id: Optional[UUID] = None) -> List[dict]:
        """获取学生下拉选项"""
        filters = [Student.status == "active", Student.deleted_at.is_(None)]
        if grade_id:
            filters.append(Student.grade_id == grade_id)
        if class_id:
            filters.append(Student.class_id == class_id)

        students = await self.get_all(filters)
        return [
            {"id": str(s.id), "label": s.name, "value": str(s.id)} for s in students
        ]
