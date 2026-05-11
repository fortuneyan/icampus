"""
课程管理接口
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.models.course import Course
from app.schemas.course import CourseCreate, CourseUpdate
from app.schemas.response import success, page_response
from app.services.course_service import CourseService
from app.utils.parsers import parse_uuid

router = APIRouter()


@router.get("", response_model=dict)
async def get_courses(
    grade_id: Optional[str] = Query(None, description="年级ID"),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取课程列表"""
    course_service = CourseService(db)

    filters = []
    parsed_grade_id = parse_uuid(grade_id)
    if parsed_grade_id:
        filters.append(Course.grade_id == parsed_grade_id)
    if status:
        filters.append(Course.status == status)

    result = await course_service.paginate(page, page_size, filters)

    items = [
        {
            "id": str(c.id),
            "code": c.code,
            "name": c.name,
            "category": c.category,
            "credit": float(c.credit) if c.credit else None,
            "hours": c.hours,
            "teacher_id": str(c.teacher_id) if c.teacher_id else None,
            "teacher_ids": [str(t) for t in c.teacher_ids] if c.teacher_ids else [],
            "grade_id": str(c.grade_id) if c.grade_id else None,
            "semester": c.semester,
            "exam_type": c.exam_type,
            "status": c.status,
            "grade_levels": list(c.grade_levels) if c.grade_levels else [],
            "course_type": c.course_type.value if hasattr(c.course_type, 'value') else str(c.course_type),
            "prerequisite_course_ids": [str(p) for p in (c.prerequisite_course_ids or [])],
        }
        for c in result["items"]
    ]

    return page_response(items, result["total"], page, page_size)


@router.get("/options", response_model=dict)
async def get_course_options(
    grade_id: Optional[str] = Query(None, description="年级ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取课程下拉选项"""
    course_service = CourseService(db)
    options = await course_service.get_course_options(parse_uuid(grade_id))
    return success(options)


@router.get("/{course_id}", response_model=dict)
async def get_course(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取课程详情"""
    course_service = CourseService(db)
    course = await course_service.get(course_id)

    if not course:
        raise NotFoundException("课程不存在")

    return success(
        {
            "id": str(course.id),
            "code": course.code,
            "name": course.name,
            "category": course.category,
            "credit": float(course.credit) if course.credit else None,
            "hours": course.hours,
            "teacher_id": str(course.teacher_id) if course.teacher_id else None,
            "grade_id": str(course.grade_id) if course.grade_id else None,
            "semester": course.semester,
            "exam_type": course.exam_type,
            "status": course.status,
            "grade_levels": list(course.grade_levels) if course.grade_levels else [],
            "course_type": course.course_type.value if hasattr(course.course_type, 'value') else str(course.course_type),
            "prerequisite_course_ids": [str(p) for p in (course.prerequisite_course_ids or [])],
        }
    )


@router.post("", response_model=dict)
async def create_course(
    data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建课程"""
    course_service = CourseService(db)
    course = await course_service.create_course(data.model_dump())
    return success({"id": str(course.id)}, "课程创建成功")


@router.put("/{course_id}", response_model=dict)
async def update_course(
    course_id: UUID,
    data: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新课程"""
    course_service = CourseService(db)
    course = await course_service.update_course(
        course_id, data.model_dump(exclude_unset=True)
    )
    return success({"id": str(course.id)}, "课程更新成功")


@router.delete("/{course_id}", response_model=dict)
async def delete_course(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除课程"""
    course_service = CourseService(db)
    await course_service.soft_delete(course_id)
    return success(message="课程删除成功")


@router.get("/by-teacher/{teacher_id}", response_model=dict)
async def get_courses_by_teacher(
    teacher_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教师承担的课程列表"""
    course_service = CourseService(db)
    courses = await course_service.get_courses_by_teacher(teacher_id)
    return success(courses)
