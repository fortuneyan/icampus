"""
用户服务
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.department import Department
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import NotFoundException, ConflictException
from app.schemas.user import UserCreate, UserUpdate
from app.services.base_service import BaseService


class UserService(BaseService[User]):
    """用户服务"""

    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return await self.get_by_field("username", username)

    async def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return await self.get_by_field("email", email)

    async def get_by_phone(self, phone: str) -> Optional[User]:
        """根据手机号获取用户"""
        return await self.get_by_field("phone", phone)

    async def create_user(self, data: UserCreate) -> User:
        """创建用户"""
        if await self.get_by_username(data.username):
            raise ConflictException("用户名已存在")
        if data.email and await self.get_by_email(data.email):
            raise ConflictException("邮箱已被使用")
        if data.phone and await self.get_by_phone(data.phone):
            raise ConflictException("手机号已被使用")

        user_data = data.model_dump()
        user_data["password_hash"] = get_password_hash(user_data.pop("password"))
        return await self.create(user_data)

    async def update_user(self, user_id: UUID, data: UserUpdate) -> User:
        """更新用户"""
        user = await self.get(user_id)
        if not user:
            raise NotFoundException("用户不存在")

        update_data = data.model_dump(exclude_unset=True)

        if data.email and data.email != user.email:
            if await self.get_by_email(data.email):
                raise ConflictException("邮箱已被使用")

        if data.phone and data.phone != user.phone:
            if await self.get_by_phone(data.phone):
                raise ConflictException("手机号已被使用")

        return await self.update(user_id, update_data)

    async def reset_password(self, user_id: UUID, new_password: str) -> User:
        """重置密码"""
        user = await self.get(user_id)
        if not user:
            raise NotFoundException("用户不存在")

        user.password_hash = get_password_hash(new_password)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def change_password(
        self, user_id: UUID, old_password: str, new_password: str
    ) -> User:
        """修改密码"""
        user = await self.get(user_id)
        if not user:
            raise NotFoundException("用户不存在")

        if not verify_password(old_password, user.password_hash):
            raise ConflictException("原密码错误")

        user.password_hash = get_password_hash(new_password)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_status(self, user_id: UUID, status: str) -> User:
        """更新用户状态"""
        user = await self.get(user_id)
        if not user:
            raise NotFoundException("用户不存在")

        return await self.update(user_id, {"status": status})

    async def search_users(
        self,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        department_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """搜索用户"""
        filters = []

        if keyword:
            filters.append(
                or_(
                    User.username.ilike(f"%{keyword}%"),
                    User.real_name.ilike(f"%{keyword}%"),
                    User.email.ilike(f"%{keyword}%"),
                    User.phone.ilike(f"%{keyword}%"),
                )
            )

        if status:
            filters.append(User.status == status)

        if department_id:
            filters.append(User.department_id == department_id)

        filters.append(User.deleted_at.is_(None))

        return await self.paginate(page, page_size, filters, "created_at", True)

    async def get_user_options(self, role: Optional[str] = None) -> List[dict]:
        """获取用户下拉选项"""
        filters = [User.status == "active", User.deleted_at.is_(None)]
        if role:
            from app.models.role import Role
            from sqlalchemy import select

            result = await self.db.execute(
                select(User).where(User.status == "active", User.deleted_at.is_(None))
            )
            users = result.scalars().all()
        else:
            users = await self.get_all(filters)
        return [{"value": str(u.id), "label": u.real_name or u.username} for u in users]

    async def delete_user(self, user_id: UUID, hard: bool = False) -> bool:
        """删除用户"""
        user = await self.get(user_id)
        if not user:
            raise NotFoundException("用户不存在")

        if hard:
            return await self.delete(user_id)
        else:
            return await self.soft_delete(user_id) is not None
