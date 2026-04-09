"""
角色服务
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import ARRAY

from app.models.role import Role, Permission
from app.models.user import User
from app.core.exceptions import NotFoundException, ConflictException
from app.services.base_service import BaseService


class RoleService(BaseService[Role]):
    """角色服务"""

    def __init__(self, db: AsyncSession):
        super().__init__(Role, db)

    async def get_by_code(self, code: str) -> Optional[Role]:
        """根据编码获取角色"""
        return await self.get_by_field("code", code)

    async def create_role(self, data: dict) -> Role:
        """创建角色"""
        if await self.get_by_code(data["code"]):
            raise ConflictException("角色编码已存在")

        return await self.create(data)

    async def update_role(self, role_id: UUID, data: dict) -> Role:
        """更新角色"""
        role = await self.get(role_id)
        if not role:
            raise NotFoundException("角色不存在")

        if data.get("code") and data["code"] != role.code:
            if await self.get_by_code(data["code"]):
                raise ConflictException("角色编码已存在")

        return await self.update(role_id, data)

    async def delete_role(self, role_id: UUID) -> bool:
        """删除角色"""
        role = await self.get(role_id)
        if not role:
            raise NotFoundException("角色不存在")

        result = await self.db.execute(select(User).where(User.id.in_(select(User.id))))

        return await self.soft_delete(role_id) is not None

    async def assign_permissions(
        self, role_id: UUID, permission_ids: List[UUID]
    ) -> Role:
        """分配权限"""
        role = await self.get(role_id)
        if not role:
            raise NotFoundException("角色不存在")

        permissions = await self.db.execute(
            select(Permission).where(Permission.id.in_(permission_ids))
        )

        return role


class PermissionService(BaseService[Permission]):
    """权限服务"""

    def __init__(self, db: AsyncSession):
        super().__init__(Permission, db)

    async def get_by_code(self, code: str) -> Optional[Permission]:
        """根据编码获取权限"""
        return await self.get_by_field("code", code)

    async def get_permission_tree(self, parent_id: Optional[UUID] = None) -> List[dict]:
        """获取权限树形结构"""
        if parent_id:
            permissions = await self.get_all([Permission.parent_id == parent_id])
        else:
            permissions = await self.get_all([Permission.parent_id.is_(None)])

        tree = []
        for perm in permissions:
            children = await self.get_permission_tree(perm.id)
            tree.append(
                {
                    "id": str(perm.id),
                    "label": perm.name,
                    "value": str(perm.id),
                    "code": perm.code,
                    "resource": perm.resource,
                    "action": perm.action,
                    "children": children if children else [],
                }
            )

        return tree

    async def get_all_permissions(self) -> List[Permission]:
        """获取所有权限"""
        return await self.get_all()
