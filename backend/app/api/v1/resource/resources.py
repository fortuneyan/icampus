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
from app.schemas.resource import ResourceCreate, ResourceUpdate, CategoryCreate
from app.schemas.response import success, page_response
from app.services.resource_service import ResourceService, CategoryService

router = APIRouter()


@router.get("/resources", response_model=dict)
async def get_resources(
    keyword: Optional[str] = Query(None),
    category_id: Optional[UUID] = Query(None),
    resource_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ResourceService(db)
    result = await service.search_resources(
        keyword, category_id, resource_type, page, page_size
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
    parent_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CategoryService(db)
    tree = await service.get_category_tree(parent_id)
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
