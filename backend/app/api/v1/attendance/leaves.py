from typing import Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.student import Student
from app.schemas.leave import LeaveRequestCreate, LeaveRequestUpdate, LeaveApproval, LeaveQuotaCreate
from app.schemas.response import success, page_response
from app.services.leave_service import LeaveService, LeaveQuotaService

router = APIRouter()


def to_naive_datetime(dt: Optional[datetime]) -> Optional[datetime]:
    """将带时区的 datetime 转换为不带时区的 datetime"""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


@router.get("", response_model=dict)
async def get_leave_requests(
    student_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LeaveService(db)

    if student_id:
        result = await service.get_student_leaves(UUID(student_id), status=status)
        items = [
            {
                "id": str(l.id),
                "student_id": str(l.student_id),
                "leave_type": l.leave_type,
                "start_date": l.start_date.isoformat(),
                "end_date": l.end_date.isoformat(),
                "reason": l.reason,
                "status": l.status,
                "approver_id": str(l.approver_id) if l.approver_id else None,
                "approved_at": l.approved_at.isoformat() if l.approved_at else None,
                "approve_comment": l.approve_comment,
                "created_at": l.created_at.isoformat(),
            }
            for l in result["items"]
        ]
        return page_response(items, result["total"], page, page_size)
    else:
        result = await service.get_leaves_by_status(status or "pending", page, page_size)
        items = [
            {
                "id": str(l.id),
                "student_id": str(l.student_id),
                "leave_type": l.leave_type,
                "start_date": l.start_date.isoformat(),
                "end_date": l.end_date.isoformat(),
                "reason": l.reason,
                "status": l.status,
                "days": getattr(l, 'days', 0),
                "created_at": l.created_at.isoformat(),
            }
            for l in result["items"]
        ]
        return page_response(items, result["total"], page, page_size)


@router.post("", response_model=dict)
async def create_leave_request(
    data: LeaveRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LeaveService(db)
    
    if not await service.check_quota(
        UUID(data.student_id),
        data.leave_type,
        (data.end_date - data.start_date).days + 1,
        data.start_date.year
    ):
        from app.core.exceptions import ConflictException
        raise ConflictException("请假天数超出可用额度")

    leave_data = data.model_dump()
    leave_data["start_date"] = to_naive_datetime(leave_data.get("start_date"))
    leave_data["end_date"] = to_naive_datetime(leave_data.get("end_date"))

    leave = await service.create_leave_request(leave_data)
    return success({"id": str(leave.id)}, "请假申请已提交")


@router.get("/{leave_id}", response_model=dict)
async def get_leave_request(
    leave_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LeaveService(db)
    leave = await service.get(leave_id)
    
    if not leave:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("请假申请不存在")
    
    return success({
        "id": str(leave.id),
        "student_id": str(leave.student_id),
        "leave_type": leave.leave_type,
        "start_date": leave.start_date.isoformat(),
        "end_date": leave.end_date.isoformat(),
        "reason": leave.reason,
        "status": leave.status,
        "approver_id": str(leave.approver_id) if leave.approver_id else None,
        "approved_at": leave.approved_at.isoformat() if leave.approved_at else None,
        "approve_comment": leave.approve_comment,
        "created_at": leave.created_at.isoformat(),
    })


@router.put("/{leave_id}/approve", response_model=dict)
async def approve_leave_request(
    leave_id: UUID,
    data: LeaveApproval,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LeaveService(db)
    leave = await service.approve_request(leave_id, current_user.id, data.status, data.approver_comment)
    
    if not leave:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("请假申请不存在")
    
    if data.status == "approved":
        days = (leave.end_date - leave.start_date).days + 1
        await service.use_quota(leave.student_id, leave.leave_type, days)
    
    return success(message=f"请假申请已{data.status}")


@router.get("/stats/summary", response_model=dict)
async def get_leave_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import select, func
    from app.models.leave import LeaveRequest
    
    pending_result = await db.execute(
        select(func.count()).select_from(LeaveRequest).where(LeaveRequest.status == "pending")
    )
    pending_count = pending_result.scalar()
    
    approved_result = await db.execute(
        select(func.count()).select_from(LeaveRequest).where(LeaveRequest.status == "approved")
    )
    approved_count = approved_result.scalar()
    
    rejected_result = await db.execute(
        select(func.count()).select_from(LeaveRequest).where(LeaveRequest.status == "rejected")
    )
    rejected_count = rejected_result.scalar()
    
    return success({
        "pending": pending_count,
        "approved": approved_count,
        "rejected": rejected_count
    })


@router.get("/quota", response_model=dict)
async def get_leave_quota(
    student_id: Optional[str] = Query(None),
    class_id: Optional[str] = Query(None),
    year: int = Query(datetime.now().year),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LeaveQuotaService(db)
    
    if student_id:
        quotas = await service.get_student_quota(UUID(student_id), year)
    elif class_id:
        quotas = await service.get_class_quota(UUID(class_id), year)
    else:
        return success([])
    
    items = [
        {
            "id": str(q.id),
            "leave_type": q.leave_type,
            "total_days": q.total_days,
            "used_days": q.used_days,
            "remaining_days": q.remaining_days,
        }
        for q in quotas
    ]
    return success(items)


@router.post("/quota", response_model=dict)
async def create_leave_quota(
    data: LeaveQuotaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LeaveQuotaService(db)
    quota = await service.create(data.model_dump())
    return success({"id": str(quota.id)}, "请假额度设置成功")