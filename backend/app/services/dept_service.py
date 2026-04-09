"""
部门服务
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.department import Department
from app.core.exceptions import NotFoundException, ConflictException
from app.services.base_service import BaseService


class DepartmentService(BaseService[Department]):
    """部门服务"""

    def __init__(self, db: AsyncSession):
        super().__init__(Department, db)

    async def get_by_code(self, code: str) -> Optional[Department]:
        """根据编码获取部门"""
        return await self.get_by_field("code", code)

    async def create_department(self, data: dict) -> Department:
        """创建部门"""
        if data.get("code"):
            if await self.get_by_code(data["code"]):
                raise ConflictException("部门编码已存在")

        if data.get("parent_id"):
            parent = await self.get(data["parent_id"])
            if not parent:
                raise NotFoundException("父级部门不存在")
            data["level"] = parent.level + 1
            data["path"] = f"{parent.path or ''}/{parent.id}"

        return await self.create(data)

    async def update_department(self, dept_id: UUID, data: dict) -> Department:
        """更新部门"""
        dept = await self.get(dept_id)
        if not dept:
            raise NotFoundException("部门不存在")

        if data.get("code") and data["code"] != dept.code:
            if await self.get_by_code(data["code"]):
                raise ConflictException("部门编码已存在")

        return await self.update(dept_id, data)

    async def get_department_tree(self, parent_id: Optional[UUID] = None) -> List[dict]:
        """获取部门树形结构"""
        if parent_id:
            departments = await self.get_all(
                [Department.parent_id == parent_id, Department.status == "active"]
            )
        else:
            departments = await self.get_all(
                [Department.parent_id.is_(None), Department.status == "active"]
            )

        tree = []
        for dept in departments:
            children = await self.get_department_tree(dept.id)
            tree.append(
                {
                    "id": str(dept.id),
                    "label": dept.name,
                    "value": str(dept.id),
                    "code": dept.code,
                    "name": dept.name,
                    "level": dept.level,
                    "sort_order": dept.sort_order,
                    "children": children if children else [],
                }
            )

        return tree

    async def get_all_departments(self) -> List[Department]:
        """获取所有部门"""
        return await self.get_all([Department.status == "active"])

    async def delete_department(self, dept_id: UUID) -> bool:
        """删除部门（检查是否有子部门或用户）"""
        dept = await self.get(dept_id)
        if not dept:
            raise NotFoundException("部门不存在")

        children = await self.get_all([Department.parent_id == dept_id])
        if children:
            raise ConflictException("请先删除子部门")

        return await self.soft_delete(dept_id) is not None
