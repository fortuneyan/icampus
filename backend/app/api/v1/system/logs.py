"""
日志审计接口
"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.operation_log import OperationLog
from app.models.login_log import LoginLog
from app.models.data_access_log import DataAccessLog
from app.schemas.response import success, page_response

router = APIRouter()


@router.get("/operation", response_model=dict)
async def get_operation_logs(
    user_id: Optional[UUID] = Query(None),
    module: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取操作日志"""
    query = select(OperationLog).order_by(desc(OperationLog.created_at))

    if user_id:
        query = query.where(OperationLog.user_id == user_id)
    if module:
        query = query.where(OperationLog.module == module)
    if action:
        query = query.where(OperationLog.action == action)
    if start_date:
        try:
            start = datetime.fromisoformat(start_date)
            query = query.where(OperationLog.created_at >= start)
        except:
            pass
    if end_date:
        try:
            end = datetime.fromisoformat(end_date)
            query = query.where(OperationLog.created_at <= end)
        except:
            pass

    total_result = await db.execute(query)
    total = len(total_result.scalars().all())

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()

    items = [
        {
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "username": log.username,
            "module": log.module,
            "action": log.action,
            "operation": log.operation,
            "method": log.method,
            "path": log.path,
            "ip_address": log.ip_address,
            "status_code": log.status_code,
            "response_time": log.response_time,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]

    return page_response(items, total, page, page_size)


@router.get("/login", response_model=dict)
async def get_login_logs(
    user_id: Optional[UUID] = Query(None),
    username: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取登录日志"""
    query = select(LoginLog).order_by(desc(LoginLog.created_at))

    if user_id:
        query = query.where(LoginLog.user_id == user_id)
    if username:
        query = query.where(LoginLog.username.contains(username))
    if status:
        query = query.where(LoginLog.status == status)
    if start_date:
        try:
            start = datetime.fromisoformat(start_date)
            query = query.where(LoginLog.created_at >= start)
        except:
            pass
    if end_date:
        try:
            end = datetime.fromisoformat(end_date)
            query = query.where(LoginLog.created_at <= end)
        except:
            pass

    total_result = await db.execute(query)
    total = len(total_result.scalars().all())

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()

    items = [
        {
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "username": log.username,
            "login_type": log.login_type,
            "ip_address": log.ip_address,
            "ip_location": log.ip_location,
            "device": log.device,
            "browser": log.browser,
            "status": log.status,
            "fail_reason": log.fail_reason,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]

    return page_response(items, total, page, page_size)


@router.get("/access", response_model=dict)
async def get_data_access_logs(
    user_id: Optional[UUID] = Query(None),
    data_level: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    operation: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取数据访问日志"""
    query = select(DataAccessLog).order_by(desc(DataAccessLog.created_at))

    if user_id:
        query = query.where(DataAccessLog.user_id == user_id)
    if data_level:
        query = query.where(DataAccessLog.data_level == data_level)
    if resource_type:
        query = query.where(DataAccessLog.resource_type == resource_type)
    if operation:
        query = query.where(DataAccessLog.operation == operation)
    if start_date:
        try:
            start = datetime.fromisoformat(start_date)
            query = query.where(DataAccessLog.created_at >= start)
        except:
            pass
    if end_date:
        try:
            end = datetime.fromisoformat(end_date)
            query = query.where(DataAccessLog.created_at <= end)
        except:
            pass

    total_result = await db.execute(query)
    total = len(total_result.scalars().all())

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()

    items = [
        {
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "username": log.username,
            "resource_type": log.resource_type,
            "resource_id": str(log.resource_id) if log.resource_id else None,
            "resource_name": log.resource_name,
            "data_level": log.data_level,
            "operation": log.operation,
            "status": log.status,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]

    return page_response(items, total, page, page_size)


@router.post("/operation", response_model=dict)
async def create_operation_log(
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    """创建操作日志（内部使用）"""
    log = OperationLog(**data)
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return success({"id": str(log.id)})


@router.post("/login", response_model=dict)
async def create_login_log(
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    """创建登录日志（内部使用）"""
    log = LoginLog(**data)
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return success({"id": str(log.id)})


@router.post("/access", response_model=dict)
async def create_data_access_log(
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    """创建数据访问日志（内部使用）"""
    log = DataAccessLog(**data)
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return success({"id": str(log.id)})
