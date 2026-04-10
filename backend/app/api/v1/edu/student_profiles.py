"""
学生扩展信息接口
"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.schemas.response import success, page_response

router = APIRouter()


class StudentProfileCreate(BaseModel):
    user_id: UUID
    student_no: str
    enrollment_date: Optional[datetime] = None
    graduation_date: Optional[datetime] = None
    student_status: Optional[str] = "active"
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    guardian_id_card: Optional[str] = None
    guardian_relation: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    address: Optional[str] = None
    is_left_behind: Optional[bool] = False
    is_orphan: Optional[bool] = False
    is_disabled: Optional[bool] = False
    is_poor: Optional[bool] = False
    profile_json: Optional[str] = "{}"
    remarks: Optional[str] = None


class StudentProfileUpdate(BaseModel):
    student_no: Optional[str] = None
    enrollment_date: Optional[datetime] = None
    graduation_date: Optional[datetime] = None
    student_status: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    guardian_id_card: Optional[str] = None
    guardian_relation: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    address: Optional[str] = None
    is_left_behind: Optional[bool] = None
    is_orphan: Optional[bool] = None
    is_disabled: Optional[bool] = None
    is_poor: Optional[bool] = None
    profile_json: Optional[str] = None
    remarks: Optional[str] = None


@router.get("", response_model=dict)
async def get_student_profiles(
    keyword: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取学生扩展信息列表"""
    query = select(StudentProfile)

    if keyword:
        query = query.where(StudentProfile.student_no.contains(keyword))
    if status:
        query = query.where(StudentProfile.student_status == status)

    query = query.order_by(StudentProfile.created_at.desc())

    total_result = await db.execute(query)
    total = len(total_result.scalars().all())

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    profiles = result.scalars().all()

    items = [
        {
            "id": str(p.id),
            "user_id": str(p.user_id),
            "student_no": p.student_no,
            "enrollment_date": p.enrollment_date.isoformat()
            if p.enrollment_date
            else None,
            "graduation_date": p.graduation_date.isoformat()
            if p.graduation_date
            else None,
            "student_status": p.student_status,
            "guardian_name": p.guardian_name,
            "guardian_phone": p.guardian_phone,
            "is_left_behind": p.is_left_behind,
            "is_orphan": p.is_orphan,
            "is_disabled": p.is_disabled,
            "is_poor": p.is_poor,
        }
        for p in profiles
    ]

    return page_response(items, total, page, page_size)


@router.get("/{user_id}", response_model=dict)
async def get_student_profile(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取学生扩展信息详情"""
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        return success(None)

    return success(
        {
            "id": str(profile.id),
            "user_id": str(profile.user_id),
            "student_no": profile.student_no,
            "enrollment_date": profile.enrollment_date.isoformat()
            if profile.enrollment_date
            else None,
            "graduation_date": profile.graduation_date.isoformat()
            if profile.graduation_date
            else None,
            "student_status": profile.student_status,
            "guardian_name": profile.guardian_name,
            "guardian_phone": profile.guardian_phone,
            "guardian_id_card": profile.guardian_id_card,
            "guardian_relation": profile.guardian_relation,
            "province": profile.province,
            "city": profile.city,
            "district": profile.district,
            "address": profile.address,
            "is_left_behind": profile.is_left_behind,
            "is_orphan": profile.is_orphan,
            "is_disabled": profile.is_disabled,
            "is_poor": profile.is_poor,
            "profile_json": profile.profile_json,
            "remarks": profile.remarks,
        }
    )


@router.post("", response_model=dict)
async def create_student_profile(
    data: StudentProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建学生扩展信息"""
    profile = StudentProfile(**data.model_dump())
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return success({"id": str(profile.id)}, "学生扩展信息创建成功")


@router.put("/{user_id}", response_model=dict)
async def update_student_profile(
    user_id: UUID,
    data: StudentProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新学生扩展信息"""
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        return success(message="学生扩展信息不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)

    await db.commit()
    await db.refresh(profile)
    return success({"id": str(profile.id)}, "学生扩展信息更新成功")


@router.delete("/{user_id}", response_model=dict)
async def delete_student_profile(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除学生扩展信息"""
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()

    if profile:
        await db.delete(profile)
        await db.commit()

    return success(message="学生扩展信息删除成功")
