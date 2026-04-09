"""
年级管理接口
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.models.grade_model import Grade
from app.schemas.grade import GradeCreate, GradeUpdate
from app.schemas.response import success, page_response

router = APIRouter()


@router.get("", response_model=dict)
async def get_grades(
    name: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取年级列表"""
    query = select(Grade)
    if name:
        query = query.where(Grade.name.like(f"%{name}%"))

    query = query.order_by(Grade.created_at.desc())

    total_result = await db.execute(query)
    total = len(total_result.scalars().all())

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    grades = result.scalars().all()

    items = [
        {
            "id": str(g.id),
            "name": g.name,
            "code": g.code,
            "academic_year": g.academic_year,
            "year": g.year,
            "grade_level": g.grade_level,
            "head_teacher_id": str(g.head_teacher_id) if g.head_teacher_id else None,
            "student_count": g.student_count,
            "class_count": g.class_count,
            "status": g.status,
            "description": g.description,
        }
        for g in grades
    ]

    return page_response(items, total, page, page_size)


@router.get("/options", response_model=dict)
async def get_grade_options(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """获取年级下拉选项"""
    result = await db.execute(select(Grade).where(Grade.status == "active"))
    grades = result.scalars().all()
    options = [{"value": str(g.id), "label": g.name} for g in grades]
    return success(options)


@router.get("/teachers", response_model=dict)
async def get_teacher_options(
    role: str = Query("teacher"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教师下拉选项"""
    from app.models.user import User as UserModel

    result = await db.execute(select(UserModel).where(UserModel.status == "active"))
    users = result.scalars().all()
    options = [
        {"value": str(u.id), "label": u.real_name or u.username}
        for u in users
        if u.position or u.role == "teacher"
    ]
    if not options:
        options = [
            {"value": str(u.id), "label": u.real_name or u.username} for u in users
        ]
    return success(options)


@router.get("/{grade_id}", response_model=dict)
async def get_grade(
    grade_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取年级详情"""
    result = await db.execute(select(Grade).where(Grade.id == grade_id))
    grade = result.scalar_one_or_none()

    if not grade:
        raise NotFoundException("年级不存在")

    return success(
        {
            "id": str(grade.id),
            "name": grade.name,
            "code": grade.code,
            "academic_year": grade.academic_year,
            "year": grade.year,
            "grade_level": grade.grade_level,
            "head_teacher_id": str(grade.head_teacher_id)
            if grade.head_teacher_id
            else None,
            "student_count": grade.student_count,
            "class_count": grade.class_count,
            "status": grade.status,
            "description": grade.description,
        }
    )


@router.post("", response_model=dict)
async def create_grade(
    data: GradeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建年级"""
    grade = Grade(**data.model_dump())
    db.add(grade)
    await db.commit()
    await db.refresh(grade)
    return success({"id": str(grade.id)}, "年级创建成功")


@router.put("/{grade_id}", response_model=dict)
async def update_grade(
    grade_id: UUID,
    data: GradeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新年级"""
    result = await db.execute(select(Grade).where(Grade.id == grade_id))
    grade = result.scalar_one_or_none()

    if not grade:
        raise NotFoundException("年级不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(grade, key, value)

    await db.commit()
    await db.refresh(grade)
    return success({"id": str(grade.id)}, "年级更新成功")


@router.delete("/{grade_id}", response_model=dict)
async def delete_grade(
    grade_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除年级"""
    result = await db.execute(select(Grade).where(Grade.id == grade_id))
    grade = result.scalar_one_or_none()

    if not grade:
        raise NotFoundException("年级不存在")

    await db.delete(grade)
    await db.commit()
    return success(message="年级删除成功")
