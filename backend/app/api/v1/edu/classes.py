"""
班级管理接口
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
from app.models.class_model import Class
from app.models.grade_model import Grade
from app.schemas.class_schema import ClassCreate, ClassUpdate
from app.schemas.response import success, page_response

router = APIRouter()


@router.get("", response_model=dict)
async def get_classes(
    name: Optional[str] = Query(None),
    grade_id: Optional[UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取班级列表"""
    query = select(Class)
    if name:
        query = query.where(Class.name.like(f"%{name}%"))
    if grade_id:
        query = query.where(Class.grade_id == grade_id)

    query = query.order_by(Class.created_at.desc())

    total_result = await db.execute(query)
    total = len(total_result.scalars().all())

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    classes = result.scalars().all()

    items = [
        {
            "id": str(c.id),
            "name": c.name,
            "code": c.code,
            "grade_id": str(c.grade_id) if c.grade_id else None,
            "head_teacher_id": str(c.head_teacher_id) if c.head_teacher_id else None,
            "student_count": c.student_count,
            "room_no": c.room_no,
            "academic_year": c.academic_year,
            "semester": c.semester,
            "status": c.status,
        }
        for c in classes
    ]

    return page_response(items, total, page, page_size)


@router.get("/options", response_model=dict)
async def get_class_options(
    grade_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取班级下拉选项"""
    query = select(Class).where(Class.status == "active")
    if grade_id:
        query = query.where(Class.grade_id == grade_id)
    result = await db.execute(query)
    classes = result.scalars().all()
    options = [{"value": str(c.id), "label": c.name} for c in classes]
    return success(options)


@router.get("/{class_id}", response_model=dict)
async def get_class(
    class_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取班级详情"""
    result = await db.execute(select(Class).where(Class.id == class_id))
    cls = result.scalar_one_or_none()

    if not cls:
        raise NotFoundException("班级不存在")

    return success(
        {
            "id": str(cls.id),
            "name": cls.name,
            "code": cls.code,
            "grade_id": str(cls.grade_id) if cls.grade_id else None,
            "head_teacher_id": str(cls.head_teacher_id)
            if cls.head_teacher_id
            else None,
            "student_count": cls.student_count,
            "room_no": cls.room_no,
            "academic_year": cls.academic_year,
            "semester": cls.semester,
            "status": cls.status,
        }
    )


@router.post("", response_model=dict)
async def create_class(
    data: ClassCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建班级"""
    cls = Class(**data.model_dump())
    db.add(cls)
    await db.commit()
    await db.refresh(cls)
    return success({"id": str(cls.id)}, "班级创建成功")


@router.put("/{class_id}", response_model=dict)
async def update_class(
    class_id: UUID,
    data: ClassUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新班级"""
    result = await db.execute(select(Class).where(Class.id == class_id))
    cls = result.scalar_one_or_none()

    if not cls:
        raise NotFoundException("班级不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(cls, key, value)

    await db.commit()
    await db.refresh(cls)
    return success({"id": str(cls.id)}, "班级更新成功")


@router.delete("/{class_id}", response_model=dict)
async def delete_class(
    class_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除班级"""
    result = await db.execute(select(Class).where(Class.id == class_id))
    cls = result.scalar_one_or_none()

    if not cls:
        raise NotFoundException("班级不存在")

    await db.delete(cls)
    await db.commit()
    return success(message="班级删除成功")
