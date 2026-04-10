"""
Auth service - Full debug version
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
)
from app.core.exceptions import UnauthorizedException
import bcrypt


class AuthService:
    @staticmethod
    async def authenticate(
        db: AsyncSession, username: str, password: str
    ) -> Optional[User]:
        print(f"=== AUTHENTICATE CALLED ===")
        print(f"Username: {username}")

        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if not user:
            print("User not found in DB")
            return None

        print(f"User found: {user.username}")
        print(f"User status: {user.status}")
        print(f"Password hash: {user.password_hash[:30]}...")

        # Verify password with bcrypt directly
        pwd_bytes = password.encode("utf-8")
        hash_bytes = user.password_hash.encode("utf-8")

        try:
            bcrypt_result = bcrypt.checkpw(pwd_bytes, hash_bytes)
            print(f"Direct bcrypt result: {bcrypt_result}")
        except Exception as e:
            print(f"BCrypt error: {e}")
            bcrypt_result = False

        # Use function
        func_result = verify_password(password, user.password_hash)
        print(f"Function verify_password result: {func_result}")

        if not func_result:
            print("Password verification FAILED")
            return None

        if user.status != "active":
            print(f"User status is: {user.status} - not active!")
            raise UnauthorizedException("账号已被禁用")

        print("=== AUTHENTICATE SUCCESS ===")
        return user

    @staticmethod
    async def login(db: AsyncSession, username: str, password: str) -> dict:
        print(f"=== LOGIN CALLED ===")
        user = await AuthService.authenticate(db, username, password)

        print(f"User after authenticate: {user}")

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
