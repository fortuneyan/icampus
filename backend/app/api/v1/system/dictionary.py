"""
数据字典管理接口
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
from app.models.dictionary import DictionaryType, DictionaryItem
from app.schemas.response import success, page_response
from app.services.dictionary_service import DictionaryTypeService, DictionaryItemService

router = APIRouter()


# ==================== 字典类型 ====================

class DictTypeCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    status: str = "active"


class DictTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


@router.get("/dict-types", response_model=dict)
async def get_dict_types(
    keyword: Optional[str] = Query(None, description="关键词"),
    status: Optional[str] = Query(None, description="状态"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取字典类型列表"""
    service = DictionaryTypeService(db)
    
    filters = []
    if keyword:
        filters.append(DictionaryType.name.ilike(f"%{keyword}%"))
    if status:
        filters.append(DictionaryType.status == status)
    
    result = await service.paginate(page, page_size, filters)
    
    items = [
        {
            "id": str(d.id),
            "name": d.name,
            "code": d.code,
            "description": d.description,
            "status": d.status,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in result["items"]
    ]
    
    return page_response(items, result["total"], page, page_size)


@router.get("/dict-types/{type_id}", response_model=dict)
async def get_dict_type(
    type_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取字典类型详情"""
    service = DictionaryTypeService(db)
    dict_type = await service.get(type_id)
    
    if not dict_type:
        raise NotFoundException("字典类型不存在")
    
    return success({
        "id": str(dict_type.id),
        "name": dict_type.name,
        "code": dict_type.code,
        "description": dict_type.description,
        "status": dict_type.status,
    })


@router.post("/dict-types", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_dict_type(
    data: DictTypeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建字典类型"""
    service = DictionaryTypeService(db)
    
    # 检查编码是否已存在
    existing = await service.get_by_code(data.code)
    if existing:
        raise NotFoundException("字典编码已存在")
    
    dict_type = await service.create(data.model_dump())
    return success({"id": str(dict_type.id)}, "字典类型创建成功")


@router.put("/dict-types/{type_id}", response_model=dict)
async def update_dict_type(
    type_id: UUID,
    data: DictTypeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新字典类型"""
    service = DictionaryTypeService(db)
    dict_type = await service.update(type_id, data.model_dump(exclude_unset=True))
    
    if not dict_type:
        raise NotFoundException("字典类型不存在")
    
    return success({"id": str(dict_type.id)}, "字典类型更新成功")


@router.delete("/dict-types/{type_id}", response_model=dict)
async def delete_dict_type(
    type_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除字典类型"""
    service = DictionaryTypeService(db)
    await service.delete(type_id)
    return success(message="字典类型删除成功")


# ==================== 字典项 ====================

class DictItemCreate(BaseModel):
    type_id: UUID
    label: str
    value: str
    sort_order: int = 0
    status: str = "active"
    remark: Optional[str] = None


class DictItemUpdate(BaseModel):
    label: Optional[str] = None
    value: Optional[str] = None
    sort_order: Optional[int] = None
    status: Optional[str] = None
    remark: Optional[str] = None


@router.get("/dict-items", response_model=dict)
async def get_dict_items(
    type_id: Optional[UUID] = Query(None, description="字典类型ID"),
    type_code: Optional[str] = Query(None, description="字典类型编码"),
    status: Optional[str] = Query(None, description="状态"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取字典项列表"""
    service = DictionaryItemService(db)
    
    if type_code:
        # 根据类型编码获取
        items = await service.get_by_type_code(type_code, status)
        return success(items)
    
    if not type_id:
        return success([])
    
    items = await service.get_by_type(type_id, status)
    result = [
        {
            "id": str(item.id),
            "type_id": str(item.type_id),
            "label": item.label,
            "value": item.value,
            "sort_order": item.sort_order,
            "status": item.status,
            "remark": item.remark,
        }
        for item in items
    ]
    
    return success(result)


@router.post("/dict-items", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_dict_item(
    data: DictItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建字典项"""
    service = DictionaryItemService(db)
    item = await service.create(data.model_dump())
    return success({"id": str(item.id)}, "字典项创建成功")


@router.put("/dict-items/{item_id}", response_model=dict)
async def update_dict_item(
    item_id: UUID,
    data: DictItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新字典项"""
    service = DictionaryItemService(db)
    item = await service.update(item_id, data.model_dump(exclude_unset=True))
    
    if not item:
        raise NotFoundException("字典项不存在")
    
    return success({"id": str(item.id)}, "字典项更新成功")


@router.delete("/dict-items/{item_id}", response_model=dict)
async def delete_dict_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除字典项"""
    service = DictionaryItemService(db)
    await service.delete(item_id)
    return success(message="字典项删除成功")


@router.get("/dict-items/by-code/{type_code}", response_model=dict)
async def get_dict_items_by_code(
    type_code: str,
    status: Optional[str] = Query("active", description="状态"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """根据字典编码获取字典项（用于前端下拉选项）"""
    service = DictionaryItemService(db)
    items = await service.get_by_type_code(type_code, status)
    return success(items)
