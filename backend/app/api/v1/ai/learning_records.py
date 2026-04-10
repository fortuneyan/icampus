"""
学习记录追踪接口
"""

from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.learning_record import LearningRecord
from app.schemas.response import success, page_response

router = APIRouter()


class LearningRecordCreate(BaseModel):
    resource_type: Optional[str] = None
    resource_id: Optional[UUID] = None
    resource_name: Optional[str] = None
    action_type: str
    duration: Optional[int] = 0
    progress: Optional[float] = 0.0
    score: Optional[float] = None


@router.get("", response_model=dict)
async def get_learning_records(
    resource_type: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取学习记录列表"""
    query = (
        select(LearningRecord)
        .where(LearningRecord.user_id == current_user.id)
        .order_by(desc(LearningRecord.created_at))
    )

    if resource_type:
        query = query.where(LearningRecord.resource_type == resource_type)
    if action_type:
        query = query.where(LearningRecord.action_type == action_type)
    if start_date:
        try:
            start = datetime.fromisoformat(start_date)
            query = query.where(LearningRecord.created_at >= start)
        except:
            pass
    if end_date:
        try:
            end = datetime.fromisoformat(end_date)
            query = query.where(LearningRecord.created_at <= end)
        except:
            pass

    total_result = await db.execute(query)
    total = len(total_result.scalars().all())

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    records = result.scalars().all()

    items = [
        {
            "id": str(r.id),
            "resource_type": r.resource_type,
            "resource_id": str(r.resource_id) if r.resource_id else None,
            "resource_name": r.resource_name,
            "action_type": r.action_type,
            "duration": r.duration,
            "progress": r.progress,
            "score": r.score,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]

    return page_response(items, total, page, page_size)


@router.post("", response_model=dict)
async def create_learning_record(
    data: LearningRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建学习记录"""
    record = LearningRecord(user_id=current_user.id, **data.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return success({"id": str(record.id)}, "学习记录创建成功")


@router.get("/statistics", response_model=dict)
async def get_learning_statistics(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取学习统计"""
    start_date = datetime.now() - timedelta(days=days)

    result = await db.execute(
        select(LearningRecord).where(
            LearningRecord.user_id == current_user.id,
            LearningRecord.created_at >= start_date,
        )
    )
    records = result.scalars().all()

    total_duration = sum(r.duration for r in records)
    total_count = len(records)

    action_stats = {}
    for r in records:
        action = r.action_type or "unknown"
        if action not in action_stats:
            action_stats[action] = {"count": 0, "duration": 0}
        action_stats[action]["count"] += 1
        action_stats[action]["duration"] += r.duration

    return success(
        {
            "total_duration": total_duration,
            "total_count": total_count,
            "action_stats": action_stats,
            "days": days,
        }
    )


@router.get("/daily", response_model=dict)
async def get_daily_learning(
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取每日学习数据"""
    start_date = datetime.now() - timedelta(days=days)

    result = await db.execute(
        select(LearningRecord).where(
            LearningRecord.user_id == current_user.id,
            LearningRecord.created_at >= start_date,
        )
    )
    records = result.scalars().all()

    daily_data = {}
    for r in records:
        date_key = r.created_at.strftime("%Y-%m-%d") if r.created_at else "unknown"
        if date_key not in daily_data:
            daily_data[date_key] = {"count": 0, "duration": 0}
        daily_data[date_key]["count"] += 1
        daily_data[date_key]["duration"] += r.duration

    items = [
        {"date": date, "count": data["count"], "duration": data["duration"]}
        for date, data in sorted(daily_data.items())
    ]

    return success(items)
