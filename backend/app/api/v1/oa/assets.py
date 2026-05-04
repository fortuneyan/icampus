"""
资产管理API
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.oa.asset import (
    AssetCategoryCreate,
    AssetCategoryUpdate,
    AssetCreate,
    AssetUpdate,
    AssetOperationCreate as BorrowCreate,
)
from app.schemas.response import success, page_response
from app.services.oa.asset_svc import AssetCategoryService, AssetService, BorrowRecordService

router = APIRouter()


# ============ 资产分类 ============

@router.get("/categories", response_model=dict)
async def get_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取资产分类树"""
    service = AssetCategoryService(db)
    tree = await service.get_category_tree()
    return success(tree)


@router.post("/categories", response_model=dict)
async def create_category(
    data: AssetCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加分类"""
    service = AssetCategoryService(db)
    category = await service.create_category(data.model_dump())
    return success({"id": str(category.id)}, "分类添加成功")


@router.put("/categories/{category_id}", response_model=dict)
async def update_category(
    category_id: UUID,
    data: AssetCategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新分类"""
    service = AssetCategoryService(db)
    category = await service.update_category(category_id, data.model_dump(exclude_unset=True))
    return success({"id": str(category.id)}, "分类更新成功")


@router.delete("/categories/{category_id}", response_model=dict)
async def delete_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除分类"""
    service = AssetCategoryService(db)
    await service.delete_category(category_id)
    return success(message="分类删除成功")


# ============ 资产管理 ============

@router.get("", response_model=dict)
async def get_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取资产列表"""
    service = AssetService(db)
    result = await service.get_asset_list(
        page=page,
        page_size=page_size,
        category_id=UUID(category_id) if category_id else None,
        status=status,
        keyword=keyword,
    )
    return page_response(result["items"], result["total"], page, page_size)


@router.get("/{asset_id}", response_model=dict)
async def get_asset_detail(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取资产详情"""
    service = AssetService(db)
    asset = await service.get_asset_detail(asset_id)
    return success(asset)


@router.post("", response_model=dict)
async def create_asset(
    data: AssetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加资产"""
    service = AssetService(db)
    asset = await service.create_asset(data.model_dump())
    return success({"id": str(asset.id)}, "资产添加成功")


@router.put("/{asset_id}", response_model=dict)
async def update_asset(
    asset_id: UUID,
    data: AssetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """编辑资产"""
    service = AssetService(db)
    asset = await service.update_asset(asset_id, data.model_dump(exclude_unset=True))
    return success({"id": str(asset.id)}, "资产更新成功")


@router.delete("/{asset_id}", response_model=dict)
async def delete_asset(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除资产"""
    service = AssetService(db)
    await service.delete_asset(asset_id)
    return success(message="资产删除成功")


@router.post("/{asset_id}/transfer", response_model=dict)
async def transfer_asset(
    asset_id: UUID,
    target_org_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """资产调拨"""
    service = AssetService(db)
    asset = await service.transfer_asset(asset_id, UUID(target_org_id), current_user.id)
    return success({"id": str(asset.id)}, "资产调拨成功")


# ============ 借用管理 ============

@router.post("/{asset_id}/borrow", response_model=dict)
async def borrow_asset(
    asset_id: UUID,
    data: BorrowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发起借用申请"""
    service = BorrowRecordService(db)
    record = await service.create_borrow(
        asset_id=asset_id,
        data=data.model_dump(),
        borrower_id=current_user.id,
    )
    return success({"id": str(record.id)}, "借用申请已提交")


@router.get("/borrow-records", response_model=dict)
async def get_borrow_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    asset_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取借用记录"""
    service = BorrowRecordService(db)
    result = await service.get_borrow_list(
        page=page,
        page_size=page_size,
        status=status,
        asset_id=UUID(asset_id) if asset_id else None,
    )
    return page_response(result["items"], result["total"], page, page_size)


@router.get("/borrow-records/{record_id}", response_model=dict)
async def get_borrow_record_detail(
    record_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取借用记录详情"""
    service = BorrowRecordService(db)
    record = await service.get_borrow_detail(record_id)
    return success(record)


@router.post("/borrow-records/{record_id}/return", response_model=dict)
async def return_asset(
    record_id: UUID,
    condition: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """归还资产"""
    service = BorrowRecordService(db)
    record = await service.return_asset(record_id, condition, current_user.id)
    return success({"id": str(record.id)}, "资产归还成功")


# ============ 我的资产 ============

@router.get("/my/assets", response_model=dict)
async def get_my_assets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我的借用资产"""
    service = BorrowRecordService(db)
    assets = await service.get_my_borrows(current_user.id)
    return success(assets)


@router.get("/my/assets/overdue", response_model=dict)
async def get_overdue_assets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取超期资产"""
    service = BorrowRecordService(db)
    assets = await service.get_overdue_borrows(current_user.id)
    return success(assets)