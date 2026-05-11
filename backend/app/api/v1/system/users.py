"""
用户管理接口
"""

from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.exceptions import NotFoundException, ForbiddenException
from app.models.user import User
from app.models.role import Role, UserRole
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserPasswordReset,
    UserPasswordChange,
)
from app.schemas.response import success, page_response
from app.services.user_service import UserService
from app.services.dept_service import DepartmentService
from app.utils.parsers import parse_uuid

router = APIRouter()


async def _get_user_roles_data(user_id: UUID, db: AsyncSession) -> list:
    """获取用户角色列表（序列化为字典）"""
    result = await db.execute(
        select(Role)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id, Role.status == "active")
        .order_by(Role.level)
    )
    roles = result.scalars().all()
    return [{"id": str(r.id), "code": r.code, "name": r.name} for r in roles]


@router.get("", response_model=dict)
async def get_users(
    keyword: Optional[str] = Query(None, description="关键词"),
    status: Optional[str] = Query(None, description="状态"),
    department_id: Optional[str] = Query(None, description="部门ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取用户列表"""
    user_service = UserService(db)
    result = await user_service.search_users(
        keyword, status, parse_uuid(department_id), page, page_size
    )

    items = []
    for u in result["items"]:
        roles = await _get_user_roles_data(u.id, db)
        items.append(
            {
                "id": str(u.id),
                "username": u.username,
                "email": u.email,
                "phone": u.phone,
                "real_name": u.real_name,
                "avatar": u.avatar,
                "department_id": str(u.department_id) if u.department_id else None,
                "position": u.position,
                "gender": u.gender,
                "status": u.status,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "roles": roles,
            }
        )

    return page_response(items, result["total"], page, page_size)


@router.get("/options", response_model=dict)
async def get_user_options(
    role: Optional[str] = Query(None, description="角色过滤"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取用户下拉选项"""
    user_service = UserService(db)
    options = await user_service.get_user_options(role)
    return success(options)


@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取用户详情"""
    user_service = UserService(db)
    user = await user_service.get(user_id)

    if not user:
        raise NotFoundException("用户不存在")

    roles = await _get_user_roles_data(user_id, db)

    return success(
        {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "real_name": user.real_name,
            "avatar": user.avatar,
            "department_id": str(user.department_id) if user.department_id else None,
            "position": user.position,
            "gender": user.gender,
            "birth_date": user.birth_date.isoformat() if user.birth_date else None,
            "address": user.address,
            "status": user.status,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "roles": roles,
        }
    )


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建用户"""
    user_service = UserService(db)
    user = await user_service.create_user(data)
    roles = await _get_user_roles_data(user.id, db)

    return success(
        {"id": str(user.id), "username": user.username, "roles": roles},
        "用户创建成功",
    )


@router.get("/{user_id}/profile", response_model=dict)
async def get_user_profile(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取用户扩展信息"""
    from app.models.teacher_profile import TeacherProfile

    result = await db.execute(
        select(TeacherProfile).where(TeacherProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        return success(None)

    import json

    profile_data = {}
    try:
        profile_data = json.loads(profile.profile_json) if profile.profile_json else {}
    except Exception:
        pass

    return success(
        {
            "id": str(profile.id),
            "user_id": str(profile.user_id),
            "employee_no": profile.employee_no,
            "hire_date": profile.hire_date.isoformat() if profile.hire_date else None,
            "position": profile.position,
            "title": profile.title,
            "employment_type": profile.employment_type,
            "subject": profile.subject,
            "teaching_grade": profile.teaching_grade,
            "teacher_certificate": profile.teacher_certificate,
            "education": profile.education,
            "degree": profile.degree,
            "emergency_contact": profile.emergency_contact,
            "emergency_phone": profile.emergency_phone,
            "courses": profile_data.get("courses", []),
            "grades": profile_data.get("grades", []),
            "classes": profile_data.get("classes", []),
            "remarks": profile.remarks,
        }
    )


@router.put("/{user_id}", response_model=dict)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新用户"""
    user_service = UserService(db)
    user = await user_service.update_user(user_id, data)
    roles = await _get_user_roles_data(user_id, db)

    return success({"id": str(user.id), "roles": roles}, "用户更新成功")


@router.delete("/{user_id}", response_model=dict)
async def delete_user(
    user_id: UUID,
    hard: bool = Query(False, description="是否硬删除"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除用户"""
    user_service = UserService(db)
    await user_service.delete_user(user_id, hard)

    return success(message="用户删除成功")


@router.put("/{user_id}/reset-password", response_model=dict)
async def reset_password(
    user_id: UUID,
    data: UserPasswordReset,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """重置密码（管理员操作）"""
    user_service = UserService(db)
    await user_service.reset_password(user_id, data.password)

    return success(message="密码重置成功")


@router.put("/{user_id}/status", response_model=dict)
async def update_user_status(
    user_id: UUID,
    status: str = Query(..., description="状态: active/inactive/suspended"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新用户状态"""
    user_service = UserService(db)
    await user_service.update_status(user_id, status)

    return success(message="状态更新成功")


class RoleAssignRequest(BaseModel):
    role_ids: List[UUID]


@router.get("/{user_id}/roles", response_model=dict)
async def get_user_roles(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取用户角色列表"""
    roles = await _get_user_roles_data(user_id, db)
    return success(roles)


@router.put("/{user_id}/roles", response_model=dict)
async def assign_user_roles(
    user_id: UUID,
    data: RoleAssignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """分配用户角色"""
    user_service = UserService(db)
    user = await user_service.get(user_id)
    if not user:
        raise NotFoundException("用户不存在")

    await user_service.assign_roles(user_id, data.role_ids)
    roles = await _get_user_roles_data(user_id, db)
    return success(roles, "角色分配成功")


@router.put("/change-password", response_model=dict)
async def change_password(
    data: UserPasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """修改密码"""
    user_service = UserService(db)
    await user_service.change_password(
        current_user.id, data.old_password, data.new_password
    )

    return success(message="密码修改成功")
