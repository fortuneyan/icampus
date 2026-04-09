"""
考勤管理接口
"""

from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.attendance import RuleCreate, RuleUpdate, CheckInRequest
from app.schemas.response import success, page_response
from app.services.attendance_service import RuleService, RecordService

router = APIRouter()


@router.get("/rules", response_model=dict)
async def get_rules(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    service = RuleService(db)
    rules = await service.get_all([service.model.status == "active"])
    items = [
        {
            "id": str(r.id),
            "name": r.name,
            "check_in_start": str(r.check_in_start) if r.check_in_start else None,
            "check_in_end": str(r.check_in_end) if r.check_in_end else None,
            "location": r.location,
        }
        for r in rules
    ]
    return success(items)


@router.post("/rules", response_model=dict)
async def create_rule(
    data: RuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RuleService(db)
    rule = await service.create_rule(data.model_dump())
    return success({"id": str(rule.id)}, "创建成功")


@router.post("/check-in", response_model=dict)
async def check_in(
    data: CheckInRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RecordService(db)
    record = await service.check_in(
        current_user.id, data.rule_id, data.photo, data.location
    )
    return success(
        {"id": str(record.id), "check_in_time": record.check_in_time.isoformat()},
        "签到成功",
    )


@router.get("/records", response_model=dict)
async def get_records(
    page: int = Query(1),
    page_size: int = Query(20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RecordService(db)
    result = await service.get_user_records(current_user.id, page, page_size)
    items = [
        {
            "id": str(r.id),
            "check_in_time": r.check_in_time.isoformat() if r.check_in_time else None,
            "check_out_time": r.check_out_time.isoformat()
            if r.check_out_time
            else None,
            "status": r.status,
        }
        for r in result["items"]
    ]
    return page_response(items, result["total"], page, page_size)


@router.get("/statistics", response_model=dict)
async def get_statistics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RecordService(db)
    start = (
        datetime.fromisoformat(start_date)
        if start_date
        else datetime.now() - timedelta(days=30)
    )
    end = datetime.fromisoformat(end_date) if end_date else datetime.now()
    stats = await service.get_statistics(current_user.id, start, end)
    return success(stats)
