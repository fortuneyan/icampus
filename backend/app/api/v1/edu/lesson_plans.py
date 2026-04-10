"""
教案接口
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
from app.models.lesson_plan import LessonPlan
from app.schemas.response import success, page_response

router = APIRouter()


class LessonPlanCreate(BaseModel):
    teacher_id: UUID
    course_id: Optional[UUID] = None
    grade_id: Optional[UUID] = None
    title: str
    lesson_type: Optional[str] = None
    teaching_duration: Optional[str] = None
    objectives: Optional[str] = None
    key_points: Optional[str] = None
    difficult_points: Optional[str] = None
    teaching_steps: Optional[str] = None
    homework: Optional[str] = None
    reflection: Optional[str] = None
    attachments: Optional[str] = None
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    status: Optional[str] = "draft"
    remarks: Optional[str] = None


class LessonPlanUpdate(BaseModel):
    course_id: Optional[UUID] = None
    grade_id: Optional[UUID] = None
    title: Optional[str] = None
    lesson_type: Optional[str] = None
    teaching_duration: Optional[str] = None
    objectives: Optional[str] = None
    key_points: Optional[str] = None
    difficult_points: Optional[str] = None
    teaching_steps: Optional[str] = None
    homework: Optional[str] = None
    reflection: Optional[str] = None
    attachments: Optional[str] = None
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    status: Optional[str] = None
    remarks: Optional[str] = None


@router.get("", response_model=dict)
async def get_lesson_plans(
    teacher_id: Optional[UUID] = Query(None),
    course_id: Optional[UUID] = Query(None),
    grade_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教案列表"""
    query = select(LessonPlan).order_by(desc(LessonPlan.created_at))

    if teacher_id:
        query = query.where(LessonPlan.teacher_id == teacher_id)
    if course_id:
        query = query.where(LessonPlan.course_id == course_id)
    if grade_id:
        query = query.where(LessonPlan.grade_id == grade_id)
    if status:
        query = query.where(LessonPlan.status == status)

    total_result = await db.execute(query)
    total = len(total_result.scalars().all())

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    plans = result.scalars().all()

    items = [
        {
            "id": str(p.id),
            "teacher_id": str(p.teacher_id),
            "course_id": str(p.course_id) if p.course_id else None,
            "title": p.title,
            "lesson_type": p.lesson_type,
            "teaching_duration": p.teaching_duration,
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in plans
    ]

    return page_response(items, total, page, page_size)


@router.get("/{plan_id}", response_model=dict)
async def get_lesson_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教案详情"""
    result = await db.execute(select(LessonPlan).where(LessonPlan.id == plan_id))
    plan = result.scalar_one_or_none()

    if not plan:
        return success(None)

    return success(
        {
            "id": str(plan.id),
            "teacher_id": str(plan.teacher_id),
            "course_id": str(plan.course_id) if plan.course_id else None,
            "grade_id": str(plan.grade_id) if plan.grade_id else None,
            "title": plan.title,
            "lesson_type": plan.lesson_type,
            "teaching_duration": plan.teaching_duration,
            "objectives": plan.objectives,
            "key_points": plan.key_points,
            "difficult_points": plan.difficult_points,
            "teaching_steps": plan.teaching_steps,
            "homework": plan.homework,
            "reflection": plan.reflection,
            "attachments": plan.attachments,
            "status": plan.status,
            "reviewer_id": str(plan.reviewer_id) if plan.reviewer_id else None,
            "reviewed_at": plan.reviewed_at.isoformat() if plan.reviewed_at else None,
            "review_comment": plan.review_comment,
            "academic_year": plan.academic_year,
            "semester": plan.semester,
            "remarks": plan.remarks,
        }
    )


@router.post("", response_model=dict)
async def create_lesson_plan(
    data: LessonPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建教案"""
    plan = LessonPlan(**data.model_dump())
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return success({"id": str(plan.id)}, "教案创建成功")


@router.put("/{plan_id}", response_model=dict)
async def update_lesson_plan(
    plan_id: UUID,
    data: LessonPlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新教案"""
    result = await db.execute(select(LessonPlan).where(LessonPlan.id == plan_id))
    plan = result.scalar_one_or_none()

    if not plan:
        return success(message="教案不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan, key, value)

    await db.commit()
    await db.refresh(plan)
    return success({"id": str(plan.id)}, "教案更新成功")


@router.delete("/{plan_id}", response_model=dict)
async def delete_lesson_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除教案"""
    result = await db.execute(select(LessonPlan).where(LessonPlan.id == plan_id))
    plan = result.scalar_one_or_none()

    if plan:
        await db.delete(plan)
        await db.commit()

    return success(message="教案删除成功")


@router.post("/{plan_id}/submit", response_model=dict)
async def submit_lesson_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交教案"""
    result = await db.execute(select(LessonPlan).where(LessonPlan.id == plan_id))
    plan = result.scalar_one_or_none()

    if not plan:
        return success(message="教案不存在")

    plan.status = "submitted"
    await db.commit()
    return success(message="教案提交成功")


@router.post("/{plan_id}/review", response_model=dict)
async def review_lesson_plan(
    plan_id: UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """审批教案"""
    result = await db.execute(select(LessonPlan).where(LessonPlan.id == plan_id))
    plan = result.scalar_one_or_none()

    if not plan:
        return success(message="教案不存在")

    approve = data.get("approve", True)
    if approve:
        plan.status = "approved"
        plan.reviewer_id = current_user.id
        plan.reviewed_at = datetime.now()
        if "comment" in data:
            plan.review_comment = data["comment"]
    else:
        plan.status = "rejected"
        if "comment" in data:
            plan.review_comment = data["comment"]

    await db.commit()
    return success(message="教案审批完成")
