from datetime import datetime
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.exceptions import UnauthorizedException
from app.schemas.auth import LoginRequest, LoginResponse, UserInfo, RefreshTokenRequest
from app.schemas.response import success
from app.services.auth_service import AuthService
from app.models.user import User

router = APIRouter()


@router.post("/login", response_model=dict)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    result = await AuthService.login(db, request.username, request.password)
    return success(result, "登录成功")


@router.post("/refresh", response_model=dict)
async def refresh_token(request: RefreshTokenRequest):
    """刷新令牌"""
    result = await AuthService.refresh_token(request.refresh_token)
    return success(result, "令牌刷新成功")


@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return success(
        {
            "id": str(current_user.id),
            "username": current_user.username,
            "email": current_user.email,
            "real_name": current_user.real_name,
            "avatar": current_user.avatar,
            "status": current_user.status,
        }
    )


@router.post("/logout", response_model=dict)
async def logout(current_user: User = Depends(get_current_user)):
    """用户登出"""
    return success(message="登出成功")
