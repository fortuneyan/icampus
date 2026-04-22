from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.leave import LeaveRequest, LeaveQuota
from app.models.student import Student
from app.models.user import User
from app.services.base_service import BaseService


class LeaveService(BaseService[LeaveRequest]):
    def __init__(self, db: AsyncSession):
        super().__init__(LeaveRequest, db)

    async def create_leave_request(self, data: dict) -> LeaveRequest:
        data["status"] = "pending"
        return await self.create(data)

    async def approve_request(self, request_id: UUID, approver_id: UUID, status: str, comment: str = None) -> Optional[LeaveRequest]:
        request = await self.get(request_id)
        if request:
            request.status = status
            request.approver_id = approver_id
            request.approved_at = datetime.utcnow()
            request.approve_comment = comment
            await self.db.commit()
            await self.db.refresh(request)
        return request

    async def get_student_leaves(self, student_id: UUID, status: Optional[str] = None) -> dict:
        query = select(LeaveRequest).where(LeaveRequest.student_id == student_id)
        if status:
            query = query.where(LeaveRequest.status == status)
        query = query.order_by(LeaveRequest.created_at.desc())
        result = await self.db.execute(query)
        leaves = result.scalars().all()

        return {
            "items": leaves,
            "total": len(leaves)
        }

    async def get_user_leaves(self, user_id: UUID, status: Optional[str] = None) -> dict:
        query = select(LeaveRequest).where(LeaveRequest.user_id == user_id)
        if status:
            query = query.where(LeaveRequest.status == status)
        query = query.order_by(LeaveRequest.created_at.desc())
        result = await self.db.execute(query)
        leaves = result.scalars().all()

        return {
            "items": leaves,
            "total": len(leaves)
        }

    async def get_pending_leaves(self, page: int = 1, page_size: int = 20) -> dict:
        return await self.get_leaves_by_status("pending", page, page_size)

    async def get_leaves_by_status(self, status: str, page: int = 1, page_size: int = 20) -> dict:
        query = (
            select(LeaveRequest)
            .where(LeaveRequest.status == status)
            .order_by(LeaveRequest.created_at.desc())
        )
        result = await self.db.execute(query)
        leaves = result.scalars().all()

        total = len(leaves)
        offset = (page - 1) * page_size
        items = leaves[offset:offset + page_size]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def check_quota(self, student_id: UUID, leave_type: str, days: int, year: int) -> bool:
        result = await self.db.execute(
            select(LeaveQuota).where(
                and_(
                    LeaveQuota.student_id == student_id,
                    LeaveQuota.leave_type == leave_type,
                    LeaveQuota.year == year,
                    LeaveQuota.status == "active"
                )
            )
        )
        quota = result.scalar_one_or_none()
        
        if not quota:
            return True
        
        return quota.remaining_days >= days

    async def use_quota(self, student_id: UUID, leave_type: str, days: int) -> bool:
        result = await self.db.execute(
            select(LeaveQuota).where(
                and_(
                    LeaveQuota.student_id == student_id,
                    LeaveQuota.leave_type == leave_type,
                    LeaveQuota.status == "active"
                )
            )
        )
        quota = result.scalar_one_or_none()
        
        if quota:
            quota.used_days = (quota.used_days or 0) + days
            await self.db.commit()
            return True
        return False


class LeaveQuotaService(BaseService[LeaveQuota]):
    def __init__(self, db: AsyncSession):
        super().__init__(LeaveQuota, db)

    async def get_student_quota(self, student_id: UUID, year: int) -> List[LeaveQuota]:
        result = await self.db.execute(
            select(LeaveQuota).where(
                and_(
                    LeaveQuota.student_id == student_id,
                    LeaveQuota.year == year,
                    LeaveQuota.status == "active"
                )
            )
        )
        return result.scalars().all()

    async def get_class_quota(self, class_id: UUID, year: int) -> List[LeaveQuota]:
        result = await self.db.execute(
            select(LeaveQuota).where(
                and_(
                    LeaveQuota.class_id == class_id,
                    LeaveQuota.year == year,
                    LeaveQuota.status == "active"
                )
            )
        )
        return result.scalars().all()