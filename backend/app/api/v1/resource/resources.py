"""
资源管理接口
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.models.resource import ResourceCategory
from app.schemas.resource import ResourceCreate, ResourceUpdate, CategoryCreate
from app.schemas.response import success, page_response
from app.services.resource_service import ResourceService, CategoryService

router = APIRouter()


def _parse_uuid(value: Optional[str]) -> Optional[UUID]:
    """安全解析UUID参数，空字符串返回None"""
    if not value:
        return None
    try:
        return UUID(value)
    except (ValueError, AttributeError):
        return None


@router.get("/resources", response_model=dict)
async def get_resources(
    keyword: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None, description="分类ID"),
    resource_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    parsed_category_id = _parse_uuid(category_id)
    service = ResourceService(db)
    result = await service.search_resources(
        keyword, parsed_category_id, resource_type, page, page_size
    )
    items = [
        {
            "id": str(r.id),
            "title": r.title,
            "resource_type": r.resource_type,
            "view_count": r.view_count,
            "like_count": r.like_count,
            "created_at": r.created_at.isoformat(),
        }
        for r in result["items"]
    ]
    return page_response(items, result["total"], page, page_size)


@router.get("/resources/{id}", response_model=dict)
async def get_resource(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ResourceService(db)
    resource = await service.get(id)
    if not resource:
        raise NotFoundException("资源不存在")
    await service.update_view_count(id)
    return success(
        {
            "id": str(resource.id),
            "title": resource.title,
            "description": resource.description,
            "resource_type": resource.resource_type,
            "file_url": resource.file_url,
            "view_count": resource.view_count,
        }
    )


@router.post("/resources", response_model=dict)
async def create_resource(
    data: ResourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ResourceService(db)
    resource = await service.create_resource(data.model_dump(), current_user.id)
    return success({"id": str(resource.id)}, "创建成功")


@router.put("/resources/{id}", response_model=dict)
async def update_resource(
    id: UUID,
    data: ResourceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ResourceService(db)
    resource = await service.update(id, data.model_dump(exclude_unset=True))
    return success({"id": str(resource.id)}, "更新成功")


@router.delete("/resources/{id}", response_model=dict)
async def delete_resource(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ResourceService(db)
    await service.soft_delete(id)
    return success(message="删除成功")


@router.get("/categories", response_model=dict)
async def get_categories(
    parent_id: Optional[str] = Query(None, description="父分类ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    parsed_parent_id = _parse_uuid(parent_id)
    service = CategoryService(db)
    tree = await service.get_category_tree(parsed_parent_id)
    return success(tree)


@router.post("/categories", response_model=dict)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CategoryService(db)
    category = await service.create(data.model_dump())
    return success({"id": str(category.id)}, "创建成功")


@router.get("/categories/options", response_model=dict)
async def get_category_options(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取分类下拉选项（扁平列表）"""
    from sqlalchemy import select
    result = await db.execute(
        select(ResourceCategory)
        .where(ResourceCategory.status == "active")
        .order_by(ResourceCategory.sort_order)
    )
    categories = result.scalars().all()
    options = [
        {"id": str(c.id), "label": c.name, "value": str(c.id)}
        for c in categories
    ]
    return success(options)
