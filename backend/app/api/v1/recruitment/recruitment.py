from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.recruitment import RecruitmentPlan, Applicant
from app.schemas.recruitment import (
    RecruitmentPlanCreate, RecruitmentPlanUpdate,
    ApplicantCreate, ApplicantUpdate, FollowUpCreate
)
from app.schemas.response import success, page_response
from app.services.recruitment_service import RecruitmentService, ApplicantService, FollowUpService

router = APIRouter()


@router.get("/plans", response_model=dict)
async def get_recruitment_plans(
    year: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RecruitmentService(db)
    query = select(RecruitmentPlan).order_by(RecruitmentPlan.created_at.desc())
    
    if year:
        query = query.where(RecruitmentPlan.year == year)
    if status:
        query = query.where(RecruitmentPlan.status == status)
    
    result = await db.execute(query)
    plans = result.scalars().all()
    
    total = len(plans)
    offset = (page - 1) * page_size
    items = plans[offset:offset + page_size]
    
    return page_response([
        {
            "id": str(p.id),
            "name": p.name,
            "year": p.year,
            "grade_id": str(p.grade_id) if p.grade_id else None,
            "quota": p.quota,
            "start_date": p.start_date.isoformat(),
            "end_date": p.end_date.isoformat(),
            "description": p.description,
            "status": p.status,
            "created_at": p.created_at.isoformat(),
        }
        for p in items
    ], total, page, page_size)


@router.post("/plans", response_model=dict)
async def create_recruitment_plan(
    data: RecruitmentPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RecruitmentService(db)
    plan = await service.create(data.model_dump())
    return success({"id": str(plan.id)}, "招生计划创建成功")


@router.put("/plans/{plan_id}", response_model=dict)
async def update_recruitment_plan(
    plan_id: UUID,
    data: RecruitmentPlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RecruitmentService(db)
    plan = await service.get(plan_id)
    if not plan:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("招生计划不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan, key, value)
    
    await db.commit()
    await db.refresh(plan)
    return success({"id": str(plan.id)}, "招生计划更新成功")


@router.get("/applicants", response_model=dict)
async def get_applicants(
    status: Optional[str] = Query(None),
    recruitment_plan_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ApplicantService(db)
    query = select(Applicant).order_by(Applicant.created_at.desc())
    
    if status:
        query = query.where(Applicant.status == status)
    if recruitment_plan_id:
        query = query.where(Applicant.recruitment_plan_id == UUID(recruitment_plan_id))
    
    result = await db.execute(query)
    applicants = result.scalars().all()
    
    total = len(applicants)
    offset = (page - 1) * page_size
    items = applicants[offset:offset + page_size]
    
    return page_response([
        {
            "id": str(a.id),
            "student_name": a.student_name,
            "gender": a.gender,
            "phone": a.phone,
            "guardian_name": a.guardian_name,
            "source": a.source,
            "status": a.status,
            "is_enrolled": a.is_enrolled,
            "created_at": a.created_at.isoformat(),
        }
        for a in items
    ], total, page, page_size)


@router.post("/applicants", response_model=dict)
async def create_applicant(
    data: ApplicantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ApplicantService(db)
    
    existing = await service.get_by_phone(data.phone)
    if existing:
        from app.core.exceptions import ConflictException
        raise ConflictException("该手机号已报名")
    
    applicant = await service.create(data.model_dump())
    return success({"id": str(applicant.id)}, "报名信息提交成功")


@router.put("/applicants/{applicant_id}/status", response_model=dict)
async def update_applicant_status(
    applicant_id: UUID,
    status: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ApplicantService(db)
    applicant = await service.update_status(applicant_id, status)
    
    if not applicant:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("报名信息不存在")
    
    return success(message="状态更新成功")


@router.post("/applicants/{applicant_id}/follow-up", response_model=dict)
async def add_follow_up(
    applicant_id: UUID,
    data: FollowUpCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FollowUpService(db)
    follow_up = await service.add_follow_up(applicant_id, current_user.id, data.model_dump())
    return success({"id": str(follow_up.id)}, "跟进记录添加成功")


@router.get("/applicants/{applicant_id}/follow-ups", response_model=dict)
async def get_follow_ups(
    applicant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = FollowUpService(db)
    follow_ups = await service.get_by_applicant(applicant_id)
    
    return success([
        {
            "id": str(f.id),
            "follow_type": f.follow_type,
            "content": f.content,
            "next_follow_date": f.next_follow_date.isoformat() if f.next_follow_date else None,
            "created_at": f.created_at.isoformat(),
        }
        for f in follow_ups
    ])


@router.get("/stats", response_model=dict)
async def get_recruitment_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.recruitment import Applicant
    
    pending_result = await db.execute(
        select(func.count()).select_from(Applicant).where(Applicant.status == "pending")
    )
    contacted_result = await db.execute(
        select(func.count()).select_from(Applicant).where(Applicant.status == "contacted")
    )
    interviewed_result = await db.execute(
        select(func.count()).select_from(Applicant).where(Applicant.status == "interviewed")
    )
    admitted_result = await db.execute(
        select(func.count()).select_from(Applicant).where(Applicant.status == "admitted")
    )
    
    return success({
        "pending": pending_result.scalar(),
        "contacted": contacted_result.scalar(),
        "interviewed": interviewed_result.scalar(),
        "admitted": admitted_result.scalar(),
    })
