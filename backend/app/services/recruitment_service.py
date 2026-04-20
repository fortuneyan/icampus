from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recruitment import RecruitmentPlan, Applicant, ApplicantFollowUp
from app.services.base_service import BaseService


class RecruitmentService(BaseService[RecruitmentPlan]):
    def __init__(self, db: AsyncSession):
        super().__init__(RecruitmentPlan, db)

    async def get_active_plans(self, year: int = None):
        query = select(RecruitmentPlan).where(RecruitmentPlan.status == "published")
        if year:
            query = query.where(RecruitmentPlan.year == year)
        result = await self.db.execute(query)
        return result.scalars().all()


class ApplicantService(BaseService[Applicant]):
    def __init__(self, db: AsyncSession):
        super().__init__(Applicant, db)

    async def get_by_phone(self, phone: str) -> Optional[Applicant]:
        result = await self.db.execute(
            select(Applicant).where(Applicant.phone == phone)
        )
        return result.scalar_one_or_none()

    async def get_by_status(self, status: str, page: int = 1, page_size: int = 20):
        query = (
            select(Applicant)
            .where(Applicant.status == status)
            .order_by(Applicant.created_at.desc())
        )
        result = await self.db.execute(query)
        applicants = result.scalars().all()
        
        total = len(applicants)
        offset = (page - 1) * page_size
        items = applicants[offset:offset + page_size]
        
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    async def update_status(self, applicant_id: UUID, status: str):
        applicant = await self.get(applicant_id)
        if applicant:
            applicant.status = status
            applicant.updated_at = datetime.now()
            await self.db.commit()
            await self.db.refresh(applicant)
        return applicant


class FollowUpService(BaseService[ApplicantFollowUp]):
    def __init__(self, db: AsyncSession):
        super().__init__(ApplicantFollowUp, db)

    async def get_by_applicant(self, applicant_id: UUID) -> List[ApplicantFollowUp]:
        result = await self.db.execute(
            select(ApplicantFollowUp)
            .where(ApplicantFollowUp.applicant_id == applicant_id)
            .order_by(ApplicantFollowUp.created_at.desc())
        )
        return result.scalars().all()

    async def add_follow_up(self, applicant_id: UUID, operator_id: UUID, data: dict) -> ApplicantFollowUp:
        follow_up = ApplicantFollowUp(
            applicant_id=applicant_id,
            operator_id=operator_id,
            follow_type=data.get("follow_type"),
            content=data.get("content"),
            next_follow_date=data.get("next_follow_date")
        )
        self.db.add(follow_up)
        await self.db.commit()
        await self.db.refresh(follow_up)
        return follow_up
