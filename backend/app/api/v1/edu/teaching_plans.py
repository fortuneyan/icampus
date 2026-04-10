"""
教学计划接口
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
from app.models.teaching_plan import TeachingPlan
from app.schemas.response import success, page_response

router = APIRouter()


class TeachingPlanCreate(BaseModel):
    teacher_id: UUID
    course_id: Optional[UUID] = None
    grade_id: Optional[UUID] = None
    title: str
    objectives: Optional[str] = None
    content: Optional[str] = None
    methodology: Optional[str] = None
    total_periods: Optional[str] = None
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    status: Optional[str] = "draft"
    attachments: Optional[str] = None
    remarks: Optional[str] = None


class TeachingPlanUpdate(BaseModel):
    course_id: Optional[UUID] = None
    grade_id: Optional[UUID] = None
    title: Optional[str] = None
    objectives: Optional[str] = None
    content: Optional[str] = None
    methodology: Optional[str] = None
    total_periods: Optional[str] = None
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    status: Optional[str] = None
    attachments: Optional[str] = None
    remarks: Optional[str] = None


@router.get("", response_model=dict)
async def get_teaching_plans(
    teacher_id: Optional[UUID] = Query(None),
    course_id: Optional[UUID] = Query(None),
    grade_id: Optional[UUID] = Query(None),
    academic_year: Optional[str] = Query(None),
    semester: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教学计划列表"""
    query = select(TeachingPlan).order_by(desc(TeachingPlan.created_at))

    if teacher_id:
        query = query.where(TeachingPlan.teacher_id == teacher_id)
    if course_id:
        query = query.where(TeachingPlan.course_id == course_id)
    if grade_id:
        query = query.where(TeachingPlan.grade_id == grade_id)
    if academic_year:
        query = query.where(TeachingPlan.academic_year == academic_year)
    if semester:
        query = query.where(TeachingPlan.semester == semester)
    if status:
        query = query.where(TeachingPlan.status == status)

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
            "grade_id": str(p.grade_id) if p.grade_id else None,
            "title": p.title,
            "academic_year": p.academic_year,
            "semester": p.semester,
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in plans
    ]

    return page_response(items, total, page, page_size)


@router.get("/{plan_id}", response_model=dict)
async def get_teaching_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教学计划详情"""
    result = await db.execute(select(TeachingPlan).where(TeachingPlan.id == plan_id))
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
            "objectives": plan.objectives,
            "content": plan.content,
            "methodology": plan.methodology,
            "total_periods": plan.total_periods,
            "academic_year": plan.academic_year,
            "semester": plan.semester,
            "status": plan.status,
            "approver_id": str(plan.approver_id) if plan.approver_id else None,
            "approved_at": plan.approved_at.isoformat() if plan.approved_at else None,
            "approval_comment": plan.approval_comment,
            "attachments": plan.attachments,
            "remarks": plan.remarks,
        }
    )


@router.post("", response_model=dict)
async def create_teaching_plan(
    data: TeachingPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建教学计划"""
    plan = TeachingPlan(**data.model_dump())
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return success({"id": str(plan.id)}, "教学计划创建成功")


@router.put("/{plan_id}", response_model=dict)
async def update_teaching_plan(
    plan_id: UUID,
    data: TeachingPlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新教学计划"""
    result = await db.execute(select(TeachingPlan).where(TeachingPlan.id == plan_id))
    plan = result.scalar_one_or_none()

    if not plan:
        return success(message="教学计划不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan, key, value)

    await db.commit()
    await db.refresh(plan)
    return success({"id": str(plan.id)}, "教学计划更新成功")


@router.delete("/{plan_id}", response_model=dict)
async def delete_teaching_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除教学计划"""
    result = await db.execute(select(TeachingPlan).where(TeachingPlan.id == plan_id))
    plan = result.scalar_one_or_none()

    if plan:
        await db.delete(plan)
        await db.commit()

    return success(message="教学计划删除成功")


@router.post("/{plan_id}/submit", response_model=dict)
async def submit_teaching_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交教学计划"""
    result = await db.execute(select(TeachingPlan).where(TeachingPlan.id == plan_id))
    plan = result.scalar_one_or_none()

    if not plan:
        return success(message="教学计划不存在")

    plan.status = "submitted"
    await db.commit()
    return success(message="教学计划提交成功")


@router.post("/{plan_id}/approve", response_model=dict)
async def approve_teaching_plan(
    plan_id: UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """审批教学计划"""
    result = await db.execute(select(TeachingPlan).where(TeachingPlan.id == plan_id))
    plan = result.scalar_one_or_none()

    if not plan:
        return success(message="教学计划不存在")

    approve = data.get("approve", True)
    if approve:
        plan.status = "approved"
        plan.approver_id = current_user.id
        plan.approved_at = datetime.now()
        if "comment" in data:
            plan.approval_comment = data["comment"]
    else:
        plan.status = "rejected"
        if "comment" in data:
            plan.approval_comment = data["comment"]

    await db.commit()
    return success(message="教学计划审批完成")
