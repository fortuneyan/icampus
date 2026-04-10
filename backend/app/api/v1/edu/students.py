"""
学生管理接口
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.student import Student
from app.schemas.student import StudentCreate, StudentUpdate
from app.schemas.response import success, page_response

router = APIRouter()


def parse_uuid(value: Optional[str]) -> Optional[UUID]:
    """解析UUID参数"""
    if not value:
        return None
    try:
        return UUID(value)
    except (ValueError, AttributeError):
        return None


@router.get("", response_model=dict)
async def get_students(
    keyword: Optional[str] = Query(None),
    grade_id: Optional[str] = Query(None, description="年级ID"),
    class_id: Optional[str] = Query(None, description="班级ID"),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取学生列表"""
    student_service = StudentService(db)
    result = await student_service.search_students(
        keyword, grade_id, class_id, status, page, page_size
    )

    items = [
        {
            "id": str(s.id),
            "student_no": s.student_no,
            "name": s.name,
            "gender": s.gender,
            "phone": s.phone,
            "grade_id": str(s.grade_id) if s.grade_id else None,
            "class_id": str(s.class_id) if s.class_id else None,
            "status": s.status,
            "enrollment_date": s.enrollment_date.isoformat()
            if s.enrollment_date
            else None,
        }
        for s in result["items"]
    ]

    return page_response(items, result["total"], page, page_size)


@router.get("/options", response_model=dict)
async def get_student_options(
    grade_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取学生下拉选项"""
    student_service = StudentService(db)
    options = await student_service.get_student_options(grade_id)
    return success(options)


@router.get("/{student_id}", response_model=dict)
async def get_student(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取学生详情"""
    student_service = StudentService(db)
    student = await student_service.get(student_id)

    if not student:
        raise NotFoundException("学生不存在")

    return success(
        {
            "id": str(student.id),
            "student_no": student.student_no,
            "name": student.name,
            "gender": student.gender,
            "birth_date": student.birth_date.isoformat()
            if student.birth_date
            else None,
            "id_card": student.id_card,
            "nation": student.nation,
            "origin_type": student.origin_type,
            "address": student.address,
            "phone": student.phone,
            "guardian_name": student.guardian_name,
            "guardian_phone": student.guardian_phone,
            "grade_id": str(student.grade_id) if student.grade_id else None,
            "class_id": str(student.class_id) if student.class_id else None,
            "status": student.status,
            "photo_url": student.photo_url,
            "remarks": student.remarks,
        }
    )


@router.post("", response_model=dict)
async def create_student(
    data: StudentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建学生"""
    student_service = StudentService(db)
    student = await student_service.create_student(data.model_dump())
    return success({"id": str(student.id)}, "学生创建成功")


@router.put("/{student_id}", response_model=dict)
async def update_student(
    student_id: UUID,
    data: StudentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新学生"""
    student_service = StudentService(db)
    student = await student_service.update_student(
        student_id, data.model_dump(exclude_unset=True)
    )
    return success({"id": str(student.id)}, "学生更新成功")


@router.delete("/{student_id}", response_model=dict)
async def delete_student(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除学生"""
    student_service = StudentService(db)
    await student_service.soft_delete(student_id)
    return success(message="学生删除成功")


@router.put("/{student_id}/class", response_model=dict)
async def assign_class(
    student_id: UUID,
    class_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """分配班级"""
    student_service = StudentService(db)
    await student_service.assign_class(student_id, class_id)
    return success(message="班级分配成功")
