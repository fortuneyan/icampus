"""
学生服务
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
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
        """搜索学生

        按班级查时忽略年级参数（班级查包含该班所有学生，含留级生）
        按年级查时只查该年级学生
        """
        filters = []

        if keyword:
            filters.append(
                or_(
                    Student.student_no.ilike(f"%{keyword}%"),
                    Student.name.ilike(f"%{keyword}%"),
                    Student.phone.ilike(f"%{keyword}%"),
                )
            )

        if class_id:
            filters.append(Student.class_id == class_id)
        elif grade_id:
            filters.append(Student.grade_id == grade_id)

        if status:
            filters.append(Student.status == status)

        filters.append(Student.deleted_at.is_(None))

        return await self.paginate(page, page_size, filters, "created_at", True)

    async def assign_class(self, student_id: UUID, class_id: UUID, operator_id: UUID = None, reason: str = None) -> Student:
        """分配班级，记录变动历史"""
        from app.models.student import StudentClassHistory

        student = await self.get(student_id)
        if not student:
            raise NotFoundException("学生不存在")

        if student.class_id:
            old_class_id = student.class_id
            history_end = StudentClassHistory(
                student_id=student.id,
                class_id=old_class_id,
                end_date=datetime.now(),
                reason=reason or "班级调整",
                operator_id=operator_id,
            )
            self.db.add(history_end)

        if class_id:
            history_start = StudentClassHistory(
                student_id=student.id,
                class_id=class_id,
                start_date=datetime.now(),
                reason=reason or "班级分配",
                operator_id=operator_id,
            )
            self.db.add(history_start)

        await self.db.commit()
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
