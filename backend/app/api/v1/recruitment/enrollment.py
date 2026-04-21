from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.student import Student, StudentClassHistory
from app.models.recruitment import Applicant
from app.schemas.response import success, page_response
from app.services.base_service import BaseService

router = APIRouter()


def generate_student_no(db: AsyncSession, grade_id: UUID = None) -> str:
    """生成学号: 年级代码 + 班级 + 序号"""
    import random
    year = datetime.now().year
    random_part = str(random.randint(1000, 9999))
    return f"{year}{random_part}"


@router.post("/applicants/{applicant_id}/enroll", response_model=dict)
async def enroll_applicant(
    applicant_id: UUID,
    class_id: str = Query(...),
    enrollment_type: str = Query("regular"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """录取报名学生"""
    from app.models.recruitment import RecruitmentPlan
    
    result = await db.execute(select(Applicant).where(Applicant.id == applicant_id))
    applicant = result.scalar_one_or_none()
    
    if not applicant:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("报名信息不存在")
    
    if applicant.is_enrolled:
        from app.core.exceptions import ConflictException
        raise ConflictException("该学生已被录取")
    
    class_uuid = UUID(class_id)
    
    student_no = generate_student_no(db, class_uuid)
    
    student = Student(
        student_no=student_no,
        name=applicant.student_name,
        gender=applicant.gender,
        birth_date=applicant.birth_date,
        id_card=applicant.id_card,
        phone=applicant.phone,
        guardian_name=applicant.guardian_name,
        guardian_phone=applicant.guardian_phone,
        address=applicant.address,
        enrollment_date=datetime.now(),
        enrollment_type=enrollment_type,
        grade_id=applicant.grade_id,
        class_id=class_uuid,
        status="active",
    )
    db.add(student)
    await db.flush()
    
    class_history = StudentClassHistory(
        student_id=student.id,
        class_id=class_uuid,
        start_date=datetime.now(),
        reason="录取入学",
        operator_id=current_user.id,
    )
    db.add(class_history)
    
    applicant.is_enrolled = True
    applicant.status = "admitted"
    applicant.enrolled_class_id = class_uuid
    applicant.enrolled_at = datetime.now()
    applicant.student_id = student.id
    
    if applicant.recruitment_plan_id:
        plan_result = await db.execute(
            select(RecruitmentPlan).where(RecruitmentPlan.id == applicant.recruitment_plan_id)
        )
        plan = plan_result.scalar_one_or_none()
        if plan:
            plan.enrolled_count = (plan.enrolled_count or 0) + 1
    
    await db.commit()
    await db.refresh(student)
    
    return success({
        "id": str(student.id),
        "student_no": student.student_no,
        "class_id": class_id
    }, "录取成功，学生档案已创建")


@router.put("/students/batch-promote", response_model=dict)
async def batch_promote_students(
    student_ids: list[str],
    target_grade_id: str,
    target_class_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量升级学生"""
    if not student_ids:
        from app.core.exceptions import ValidationException
        raise ValidationException("请选择要升级的学生")
    
    updated = 0
    for sid in student_ids:
        result = await db.execute(select(Student).where(Student.id == UUID(sid)))
        student = result.scalar_one_or_none()
        if student:
            if student.class_id:
                old_class_id = student.class_id
                history_end = StudentClassHistory(
                    student_id=student.id,
                    class_id=old_class_id,
                    end_date=datetime.now(),
                    reason="学年升级",
                    operator_id=current_user.id,
                )
                db.add(history_end)

            student.class_id = UUID(target_class_id)
            student.grade_id = UUID(target_grade_id)

            history = StudentClassHistory(
                student_id=student.id,
                class_id=UUID(target_class_id),
                start_date=datetime.now(),
                reason="学年升级",
                operator_id=current_user.id,
            )
            db.add(history)
            updated += 1
    
    await db.commit()
    
    return success({"updated": updated}, f"成功升级{updated}名学生")


@router.put("/students/{student_id}/transfer", response_model=dict)
async def transfer_student(
    student_id: UUID,
    target_class_id: str,
    reason: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """调整学生班级"""
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    
    if not student:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("学生不存在")
    
    if student.class_id:
        history_end = StudentClassHistory(
            student_id=student.id,
            class_id=student.class_id,
            end_date=datetime.now(),
            reason=reason,
            operator_id=current_user.id,
        )
        db.add(history_end)

    student.class_id = UUID(target_class_id)
    
    new_history = StudentClassHistory(
        student_id=student.id,
        class_id=UUID(target_class_id),
        start_date=datetime.now(),
        reason=reason,
        operator_id=current_user.id,
    )
    db.add(new_history)
    
    await db.commit()
    
    return success({"id": str(student.id)}, "班级调整成功")


@router.put("/students/{student_id}/status", response_model=dict)
async def change_student_status(
    student_id: UUID,
    status: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """变更学生状态（离校/毕业等）"""
    valid_statuses = ["active", "inactive", "graduated", "transferred"]
    if status not in valid_statuses:
        from app.core.exceptions import ValidationException
        raise ValidationException(f"无效状态: {status}")
    
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    
    if not student:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("学生不存在")
    
    student.status = status
    
    history = StudentClassHistory(
        student_id=student.id,
        class_id=student.class_id,
        end_date=datetime.now(),
        reason=f"状态变更为{status}",
        operator_id=current_user.id,
    )
    db.add(history)
    
    await db.commit()
    
    return success({"id": str(student.id), "status": status}, "状态更新成功")


@router.get("/students/{student_id}/history", response_model=dict)
async def get_student_class_history(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取学生班级变动历史"""
    result = await db.execute(
        select(StudentClassHistory)
        .where(StudentClassHistory.student_id == student_id)
        .order_by(StudentClassHistory.start_date.desc())
    )
    histories = result.scalars().all()
    
    return success([
        {
            "id": str(h.id),
            "class_id": str(h.class_id),
            "start_date": h.start_date.isoformat() if h.start_date else None,
            "end_date": h.end_date.isoformat() if h.end_date else None,
            "reason": h.reason,
            "operator_id": str(h.operator_id) if h.operator_id else None,
        }
        for h in histories
    ])
