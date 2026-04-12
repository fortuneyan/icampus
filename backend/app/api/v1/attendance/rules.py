"""
考勤规则API接口
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime, time
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.attendance_rule import AttendanceRule
from app.schemas.response import success, page_response

router = APIRouter()


# ============== Pydantic Models ==============

class AttendanceRuleCreate(BaseModel):
    """创建考勤规则"""
    name: str = Field(..., max_length=100, description="规则名称")
    rule_type: str = Field(..., description="规则类型: student/teacher")
    check_in_start: str = Field(..., description="签到开始时间 HH:mm:ss")
    check_in_end: str = Field(..., description="签到结束时间 HH:mm:ss")
    check_out_start: str = Field(..., description="签退开始时间 HH:mm:ss")
    check_out_end: str = Field(..., description="签退结束时间 HH:mm:ss")
    late_threshold: int = Field(default=0, ge=0, le=120, description="迟到阈值(分钟)")
    early_leave_threshold: int = Field(default=0, ge=0, le=120, description="早退阈值(分钟)")
    absent_threshold: int = Field(default=0, ge=0, le=480, description="旷课阈值(分钟)")
    grace_period: int = Field(default=5, ge=0, le=30, description="宽限期(分钟)")
    description: Optional[str] = Field(None, description="规则描述")

    @field_validator('rule_type')
    @classmethod
    def validate_rule_type(cls, v):
        if v not in ['student', 'teacher']:
            raise ValueError('rule_type must be student or teacher')
        return v

    @field_validator('check_in_start', 'check_in_end', 'check_out_start', 'check_out_end')
    @classmethod
    def parse_time(cls, v):
        try:
            return datetime.strptime(v, "%H:%M:%S").time()
        except ValueError:
            try:
                return datetime.strptime(v, "%H:%M").time()
            except ValueError:
                raise ValueError(f'Invalid time format: {v}')


class AttendanceRuleUpdate(BaseModel):
    """更新考勤规则"""
    name: Optional[str] = Field(None, max_length=100)
    rule_type: Optional[str] = None
    check_in_start: Optional[str] = None
    check_in_end: Optional[str] = None
    check_out_start: Optional[str] = None
    check_out_end: Optional[str] = None
    late_threshold: Optional[int] = Field(None, ge=0, le=120)
    early_leave_threshold: Optional[int] = Field(None, ge=0, le=120)
    absent_threshold: Optional[int] = Field(None, ge=0, le=480)
    grace_period: Optional[int] = Field(None, ge=0, le=30)
    description: Optional[str] = None
    status: Optional[str] = None

    @field_validator('rule_type')
    @classmethod
    def validate_rule_type(cls, v):
        if v is not None and v not in ['student', 'teacher']:
            raise ValueError('rule_type must be student or teacher')
        return v


class StatusUpdate(BaseModel):
    """状态更新"""
    status: str = Field(..., description="状态: active/inactive")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v not in ['active', 'inactive']:
            raise ValueError('status must be active or inactive')
        return v


# ============== API Routes ==============

@router.get("", response_model=dict)
async def get_attendance_rules(
    rule_type: Optional[str] = Query(None, description="规则类型: student/teacher"),
    status: Optional[str] = Query(None, description="状态: active/inactive"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取考勤规则列表
    
    - rule_type: 规则类型筛选
    - status: 状态筛选
    - page: 页码
    - page_size: 每页数量
    """
    query = select(AttendanceRule).order_by(AttendanceRule.created_at.desc())

    # 应用筛选条件
    if rule_type:
        query = query.where(AttendanceRule.rule_type == rule_type)
    if status:
        query = query.where(AttendanceRule.status == status)

    # 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    rules = result.scalars().all()

    # 转换格式
    items = [rule.to_dict() for rule in rules]

    return page_response(items, total, page, page_size)


@router.get("/{rule_id}", response_model=dict)
async def get_attendance_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取考勤规则详情"""
    result = await db.execute(
        select(AttendanceRule).where(AttendanceRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="考勤规则不存在")

    return success(rule.to_dict())


@router.post("", response_model=dict)
async def create_attendance_rule(
    data: AttendanceRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建考勤规则"""
    # 验证时间逻辑
    if data.check_in_start >= data.check_in_end:
        raise HTTPException(status_code=400, detail="签到结束时间必须晚于签到开始时间")
    if data.check_out_start >= data.check_out_end:
        raise HTTPException(status_code=400, detail="签退结束时间必须晚于签退开始时间")

    # 创建规则
    rule = AttendanceRule(
        name=data.name,
        rule_type=data.rule_type,
        check_in_start=data.check_in_start,
        check_in_end=data.check_in_end,
        check_out_start=data.check_out_start,
        check_out_end=data.check_out_end,
        late_threshold=data.late_threshold,
        early_leave_threshold=data.early_leave_threshold,
        absent_threshold=data.absent_threshold,
        grace_period=data.grace_period,
        description=data.description,
        status="active",
    )

    db.add(rule)
    await db.commit()
    await db.refresh(rule)

    return success({"id": str(rule.id)}, "考勤规则创建成功")


@router.put("/{rule_id}", response_model=dict)
async def update_attendance_rule(
    rule_id: UUID,
    data: AttendanceRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新考勤规则"""
    result = await db.execute(
        select(AttendanceRule).where(AttendanceRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="考勤规则不存在")

    # 更新字段
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)

    await db.commit()
    await db.refresh(rule)

    return success({"id": str(rule.id)}, "考勤规则更新成功")


@router.delete("/{rule_id}", response_model=dict)
async def delete_attendance_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除考勤规则"""
    result = await db.execute(
        select(AttendanceRule).where(AttendanceRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()

    if rule:
        await db.delete(rule)
        await db.commit()

    return success(message="考勤规则删除成功")


@router.patch("/{rule_id}/status", response_model=dict)
async def update_rule_status(
    rule_id: UUID,
    data: StatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新规则状态"""
    result = await db.execute(
        select(AttendanceRule).where(AttendanceRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="考勤规则不存在")

    rule.status = data.status
    await db.commit()

    status_text = "启用" if data.status == "active" else "停用"
    return success(message=f"考勤规则{status_text}成功")
