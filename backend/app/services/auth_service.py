from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.exceptions import UnauthorizedException


class AuthService:
    @staticmethod
    async def authenticate(
        db: AsyncSession, username: str, password: str
    ) -> Optional[User]:
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash):
            return None

        if user.status != "active":
            raise UnauthorizedException("账号已被禁用")

        return user

    @staticmethod
    async def login(db: AsyncSession, username: str, password: str) -> dict:
        user = await AuthService.authenticate(db, username, password)

        if not user:
            raise UnauthorizedException("用户名或密码错误")

        access_token = create_access_token(
            {"sub": str(user.id), "username": user.username}
        )
        refresh_token = create_refresh_token({"sub": str(user.id)})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 1440,
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "real_name": user.real_name,
                "avatar": user.avatar,
                "status": user.status,
            },
        }

    @staticmethod
    async def refresh_token(refresh_token: str) -> dict:
        payload = decode_token(refresh_token)

        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedException("无效的刷新令牌")

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("令牌信息无效")

        access_token = create_access_token({"sub": user_id})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 1440,
        }
