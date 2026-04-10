"""
教师扩展信息接口
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
from app.models.teacher_profile import TeacherProfile
from app.schemas.response import success, page_response

router = APIRouter()


class TeacherProfileCreate(BaseModel):
    user_id: UUID
    employee_no: str
    hire_date: Optional[datetime] = None
    position: Optional[str] = None
    title: Optional[str] = None
    employment_type: Optional[str] = "full_time"
    subject: Optional[str] = None
    teaching_grade: Optional[str] = None
    teacher_certificate: Optional[str] = None
    education: Optional[str] = None
    degree: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    profile_json: Optional[str] = "{}"
    remarks: Optional[str] = None


class TeacherProfileUpdate(BaseModel):
    employee_no: Optional[str] = None
    hire_date: Optional[datetime] = None
    position: Optional[str] = None
    title: Optional[str] = None
    employment_type: Optional[str] = None
    subject: Optional[str] = None
    teaching_grade: Optional[str] = None
    teacher_certificate: Optional[str] = None
    education: Optional[str] = None
    degree: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    profile_json: Optional[str] = None
    remarks: Optional[str] = None


@router.get("", response_model=dict)
async def get_teacher_profiles(
    keyword: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教师扩展信息列表"""
    query = select(TeacherProfile)

    if keyword:
        query = query.where(TeacherProfile.employee_no.contains(keyword))
    if subject:
        query = query.where(TeacherProfile.subject == subject)

    query = query.order_by(TeacherProfile.created_at.desc())

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
            "employee_no": p.employee_no,
            "hire_date": p.hire_date.isoformat() if p.hire_date else None,
            "position": p.position,
            "title": p.title,
            "subject": p.subject,
            "employment_type": p.employment_type,
        }
        for p in profiles
    ]

    return page_response(items, total, page, page_size)


@router.get("/{user_id}", response_model=dict)
async def get_teacher_profile(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教师扩展信息详情"""
    result = await db.execute(
        select(TeacherProfile).where(TeacherProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        return success(None)

    return success(
        {
            "id": str(profile.id),
            "user_id": str(profile.user_id),
            "employee_no": profile.employee_no,
            "hire_date": profile.hire_date.isoformat() if profile.hire_date else None,
            "position": profile.position,
            "title": profile.title,
            "employment_type": profile.employment_type,
            "subject": profile.subject,
            "teaching_grade": profile.teaching_grade,
            "teacher_certificate": profile.teacher_certificate,
            "education": profile.education,
            "degree": profile.degree,
            "emergency_contact": profile.emergency_contact,
            "emergency_phone": profile.emergency_phone,
            "profile_json": profile.profile_json,
            "remarks": profile.remarks,
        }
    )


@router.post("", response_model=dict)
async def create_teacher_profile(
    data: TeacherProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建教师扩展信息"""
    profile = TeacherProfile(**data.model_dump())
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return success({"id": str(profile.id)}, "教师扩展信息创建成功")


@router.put("/{user_id}", response_model=dict)
async def update_teacher_profile(
    user_id: UUID,
    data: TeacherProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新教师扩展信息"""
    result = await db.execute(
        select(TeacherProfile).where(TeacherProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        return success(message="教师扩展信息不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)

    await db.commit()
    await db.refresh(profile)
    return success({"id": str(profile.id)}, "教师扩展信息更新成功")


@router.delete("/{user_id}", response_model=dict)
async def delete_teacher_profile(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除教师扩展信息"""
    result = await db.execute(
        select(TeacherProfile).where(TeacherProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()

    if profile:
        await db.delete(profile)
        await db.commit()

    return success(message="教师扩展信息删除成功")
