"""
资产操作记录API
路径: /oa/asset-operations/*
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.response import success, page_response
from app.services.oa.asset_svc import BorrowRecordService

router = APIRouter()


@router.get("", response_model=dict)
async def get_operations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    asset_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取操作记录列表"""
    service = BorrowRecordService(db)
    result = await service.get_borrow_list(
        page=page,
        page_size=page_size,
        status=status,
        asset_id=UUID(asset_id) if asset_id else None,
    )
    return page_response(result["items"], result["total"], page, page_size)


@router.get("/{operation_id}", response_model=dict)
async def get_operation_detail(
    operation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取操作记录详情"""
    service = BorrowRecordService(db)
    record = await service.get_borrow_detail(operation_id)
    return success(record)
