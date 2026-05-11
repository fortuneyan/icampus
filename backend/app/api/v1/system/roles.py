"""
角色和权限管理接口
"""

from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.models.role import Role, Permission, Menu
from app.schemas.response import success, page_response
from app.services.role_service import RoleService, PermissionService
from app.services.menu_service import MenuService
from app.utils.parsers import parse_uuid

router = APIRouter()


class RoleCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    level: int = 1
    data_scope: str = "all"
    status: str = "active"


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    level: Optional[int] = None
    data_scope: Optional[str] = None
    status: Optional[str] = None


class PermissionCreate(BaseModel):
    code: str
    name: str
    resource: str
    action: str
    description: Optional[str] = None
    parent_id: Optional[UUID] = None


class MenuCreate(BaseModel):
    name: str
    title: str
    parent_id: Optional[UUID] = None
    icon: Optional[str] = None
    path: Optional[str] = None
    component: Optional[str] = None
    sort_order: int = 0
    visible: bool = True
    enabled: bool = True
    keep_alive: bool = True
    permission_code: Optional[str] = None


@router.get("/roles", response_model=dict)
async def get_roles(
    keyword: Optional[str] = Query(None, description="关键词"),
    status: Optional[str] = Query(None, description="状态"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取角色列表"""
    role_service = RoleService(db)

    filters = []
    if keyword:
        filters.append(Role.name.ilike(f"%{keyword}%"))
    if status:
        filters.append(Role.status == status)

    result = await role_service.paginate(page, page_size, filters)

    items = [
        {
            "id": str(r.id),
            "code": r.code,
            "name": r.name,
            "description": r.description,
            "level": r.level,
            "data_scope": r.data_scope,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in result["items"]
    ]

    return page_response(items, result["total"], page, page_size)


# ⚠️ 注意：/roles/options 必须在 /roles/{role_id} 之前定义
# FastAPI 按定义顺序匹配路由，/{role_id} 会匹配所有 /roles/* 的请求
@router.get("/roles/options", response_model=dict)
async def get_role_options(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取角色下拉选项（用于工作流等场景）"""
    from sqlalchemy import select
    from app.models.role import Role

    stmt = select(Role).where(Role.status == "active").order_by(Role.level, Role.name)
    result = await db.execute(stmt)
    roles = result.scalars().all()

    options = [
        {"id": str(r.id), "code": r.code, "name": r.name}
        for r in roles
    ]
    return success(options)


@router.get("/roles/{role_id}", response_model=dict)
async def get_role(
    role_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取角色详情"""
    role_service = RoleService(db)
    role = await role_service.get(role_id)

    if not role:
        raise NotFoundException("角色不存在")

    return success(
        {
            "id": str(role.id),
            "code": role.code,
            "name": role.name,
            "description": role.description,
            "level": role.level,
            "data_scope": role.data_scope,
            "status": role.status,
            "created_at": role.created_at.isoformat() if role.created_at else None,
        }
    )


@router.post("/roles", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_role(
    data: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建角色"""
    role_service = RoleService(db)
    role = await role_service.create_role(data.model_dump())

    return success({"id": str(role.id)}, "角色创建成功")


@router.put("/roles/{role_id}", response_model=dict)
async def update_role(
    role_id: UUID,
    data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新角色"""
    role_service = RoleService(db)
    role = await role_service.update_role(role_id, data.model_dump(exclude_unset=True))

    return success({"id": str(role.id)}, "角色更新成功")


@router.delete("/roles/{role_id}", response_model=dict)
async def delete_role(
    role_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除角色"""
    role_service = RoleService(db)
    await role_service.delete_role(role_id)

    return success(message="角色删除成功")


# ============================================================
# 权限和菜单接口
# ============================================================

@router.get("/permissions", response_model=dict)
async def get_permissions(
    parent_id: Optional[str] = Query(None, description="父级权限ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取权限树"""
    perm_service = PermissionService(db)
    tree = await perm_service.get_permission_tree(parse_uuid(parent_id))

    return success(tree)


@router.get("/menus", response_model=dict)
async def get_menus(
    parent_id: Optional[str] = Query(None, description="父级菜单ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取菜单树"""
    menu_service = MenuService(db)
    tree = await menu_service.get_menu_tree(parse_uuid(parent_id))

    return success(tree)


@router.get("/menus/user", response_model=dict)
async def get_user_menus(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """获取当前用户菜单"""
    menu_service = MenuService(db)
    menus = await menu_service.get_user_menus(current_user.id)

    return success(menus)


@router.post("/menus", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_menu(
    data: MenuCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建菜单"""
    menu_service = MenuService(db)
    menu = await menu_service.create_menu(data.model_dump())

    return success({"id": str(menu.id)}, "菜单创建成功")


@router.put("/menus/{menu_id}", response_model=dict)
async def update_menu(
    menu_id: UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新菜单"""
    menu_service = MenuService(db)
    menu = await menu_service.update_menu(menu_id, data)

    return success({"id": str(menu.id)}, "菜单更新成功")


@router.delete("/menus/{menu_id}", response_model=dict)
async def delete_menu(
    menu_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除菜单"""
    menu_service = MenuService(db)
    await menu_service.delete_menu(menu_id)

    return success(message="菜单删除成功")
