"""
学籍变动管理接口
"""

from datetime import datetime
from uuid import uuid4
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.student import Student, StudentClassHistory, get_current_academic_year
from app.models.grade_model import Grade
from app.models.class_model import Class
from app.models.enrollment_change import EnrollmentChange
from app.schemas.response import success, page_response
from app.core.exceptions import NotFoundException, ValidationException

router = APIRouter()

MAX_GRADE_LEVEL = 12


@router.get("/students/{student_id}/history", response_model=dict)
async def get_student_enrollment_history(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取学生学籍变动历史"""
    result = await db.execute(
        select(Student).where(Student.id == uuid4() if isinstance(student_id, str) else student_id)
    )
    student = result.scalar_one_or_none()
    
    if not student:
        raise NotFoundException("学生不存在")
    
    result = await db.execute(
        select(EnrollmentChange)
        .where(EnrollmentChange.student_id == student.id)
        .order_by(EnrollmentChange.change_date.desc())
    )
    changes = result.scalars().all()
    
    change_list = []
    for c in changes:
        to_grade_name = None
        to_class_name = None
        if c.to_grade_id:
            grade_result = await db.execute(select(Grade).where(Grade.id == c.to_grade_id))
            grade = grade_result.scalar_one_or_none()
            to_grade_name = grade.name if grade else None
        
        if c.to_class_id:
            class_result = await db.execute(select(Class).where(Class.id == c.to_class_id))
            cls = class_result.scalar_one_or_none()
            to_class_name = cls.name if cls else None
        
        change_list.append({
            "change_type": c.change_type,
            "change_type_name": c.change_type_name,
            "change_date": c.change_date.isoformat() if c.change_date else None,
            "effective_date": c.effective_date.isoformat() if c.effective_date else None,
            "to_grade": to_grade_name,
            "to_class": to_class_name,
            "from_status": c.from_status,
            "to_status": c.to_status,
            "reason": c.reason,
            "notes": c.notes,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    
    result = await db.execute(
        select(StudentClassHistory)
        .where(StudentClassHistory.student_id == student.id)
        .order_by(StudentClassHistory.start_date.desc())
    )
    class_changes = result.scalars().all()

    class_change_list = []
    for ch in class_changes:
        class_change_list.append({
            "change_type": "class_change",
            "change_type_name": ch.change_type_name,
            "change_date": ch.start_date.isoformat() if ch.start_date else None,
            "to_class": ch.display_class_name,
            "reason": ch.reason,
        })

    return success({
        "student_id": str(student.id),
        "student_name": student.name,
        "student_no": student.student_no,
        "enrollment_status": student.enrollment_status,
        "changes": change_list,
        "class_changes": class_change_list,
    })


@router.get("/changes", response_model=dict)
async def get_enrollment_changes(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    change_type: Optional[str] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取学籍变动记录列表"""
    query = select(EnrollmentChange).order_by(EnrollmentChange.change_date.desc())
    
    if start_date:
        query = query.where(EnrollmentChange.change_date >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.where(EnrollmentChange.change_date <= datetime.fromisoformat(end_date))
    if change_type:
        query = query.where(EnrollmentChange.change_type == change_type)
    
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    changes = result.scalars().all()
    
    count_result = await db.execute(select(EnrollmentChange).order_by(None))
    total = len((await db.execute(count_result.order_by(None))).fetchall()) if hasattr(await db.execute(count_result), 'fetchall') else 0
    
    change_list = []
    for c in changes:
        change_list.append({
            "id": str(c.id),
            "student_id": str(c.student_id),
            "change_type": c.change_type,
            "change_type_name": c.change_type_name,
            "change_date": c.change_date.isoformat() if c.change_date else None,
            "from_status": c.from_status,
            "to_status": c.to_status,
            "reason": c.reason,
        })
    
    return page_response(change_list, total, page, page_size)


async def record_enrollment_change(
    db: AsyncSession,
    student: Student,
    change_type: str,
    from_grade_id,
    to_grade_id,
    from_class_id,
    to_class_id,
    from_status,
    to_status,
    reason: str,
    notes: str = None,
    operator_id = None,
):
    """记录学籍变动"""
    now = datetime.now()
    change = EnrollmentChange(
        id=uuid4(),
        student_id=student.id,
        change_type=change_type,
        from_grade_id=from_grade_id,
        to_grade_id=to_grade_id,
        from_class_id=from_class_id,
        to_class_id=to_class_id,
        from_status=from_status,
        to_status=to_status,
        change_date=now,
        effective_date=now,
        reason=reason,
        notes=notes,
        operator_id=operator_id,
    )
    db.add(change)

    student.enrollment_status = to_status
    student.last_change_date = now

    return change


@router.put("/students/{student_id}/promote", response_model=dict)
async def promote_student(
    student_id: str,
    target_grade_id: str = Query(...),
    target_class_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """升级学生"""
    from uuid import UUID

    student_id_uuid = UUID(student_id)
    target_grade_id_uuid = UUID(target_grade_id) if target_grade_id else None
    target_class_id_uuid = UUID(target_class_id) if target_class_id else None

    result = await db.execute(select(Student).where(Student.id == student_id_uuid))
    student = result.scalar_one_or_none()

    if not student:
        raise NotFoundException("学生不存在")

    if student.enrollment_status != "in_school":
        raise ValidationException("只有在校生可以升级")

    from_grade_id = student.grade_id
    from_class_id = student.class_id

    student.grade_id = target_grade_id_uuid
    student.class_id = target_class_id_uuid

    await record_enrollment_change(
        db=db,
        student=student,
        change_type="promote",
        from_grade_id=from_grade_id,
        to_grade_id=target_grade_id_uuid,
        from_class_id=from_class_id,
        to_class_id=target_class_id_uuid,
        from_status="in_school",
        to_status="in_school",
        reason="学年末升级",
        operator_id=current_user.id,
    )

    await db.commit()

    return success({"student_id": str(student.id)}, "升级成功")


@router.post("/students/{student_id}/suspend", response_model=dict)
async def suspend_student(
    student_id: str,
    reason: str = Query(...),
    notes: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """休学"""
    from uuid import UUID

    student_id_uuid = UUID(student_id)

    result = await db.execute(select(Student).where(Student.id == student_id_uuid))
    student = result.scalar_one_or_none()

    if not student:
        raise NotFoundException("学生不存在")

    if student.enrollment_status != "in_school":
        raise ValidationException("只有在校生可以休学")

    from_status = student.enrollment_status

    await record_enrollment_change(
        db=db,
        student=student,
        change_type="suspend",
        from_grade_id=student.grade_id,
        to_grade_id=student.grade_id,
        from_class_id=student.class_id,
        to_class_id=None,
        from_status=from_status,
        to_status="suspended",
        reason=reason,
        notes=notes,
        operator_id=current_user.id,
    )

    await db.commit()

    return success({"student_id": str(student.id)}, "休学申请已提交")


@router.post("/students/{student_id}/resume", response_model=dict)
async def resume_student(
    student_id: str,
    target_class_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """复学"""
    from uuid import UUID

    student_id_uuid = UUID(student_id)
    target_class_id_uuid = UUID(target_class_id) if target_class_id else None

    result = await db.execute(select(Student).where(Student.id == student_id_uuid))
    student = result.scalar_one_or_none()

    if not student:
        raise NotFoundException("学生不存在")

    if student.enrollment_status != "suspended":
        raise ValidationException("只有休学生可以复学")

    student.class_id = target_class_id_uuid

    await record_enrollment_change(
        db=db,
        student=student,
        change_type="resume",
        from_grade_id=student.grade_id,
        to_grade_id=student.grade_id,
        from_class_id=None,
        to_class_id=target_class_id_uuid,
        from_status="suspended",
        to_status="in_school",
        reason="休学期满复学",
        operator_id=current_user.id,
    )

    await db.commit()

    return success({"student_id": str(student.id)}, "复学成功")


@router.post("/students/{student_id}/graduate", response_model=dict)
async def graduate_student(
    student_id: str,
    diploma_no: Optional[str] = Query(None),
    notes: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """毕业"""
    from uuid import UUID

    student_id_uuid = UUID(student_id)

    result = await db.execute(select(Student).where(Student.id == student_id_uuid))
    student = result.scalar_one_or_none()

    if not student:
        raise NotFoundException("学生不存在")

    if student.enrollment_status != "in_school":
        raise ValidationException("只有在校生可以办理毕业")

    student.enrollment_status = "graduated"
    student.graduation_year = datetime.now().year
    if diploma_no:
        student.diploma_no = diploma_no

    await record_enrollment_change(
        db=db,
        student=student,
        change_type="graduate",
        from_grade_id=student.grade_id,
        to_grade_id=None,
        from_class_id=student.class_id,
        to_class_id=None,
        from_status="in_school",
        to_status="graduated",
        reason="正常毕业",
        notes=f"���业��编号: {diploma_no}" if diploma_no else "正常毕业",
        operator_id=current_user.id,
    )

    await db.commit()

    return success({"student_id": str(student.id)}, "毕业办理成功")


@router.post("/students/{student_id}/quit", response_model=dict)
async def quit_student(
    student_id: str,
    reason: str = Query(...),
    notes: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """退学"""
    from uuid import UUID

    student_id_uuid = UUID(student_id)

    result = await db.execute(select(Student).where(Student.id == student_id_uuid))
    student = result.scalar_one_or_none()

    if not student:
        raise NotFoundException("学生不存在")

    if student.enrollment_status != "in_school":
        raise ValidationException("只有在校生可以办理退学")

    student.enrollment_status = "leave"

    await record_enrollment_change(
        db=db,
        student=student,
        change_type="quit",
        from_grade_id=student.grade_id,
        to_grade_id=None,
        from_class_id=student.class_id,
        to_class_id=None,
        from_status="in_school",
        to_status="leave",
        reason=reason,
        notes=notes,
        operator_id=current_user.id,
    )

    await db.commit()

    return success({"student_id": str(student.id)}, "退学办理成功")


@router.post("/students/{student_id}/repeat", response_model=dict)
async def repeat_student(
    student_id: str,
    target_class_id: Optional[str] = Query(None),
    reason: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """留级"""
    from uuid import UUID

    student_id_uuid = UUID(student_id)
    target_class_id_uuid = UUID(target_class_id) if target_class_id else None

    result = await db.execute(select(Student).where(Student.id == student_id_uuid))
    student = result.scalar_one_or_none()

    if not student:
        raise NotFoundException("学生不存在")

    if student.enrollment_status != "in_school":
        raise ValidationException("只有在校生可以留级")

    from_grade_id = student.grade_id

    student.enrollment_status = "repeating"
    student.class_id = target_class_id_uuid

    await record_enrollment_change(
        db=db,
        student=student,
        change_type="repeat",
        from_grade_id=from_grade_id,
        to_grade_id=from_grade_id,
        from_class_id=student.class_id,
        to_class_id=target_class_id_uuid,
        from_status="in_school",
        to_status="repeating",
        reason=reason or "成绩不合格留级",
        operator_id=current_user.id,
    )

    await db.commit()

    return success({"student_id": str(student.id)}, "留级处理成功")


@router.post("/students/{student_id}/retry", response_model=dict)
async def retry_student(
    student_id: str,
    target_grade_id: str = Query(...),
    target_class_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """复读（重新入学）"""
    from uuid import UUID

    student_id_uuid = UUID(student_id)
    target_grade_id_uuid = UUID(target_grade_id)
    target_class_id_uuid = UUID(target_class_id) if target_class_id else None

    result = await db.execute(select(Student).where(Student.id == student_id_uuid))
    student = result.scalar_one_or_none()

    if not student:
        raise NotFoundException("学生不存在")

    if student.enrollment_status in ("in_school", "repeating"):
        raise ValidationException("该学生状态不允许复读")

    student.grade_id = target_grade_id_uuid
    student.class_id = target_class_id_uuid
    student.enrollment_status = "in_school"

    await record_enrollment_change(
        db=db,
        student=student,
        change_type="retry",
        from_grade_id=None,
        to_grade_id=target_grade_id_uuid,
        from_class_id=None,
        to_class_id=target_class_id_uuid,
        from_status=student.enrollment_status,
        to_status="in_school",
        reason="自愿复读",
        operator_id=current_user.id,
    )

    await db.commit()

    return success({"student_id": str(student.id)}, "复读处理成功")


@router.post("/tasks/auto-promote", response_model=dict)
async def auto_promote_students(
    academic_year: Optional[str] = Query(None),
    dry_run: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """自动升级任务

    - 将所有在校生年级+1
    - 超过最大年级的学生自动毕业
    - 支持预览模式（dry_run=true）
    """
    if not academic_year:
        academic_year = get_current_academic_year()

    result = await db.execute(
        select(Student).where(Student.enrollment_status == "in_school")
    )
    students = result.scalars().all()

    promote_list = []
    graduate_list = []
    fail_list = []

    current_year = int(academic_year.split("-")[0])

    for student in students:
        if not student.enrollment_year:
            fail_list.append({"id": str(student.id), "name": student.name, "reason": "无入学年份"})
            continue

        expected_level = current_year - student.enrollment_year + 1

        if expected_level > MAX_GRADE_LEVEL:
            if not dry_run:
                student.enrollment_status = "graduated"
                student.graduation_year = current_year

                await record_enrollment_change(
                    db=db,
                    student=student,
                    change_type="graduate",
                    from_grade_id=student.grade_id,
                    to_grade_id=None,
                    from_class_id=student.class_id,
                    to_class_id=None,
                    from_status="in_school",
                    to_status="graduated",
                    reason="自动毕业（超过最大年级）",
                    operator_id=current_user.id,
                )

            graduate_list.append({"id": str(student.id), "name": student.name, "grade_level": expected_level})
        else:
            promote_list.append({"id": str(student.id), "name": student.name, "grade_level": expected_level})

    if not dry_run:
        await db.commit()

    return success({
        "academic_year": academic_year,
        "total_students": len(students),
        "promote_count": len(promote_list),
        "promote_list": promote_list[:10],
        "graduate_count": len(graduate_list),
        "graduate_list": graduate_list[:10],
        "fail_count": len(fail_list),
        "dry_run": dry_run,
    }, "自动升级完成" if not dry_run else "预览模式")


@router.get("/stats/summary", response_model=dict)
async def get_enrollment_stats(
    academic_year: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取学籍统计"""
    if not academic_year:
        academic_year = get_current_academic_year()

    result = await db.execute(select(Student).where(Student.deleted_at == None))
    students = result.scalars().all()

    stats = {
        "total": len(students),
        "in_school": 0,
        "suspended": 0,
        "graduated": 0,
        "leave": 0,
        "repeating": 0,
        "by_cohort": {},
        "academic_year": academic_year,
    }

    for student in students:
        status = student.enrollment_status or "in_school"
        if status in stats:
            stats[status] += 1

        cohort = student.enrollment_cohort
        if cohort:
            stats["by_cohort"][cohort] = stats["by_cohort"].get(cohort, 0) + 1

    return success(stats)


@router.get("/students/grade-info", response_model=dict)
async def get_students_with_grade_info(
    page: int = Query(1),
    page_size: int = Query(20),
    keyword: Optional[str] = Query(None),
    enrollment_status: Optional[str] = Query(None),
    enrollment_year: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取学生列表（带自动计算的年级信息）"""
    query = select(Student).where(Student.deleted_at == None)

    if keyword:
        query = query.where(
            (Student.name.like(f"%{keyword}%")) | (Student.student_no.like(f"%{keyword}%"))
        )

    if enrollment_status:
        query = query.where(Student.enrollment_status == enrollment_status)

    if enrollment_year:
        query = query.where(Student.enrollment_year == enrollment_year)

    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    students = result.scalars().all()

    total_result = await db.execute(select(Student).where(Student.deleted_at == None))
    total = len(total_result.scalars().all())

    items = []
    for s in students:
        items.append({
            "id": str(s.id),
            "student_no": s.student_no,
            "name": s.name,
            "gender": s.gender,
            "enrollment_year": s.enrollment_year,
            "enrollment_cohort": s.enrollment_cohort,
            "grade_level": s.grade_level,
            "grade_name": s.grade_name,
            "class_id": str(s.class_id) if s.class_id else None,
            "class_name": s.class_obj.name if s.class_obj else None,
            "enrollment_status": s.enrollment_status,
            "academic_year": s.academic_year or get_current_academic_year(),
        })

    return page_response(items, total, page, page_size)