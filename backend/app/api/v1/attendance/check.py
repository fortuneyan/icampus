"""
考勤管理接口
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.attendance import RuleCreate, RuleUpdate, CheckInRequest
from app.schemas.response import success, page_response
from app.services.attendance_service import RuleService, RecordService


# ==================== 请假相关 Schema ====================

class LeaveRequestCreate(BaseModel):
    """创建请假申请"""
    leave_type: str = Field(..., description="请假类型: personal/sick/other")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    reason: str = Field(..., min_length=1, max_length=500, description="请假原因")


class LeaveRequestResponse(BaseModel):
    """请假申请响应"""
    id: str
    leave_type: str
    start_date: str
    end_date: str
    reason: str
    status: str
    created_at: Optional[str] = None


class LeaveApproveRequest(BaseModel):
    """审批请假申请"""
    status: str = Field(..., description="审批状态: approved/rejected")
    comment: Optional[str] = Field(None, description="审批意见")

router = APIRouter()


@router.get("/rules", response_model=dict)
async def get_rules(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    service = RuleService(db)
    rules = await service.get_all([service.model.status == "active"])
    items = [
        {
            "id": str(r.id),
            "name": r.name,
            "check_in_start": str(r.check_in_start) if r.check_in_start else None,
            "check_in_end": str(r.check_in_end) if r.check_in_end else None,
            "location": r.location,
        }
        for r in rules
    ]
    return success(items)


@router.post("/rules", response_model=dict)
async def create_rule(
    data: RuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RuleService(db)
    rule = await service.create_rule(data.model_dump())
    return success({"id": str(rule.id)}, "创建成功")


@router.post("/check-in", response_model=dict)
async def check_in(
    data: CheckInRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RecordService(db)
    record = await service.check_in(
        current_user.id, data.rule_id, data.photo, data.location
    )
    return success(
        {"id": str(record.id), "check_in_time": record.check_in_time.isoformat()},
        "签到成功",
    )


@router.get("/records", response_model=dict)
async def get_records(
    page: int = Query(1),
    page_size: int = Query(20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取考勤记录列表"""
    service = RecordService(db)
    result = await service.get_user_records(current_user.id, page, page_size)
    
    items = [
        {
            "id": str(r.id),
            "user_name": current_user.real_name or current_user.username or "未知",
            "date": r.check_in_time.date().isoformat() if r.check_in_time else None,
            "check_in_time": r.check_in_time.isoformat() if r.check_in_time else None,
            "check_out_time": r.check_out_time.isoformat() if r.check_out_time else None,
            "attendance_type": r.status or "normal",
            "location": r.check_in_location,
            "status": r.status or "normal",
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in result["items"]
    ]
    return page_response(items, result["total"], page, page_size)


@router.get("/statistics", response_model=dict)
async def get_statistics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RecordService(db)
    start = (
        datetime.fromisoformat(start_date)
        if start_date
        else datetime.now() - timedelta(days=30)
    )
    end = datetime.fromisoformat(end_date) if end_date else datetime.now()
    stats = await service.get_statistics(current_user.id, start, end)
    return success(stats)


# ==================== 请假管理接口 ====================

# 模拟请假数据存储（实际应该使用数据库模型）
leave_requests_db: List[dict] = []


@router.post("/leave", response_model=dict, summary="创建请假申请")
async def create_leave(
    data: LeaveRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建请假申请"""
    leave_request = {
        "id": str(UUID(int=len(leave_requests_db) + 1)),
        "user_id": str(current_user.id),
        "leave_type": data.leave_type,
        "start_date": data.start_date.isoformat(),
        "end_date": data.end_date.isoformat(),
        "reason": data.reason,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
    }
    leave_requests_db.append(leave_request)
    return success({
        "id": leave_request["id"],
        "status": leave_request["status"]
    }, "请假申请已提交")


@router.get("/leave", response_model=dict, summary="获取请假列表")
async def get_leave_list(
    status: Optional[str] = Query(None, description="状态筛选: pending/approved/rejected"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的请假申请列表"""
    items = [
        {
            "id": r["id"],
            "leave_type": r["leave_type"],
            "start_date": r["start_date"],
            "end_date": r["end_date"],
            "reason": r["reason"],
            "status": r["status"],
            "created_at": r["created_at"],
        }
        for r in leave_requests_db
        if r["user_id"] == str(current_user.id) and (not status or r["status"] == status)
    ]
    total = len(items)
    # 分页
    start = (page - 1) * page_size
    end = start + page_size
    return page_response(items[start:end], total, page, page_size)


@router.put("/leave/{leave_id}/approve", response_model=dict, summary="审批请假申请")
async def approve_leave(
    leave_id: str,
    data: LeaveApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """审批请假申请（需要管理员权限）"""
    # 查找请假申请
    leave_request = None
    for r in leave_requests_db:
        if r["id"] == leave_id:
            leave_request = r
            break
    
    if not leave_request:
        raise HTTPException(status_code=404, detail="请假申请不存在")
    
    if leave_request["status"] != "pending":
        raise HTTPException(status_code=400, detail="该申请已处理")
    
    leave_request["status"] = data.status
    leave_request["approved_by"] = str(current_user.id)
    leave_request["approved_at"] = datetime.now().isoformat()
    if data.comment:
        leave_request["comment"] = data.comment
    
    return success({
        "id": leave_id,
        "status": data.status
    }, "审批完成")
