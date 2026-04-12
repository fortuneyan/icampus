"""
学生成长档案接口
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.growth_record import GrowthRecord, GrowthComment
from app.schemas.response import success, page_response

router = APIRouter()


# ==================== 成长记录 ====================

class GrowthRecordCreate(BaseModel):
    student_id: UUID
    record_type: str  # photo/video/honor/activity/comment
    title: str
    content: Optional[str] = None
    attachment_url: Optional[str] = None
    attachment_urls: Optional[str] = None
    tags: Optional[str] = None
    record_date: Optional[datetime] = None
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    is_public: bool = False
    is_featured: bool = False
    status: str = "draft"


class GrowthRecordUpdate(BaseModel):
    record_type: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    attachment_url: Optional[str] = None
    attachment_urls: Optional[str] = None
    tags: Optional[str] = None
    record_date: Optional[datetime] = None
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    is_public: Optional[bool] = None
    is_featured: Optional[bool] = None
    status: Optional[str] = None


@router.get("/growth-records", response_model=dict)
async def get_growth_records(
    student_id: Optional[UUID] = Query(None),
    record_type: Optional[str] = Query(None),
    academic_year: Optional[str] = Query(None),
    semester: Optional[str] = Query(None),
    is_public: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取成长记录列表"""
    query = select(GrowthRecord).order_by(desc(GrowthRecord.created_at))

    if student_id:
        query = query.where(GrowthRecord.student_id == student_id)
    if record_type:
        query = query.where(GrowthRecord.record_type == record_type)
    if academic_year:
        query = query.where(GrowthRecord.academic_year == academic_year)
    if semester:
        query = query.where(GrowthRecord.semester == semester)
    if is_public is not None:
        query = query.where(GrowthRecord.is_public == is_public)

    total_result = await db.execute(query)
    total = len(total_result.scalars().all())

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    records = result.scalars().all()

    items = [
        {
            "id": str(r.id),
            "student_id": str(r.student_id),
            "record_type": r.record_type,
            "title": r.title,
            "content": r.content,
            "attachment_url": r.attachment_url,
            "tags": r.tags,
            "academic_year": r.academic_year,
            "semester": r.semester,
            "is_public": r.is_public,
            "is_featured": r.is_featured,
            "status": r.status,
            "record_date": r.record_date.isoformat() if r.record_date else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]

    return page_response(items, total, page, page_size)


@router.get("/growth-records/{record_id}", response_model=dict)
async def get_growth_record(
    record_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取成长记录详情"""
    result = await db.execute(
        select(GrowthRecord).where(GrowthRecord.id == record_id)
    )
    record = result.scalar_one_or_none()

    if not record:
        return success(None)

    return success({
        "id": str(record.id),
        "student_id": str(record.student_id),
        "record_type": record.record_type,
        "title": record.title,
        "content": record.content,
        "attachment_url": record.attachment_url,
        "attachment_urls": record.attachment_urls,
        "tags": record.tags,
        "academic_year": record.academic_year,
        "semester": record.semester,
        "is_public": record.is_public,
        "is_featured": record.is_featured,
        "status": record.status,
        "record_date": record.record_date.isoformat() if record.record_date else None,
        "created_by": str(record.created_by) if record.created_by else None,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    })


@router.post("/growth-records", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_growth_record(
    data: GrowthRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建成长记录"""
    record = GrowthRecord(
        **data.model_dump(),
        created_by=current_user.id
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return success({"id": str(record.id)}, "成长记录创建成功")


@router.put("/growth-records/{record_id}", response_model=dict)
async def update_growth_record(
    record_id: UUID,
    data: GrowthRecordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新成长记录"""
    result = await db.execute(
        select(GrowthRecord).where(GrowthRecord.id == record_id)
    )
    record = result.scalar_one_or_none()

    if not record:
        return success(message="成长记录不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(record, key, value)

    await db.commit()
    await db.refresh(record)
    return success({"id": str(record.id)}, "成长记录更新成功")


@router.delete("/growth-records/{record_id}", response_model=dict)
async def delete_growth_record(
    record_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除成长记录"""
    result = await db.execute(
        select(GrowthRecord).where(GrowthRecord.id == record_id)
    )
    record = result.scalar_one_or_none()

    if record:
        await db.delete(record)
        await db.commit()

    return success(message="成长记录删除成功")


@router.get("/growth-records/student/{student_id}/timeline", response_model=dict)
async def get_student_growth_timeline(
    student_id: UUID,
    academic_year: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取学生成长时间线"""
    query = (
        select(GrowthRecord)
        .where(GrowthRecord.student_id == student_id)
        .order_by(GrowthRecord.record_date)
    )

    if academic_year:
        query = query.where(GrowthRecord.academic_year == academic_year)

    result = await db.execute(query)
    records = result.scalars().all()

    # 按月份分组
    timeline = {}
    for record in records:
        if record.record_date:
            month_key = record.record_date.strftime("%Y-%m")
        else:
            month_key = "unknown"
        
        if month_key not in timeline:
            timeline[month_key] = []
        
        timeline[month_key].append({
            "id": str(record.id),
            "record_type": record.record_type,
            "title": record.title,
            "content": record.content,
            "attachment_url": record.attachment_url,
            "record_date": record.record_date.isoformat() if record.record_date else None,
        })

    return success(timeline)
