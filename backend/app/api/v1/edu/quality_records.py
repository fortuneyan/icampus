"""
综合素质记录接口
"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.quality import QualityRecord
from app.schemas.response import success, page_response

router = APIRouter()


class QualityRecordCreate(BaseModel):
    student_id: UUID
    dimension: str
    title: str
    content: Optional[str] = None
    evidence_url: Optional[str] = None
    self_rating: Optional[int] = None
    record_date: Optional[datetime] = None
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    status: Optional[str] = "draft"
    remarks: Optional[str] = None


class QualityRecordUpdate(BaseModel):
    dimension: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    evidence_url: Optional[str] = None
    self_rating: Optional[int] = None
    teacher_rating: Optional[int] = None
    final_rating: Optional[int] = None
    record_date: Optional[datetime] = None
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    status: Optional[str] = None
    remarks: Optional[str] = None


@router.get("", response_model=dict)
async def get_quality_records(
    student_id: Optional[UUID] = Query(None),
    dimension: Optional[str] = Query(None),
    academic_year: Optional[str] = Query(None),
    semester: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取综合素质记录列表"""
    query = select(QualityRecord).order_by(desc(QualityRecord.created_at))

    if student_id:
        query = query.where(QualityRecord.student_id == student_id)
    if dimension:
        query = query.where(QualityRecord.dimension == dimension)
    if academic_year:
        query = query.where(QualityRecord.academic_year == academic_year)
    if semester:
        query = query.where(QualityRecord.semester == semester)
    if status:
        query = query.where(QualityRecord.status == status)

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
            "dimension": r.dimension,
            "title": r.title,
            "content": r.content,
            "self_rating": r.self_rating,
            "teacher_rating": r.teacher_rating,
            "final_rating": r.final_rating,
            "academic_year": r.academic_year,
            "semester": r.semester,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]

    return page_response(items, total, page, page_size)


@router.get("/{record_id}", response_model=dict)
async def get_quality_record(
    record_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取综合素质记录详情"""
    result = await db.execute(
        select(QualityRecord).where(QualityRecord.id == record_id)
    )
    record = result.scalar_one_or_none()

    if not record:
        return success(None)

    return success(
        {
            "id": str(record.id),
            "student_id": str(record.student_id),
            "dimension": record.dimension,
            "title": record.title,
            "content": record.content,
            "evidence_url": record.evidence_url,
            "self_rating": record.self_rating,
            "teacher_rating": record.teacher_rating,
            "final_rating": record.final_rating,
            "record_date": record.record_date.isoformat()
            if record.record_date
            else None,
            "academic_year": record.academic_year,
            "semester": record.semester,
            "status": record.status,
            "evaluator_id": str(record.evaluator_id) if record.evaluator_id else None,
            "remarks": record.remarks,
        }
    )


@router.post("", response_model=dict)
async def create_quality_record(
    data: QualityRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建综合素质记录"""
    record = QualityRecord(**data.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return success({"id": str(record.id)}, "综合素质记录创建成功")


@router.put("/{record_id}", response_model=dict)
async def update_quality_record(
    record_id: UUID,
    data: QualityRecordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新综合素质记录"""
    result = await db.execute(
        select(QualityRecord).where(QualityRecord.id == record_id)
    )
    record = result.scalar_one_or_none()

    if not record:
        return success(message="综合素质记录不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(record, key, value)

    if data.evaluator_id is None and current_user:
        record.evaluator_id = current_user.id

    await db.commit()
    await db.refresh(record)
    return success({"id": str(record.id)}, "综合素质记录更新成功")


@router.delete("/{record_id}", response_model=dict)
async def delete_quality_record(
    record_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除综合素质记录"""
    result = await db.execute(
        select(QualityRecord).where(QualityRecord.id == record_id)
    )
    record = result.scalar_one_or_none()

    if record:
        await db.delete(record)
        await db.commit()

    return success(message="综合素质记录删除成功")


@router.post("/{record_id}/submit", response_model=dict)
async def submit_quality_record(
    record_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交综合素质记录"""
    result = await db.execute(
        select(QualityRecord).where(QualityRecord.id == record_id)
    )
    record = result.scalar_one_or_none()

    if not record:
        return success(message="综合素质记录不存在")

    record.status = "submitted"
    await db.commit()
    return success(message="综合素质记录提交成功")


@router.post("/{record_id}/confirm", response_model=dict)
async def confirm_quality_record(
    record_id: UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """确认综合素质记录（教师评价）"""
    result = await db.execute(
        select(QualityRecord).where(QualityRecord.id == record_id)
    )
    record = result.scalar_one_or_none()

    if not record:
        return success(message="综合素质记录不存在")

    if "teacher_rating" in data:
        record.teacher_rating = data["teacher_rating"]
    if "final_rating" in data:
        record.final_rating = data["final_rating"]
    if "remarks" in data:
        record.remarks = data["remarks"]

    record.status = "confirmed"
    record.evaluator_id = current_user.id

    await db.commit()
    return success(message="综合素质记录确认成功")
