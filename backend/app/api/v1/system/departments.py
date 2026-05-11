"""
部门管理接口
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.schemas.response import success
from app.services.dept_service import DepartmentService
from app.utils.parsers import parse_uuid

router = APIRouter()


@router.get("", response_model=dict)
async def get_departments(
    parent_id: Optional[str] = Query(None, description="父级部门ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取部门树形列表"""
    dept_service = DepartmentService(db)
    tree = await dept_service.get_department_tree(parse_uuid(parent_id))

    return success(tree)


@router.get("/all", response_model=dict)
async def get_all_departments(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """获取所有部门"""
    dept_service = DepartmentService(db)
    departments = await dept_service.get_all_departments()

    items = [
        {
            "id": str(d.id),
            "name": d.name,
            "code": d.code,
            "parent_id": str(d.parent_id) if d.parent_id else None,
            "level": d.level,
            "sort_order": d.sort_order,
            "status": d.status,
        }
        for d in departments
    ]

    return success(items)


# ⚠️ 注意：/options 必须在 /{dept_id} 之前定义，避免 "options" 被当作 dept_id
@router.get("/options", response_model=dict)
async def get_department_options(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取部门下拉选项（用于工作流等场景）"""
    from sqlalchemy import select
    from app.models.department import Department

    stmt = select(Department).where(
        Department.is_deleted == False
    ).order_by(Department.sort_order, Department.name)
    result = await db.execute(stmt)
    depts = result.scalars().all()

    def build_tree(dept, dept_list):
        item = {"id": str(dept.id), "name": dept.name}
        children = [d for d in dept_list if d.parent_id == dept.id]
        if children:
            item["children"] = [build_tree(c, dept_list) for c in children]
        return item

    root_depts = [d for d in depts if d.parent_id is None]
    tree = [build_tree(d, depts) for d in root_depts]

    return success(tree)


@router.get("/{dept_id}", response_model=dict)
async def get_department(
    dept_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取部门详情"""
    dept_service = DepartmentService(db)
    dept = await dept_service.get(dept_id)

    if not dept:
        raise NotFoundException("部门不存在")

    return success(
        {
            "id": str(dept.id),
            "name": dept.name,
            "code": dept.code,
            "parent_id": str(dept.parent_id) if dept.parent_id else None,
            "level": dept.level,
            "sort_order": dept.sort_order,
            "leader_id": str(dept.leader_id) if dept.leader_id else None,
            "phone": dept.phone,
            "email": dept.email,
            "status": dept.status,
            "description": dept.description,
        }
    )


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_department(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建部门"""
    dept_service = DepartmentService(db)
    dept = await dept_service.create_department(data)

    return success({"id": str(dept.id), "name": dept.name}, "部门创建成功")


@router.put("/{dept_id}", response_model=dict)
async def update_department(
    dept_id: UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新部门"""
    dept_service = DepartmentService(db)
    dept = await dept_service.update_department(dept_id, data)

    return success({"id": str(dept.id)}, "部门更新成功")


@router.delete("/{dept_id}", response_model=dict)
async def delete_department(
    dept_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除部门"""
    dept_service = DepartmentService(db)
    await dept_service.delete_department(dept_id)

    return success(message="部门删除成功")
