# -*- coding: utf-8 -*-
"""
选课管理API
T6: 选课管理
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/course-selection", tags=["选课管理"])

# ==================== 请求模型 ====================

class SelectionRequest(BaseModel):
    """选课请求"""
    student_id: int = Field(..., description="学生ID")
    course_id: int = Field(..., description="课程ID")
    rule_id: int = Field(..., description="选课规则ID")
    credits: float = Field(..., description="学分", ge=0)


class BatchSelectionRequest(BaseModel):
    """批量选课请求"""
    student_id: int = Field(..., description="学生ID")
    course_ids: List[tuple[int, float]] = Field(..., description="课程ID和学分列表")
    rule_id: int = Field(..., description="选课规则ID")


class WithdrawRequest(BaseModel):
    """撤选请求"""
    record_id: int = Field(..., description="选课记录ID")
    student_id: int = Field(..., description="学生ID")


class DropRequest(BaseModel):
    """退选请求"""
    record_id: int = Field(..., description="选课记录ID")
    student_id: int = Field(..., description="学生ID")
    reason: Optional[str] = Field(None, description="退选原因")


class RuleCreateRequest(BaseModel):
    """创建选课规则请求"""
    name: str = Field(..., description="规则名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="规则描述")

    academic_year: str = Field(..., description="学年", pattern=r"^\d{4}-\d{4}$")
    semester: int = Field(..., description="学期", ge=1, le=3)

    period_type: str = Field(..., description="选课时段类型")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")

    selection_mode: str = Field("course", description="选课模式")
    strategy: str = Field("fcfs", description="选课策略")

    min_credits: int = Field(0, description="最低学分", ge=0)
    max_credits: int = Field(50, description="最高学分", ge=0)
    default_credits: int = Field(25, description="默认学分", ge=0)

    min_courses: int = Field(0, description="最少选课数", ge=0)
    max_courses: int = Field(20, description="最多选课数", ge=0)

    exclusive_groups: List[str] = Field(default_factory=list, description="互斥课程组")
    required_course_ids: List[int] = Field(default_factory=list, description="必修课程")
    allowed_grades: List[int] = Field(default_factory=list, description="允许年级")
    allowed_class_ids: List[int] = Field(default_factory=list, description="允许班级")

    allow_conflicts: bool = Field(False, description="允许时间冲突")
    allow_overcapacity: bool = Field(False, description="允许超容量")


class LotteryRequest(BaseModel):
    """抽签请求"""
    course_id: int = Field(..., description="课程ID")
    max_capacity: int = Field(..., description="最大容量", ge=1)


# ==================== 响应模型 ====================

class SelectionResponse(BaseModel):
    """选课响应"""
    success: bool
    record_id: Optional[int] = None
    status: str
    message: str
    waitlist_position: Optional[int] = None


class RuleResponse(BaseModel):
    """规则响应"""
    id: int
    name: str
    academic_year: str
    semester: int
    period_type: str
    start_time: datetime
    end_time: datetime
    selection_mode: str
    strategy: str
    status: str
    min_credits: int
    max_credits: int
    current_count: Optional[int] = None
    is_active: Optional[bool] = None


class StudentSummaryResponse(BaseModel):
    """学生选课汇总响应"""
    student_id: int
    academic_year: str
    semester: int
    total_courses: int
    approved_courses: int
    pending_courses: int
    waitlisted_courses: int
    total_credits: float
    approved_credits: float
    selection_complete: bool
    warnings: List[str]


class CourseSelectionListResponse(BaseModel):
    """课程选课名单响应"""
    course_id: int
    course_name: Optional[str]
    total: int
    approved: int
    pending: int
    waitlisted: int
    rejected: int
    records: List[dict]


class ReportResponse(BaseModel):
    """选课报表响应"""
    academic_year: str
    semester: int
    total_courses: int
    total_students: int
    total_selections: int
    total_approved: int
    popular_courses: List[dict]
    low_demand_courses: List[dict]
    class_stats: List[dict]
    generated_at: datetime


# ==================== API路由 ====================

# 模拟数据存储
_mock_rules = {}
_mock_records = {}
_mock_service = None


def get_service():
    """获取服务实例"""
    global _mock_service
    if _mock_service is None:
        from app.services.course_selection_service import CourseSelectionService
        _mock_service = CourseSelectionService()

        # 添加模拟规则
        from app.models.course_selection_rule import SelectionRule, SelectionPeriodType, SelectionMode, SelectionStrategy, RuleStatus

        rule = SelectionRule(
            id=1,
            name="2026学年第一学期选课",
            academic_year="2025-2026",
            semester=1,
            period_type=SelectionPeriodType.FIRST,
            start_time=datetime(2025, 12, 1, 9, 0),
            end_time=datetime(2025, 12, 15, 23, 59),
            selection_mode=SelectionMode.COURSE_BASED,
            strategy=SelectionStrategy.FIRST_COME_FIRST_SERVED,
            min_credits=15,
            max_credits=30,
            default_credits=25,
            min_courses=5,
            max_courses=10,
            status=RuleStatus.ACTIVE
        )
        _mock_service.rules[1] = rule

    return _mock_service


# ==================== 规则管理 ====================

@router.post("/rules", response_model=RuleResponse)
async def create_rule(req: RuleCreateRequest):
    """创建选课规则"""
    service = get_service()

    from app.models.course_selection_rule import SelectionPeriodType, SelectionMode, SelectionStrategy

    rule_data = req.model_dump()
    rule_data["period_type"] = SelectionPeriodType(rule_data["period_type"])
    rule_data["selection_mode"] = SelectionMode(rule_data["selection_mode"])
    rule_data["strategy"] = SelectionStrategy(rule_data["strategy"])

    success, rule, msg = service.create_rule(rule_data)

    if not success:
        raise HTTPException(status_code=400, detail=msg)

    return RuleResponse(
        id=rule.id,
        name=rule.name,
        academic_year=rule.academic_year,
        semester=rule.semester,
        period_type=rule.period_type,
        start_time=rule.start_time,
        end_time=rule.end_time,
        selection_mode=rule.selection_mode,
        strategy=rule.strategy,
        status=rule.status,
        min_credits=rule.min_credits,
        max_credits=rule.max_credits
    )


@router.get("/rules", response_model=List[RuleResponse])
async def list_rules(
    academic_year: Optional[str] = Query(None, description="学年"),
    semester: Optional[int] = Query(None, description="学期"),
    status: Optional[str] = Query(None, description="状态")
):
    """获取选课规则列表"""
    service = get_service()
    rules = list(service.rules.values())

    if academic_year:
        rules = [r for r in rules if r.academic_year == academic_year]
    if semester:
        rules = [r for r in rules if r.semester == semester]
    if status:
        rules = [r for r in rules if r.status == status]

    return [
        RuleResponse(
            id=r.id,
            name=r.name,
            academic_year=r.academic_year,
            semester=r.semester,
            period_type=r.period_type,
            start_time=r.start_time,
            end_time=r.end_time,
            selection_mode=r.selection_mode,
            strategy=r.strategy,
            status=r.status,
            min_credits=r.min_credits,
            max_credits=r.max_credits,
            is_active=r.is_active()
        )
        for r in rules
    ]


@router.get("/rules/active", response_model=RuleResponse)
async def get_active_rule(
    academic_year: str = Query(..., description="学年"),
    semester: int = Query(..., description="学期")
):
    """获取当前生效的选课规则"""
    service = get_service()
    rule = service.get_active_rule(academic_year, semester)

    if not rule:
        raise HTTPException(status_code=404, detail="当前没有生效的选课规则")

    return RuleResponse(
        id=rule.id,
        name=rule.name,
        academic_year=rule.academic_year,
        semester=rule.semester,
        period_type=rule.period_type,
        start_time=rule.start_time,
        end_time=rule.end_time,
        selection_mode=rule.selection_mode,
        strategy=rule.strategy,
        status=rule.status,
        min_credits=rule.min_credits,
        max_credits=rule.max_credits,
        is_active=rule.is_active()
    )


# ==================== 选课操作 ====================

@router.post("/select", response_model=SelectionResponse)
async def select_course(req: SelectionRequest):
    """选课"""
    service = get_service()

    success, record, msg = service.select_course(
        student_id=req.student_id,
        course_id=req.course_id,
        rule_id=req.rule_id,
        credits=req.credits,
        student_info={
            "name": f"Student {req.student_id}",
            "class": f"Class {(req.student_id - 1) % 10 + 1}"
        }
    )

    return SelectionResponse(
        success=success,
        record_id=record.id if record else None,
        status=record.status if record else "failed",
        message=msg,
        waitlist_position=record.waitlist_position if record else None
    )


@router.post("/withdraw", response_model=dict)
async def withdraw_course(req: WithdrawRequest):
    """撤选课程"""
    service = get_service()

    success, msg = service.withdraw_course(req.record_id, req.student_id)

    if not success:
        raise HTTPException(status_code=400, detail=msg)

    return {"success": True, "message": msg}


@router.post("/drop", response_model=dict)
async def drop_course(req: DropRequest):
    """退选课程"""
    service = get_service()

    success, msg = service.drop_course(req.record_id, req.student_id, req.reason)

    if not success:
        raise HTTPException(status_code=400, detail=msg)

    return {"success": True, "message": msg}


@router.post("/batch-select", response_model=dict)
async def batch_select(req: BatchSelectionRequest):
    """批量选课"""
    service = get_service()

    results = service.batch_select(
        student_id=req.student_id,
        course_ids=req.course_ids,
        rule_id=req.rule_id,
        student_info={"name": f"Student {req.student_id}"}
    )

    return {
        "success": len(results["success"]),
        "failed": len(results["failed"]),
        "waitlisted": len(results["waitlisted"]),
        "details": results
    }


# ==================== 查询功能 ====================

@router.get("/student/{student_id}", response_model=List[dict])
async def get_student_records(
    student_id: int,
    academic_year: Optional[str] = Query(None, description="学年"),
    semester: Optional[int] = Query(None, description="学期")
):
    """获取学生选课记录"""
    service = get_service()
    records = service.get_student_records(student_id, academic_year, semester)

    return [
        {
            "id": r.id,
            "student_id": r.student_id,
            "student_name": r.student_name,
            "course_id": r.course_id,
            "course_name": r.course_name,
            "status": r.status,
            "credits": r.credits,
            "selected_at": r.selected_at.isoformat() if r.selected_at else None,
            "waitlist_position": r.waitlist_position
        }
        for r in records
    ]


@router.get("/student/{student_id}/summary", response_model=StudentSummaryResponse)
async def get_student_summary(
    student_id: int,
    academic_year: str = Query(..., description="学年"),
    semester: int = Query(..., description="学期")
):
    """获取学生选课汇总"""
    service = get_service()
    summary = service.get_student_summary(student_id, academic_year, semester)

    return StudentSummaryResponse(
        student_id=summary.student_id,
        academic_year=summary.academic_year,
        semester=summary.semester,
        total_courses=summary.total_courses,
        approved_courses=summary.approved_courses,
        pending_courses=summary.pending_courses,
        waitlisted_courses=summary.waitlisted_courses,
        total_credits=summary.total_credits,
        approved_credits=summary.approved_credits,
        selection_complete=summary.selection_complete,
        warnings=summary.warnings
    )


@router.get("/course/{course_id}/students", response_model=CourseSelectionListResponse)
async def get_course_selection_list(
    course_id: int,
    status: Optional[str] = Query(None, description="筛选状态")
):
    """获取课程选课名单"""
    service = get_service()
    records = service.get_course_selection_list(course_id)

    if status:
        records = [r for r in records if r.status == status]

    return CourseSelectionListResponse(
        course_id=course_id,
        course_name=records[0].course_name if records else None,
        total=len(records),
        approved=len([r for r in records if r.status == "approved"]),
        pending=len([r for r in records if r.status == "pending"]),
        waitlisted=len([r for r in records if r.status == "waitlisted"]),
        rejected=len([r for r in records if r.status == "rejected"]),
        records=[
            {
                "id": r.id,
                "student_id": r.student_id,
                "student_name": r.student_name,
                "status": r.status,
                "credits": r.credits,
                "selected_at": r.selected_at.isoformat() if r.selected_at else None
            }
            for r in records
        ]
    )


# ==================== 候补管理 ====================

@router.get("/waitlist/{course_id}/position")
async def get_waitlist_position(
    course_id: int,
    student_id: int = Query(..., description="学生ID")
):
    """获取候补位置"""
    service = get_service()
    position = service.get_waitlist_position(student_id, course_id)

    if position is None:
        raise HTTPException(status_code=404, detail="不在候补队列中")

    return {"course_id": course_id, "student_id": student_id, "position": position}


# ==================== 抽签系统 ====================

@router.post("/lottery")
async def conduct_lottery(req: LotteryRequest):
    """执行抽签"""
    service = get_service()

    result = service.conduct_lottery(req.course_id, req.max_capacity)

    return {
        "lottery_id": result.lottery_id,
        "course_id": result.course_id,
        "total_participants": result.total_participants,
        "winners_count": len(result.winners),
        "losers_count": len(result.losers),
        "winning_rate": result.get_winning_rate(),
        "status": result.status
    }


# ==================== 报表 ====================

@router.get("/report", response_model=ReportResponse)
async def get_selection_report(
    academic_year: str = Query(..., description="学年"),
    semester: int = Query(..., description="学期")
):
    """获取选课报表"""
    service = get_service()
    report = service.get_course_selection_report(academic_year, semester)

    return ReportResponse(
        academic_year=report.academic_year,
        semester=report.semester,
        total_courses=report.total_courses,
        total_students=report.total_students,
        total_selections=report.total_selections,
        total_approved=report.total_approved,
        popular_courses=report.popular_courses,
        low_demand_courses=report.low_demand_courses,
        class_stats=report.class_stats,
        generated_at=report.generated_at
    )


# ==================== 验证功能 ====================

@router.post("/validate")
async def validate_selection_plan(
    student_id: int,
    course_ids: List[int],
    rule_id: int
):
    """验证选课计划"""
    service = get_service()
    rule = service.rules.get(rule_id)

    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    valid, plan = service.validate_student_plan(student_id, course_ids, rule)

    return {
        "valid": valid,
        "total_credits": plan.total_credits,
        "course_count": len(plan.courses),
        "has_conflicts": plan.has_conflicts,
        "warnings": plan.warnings,
        "suggestions": plan.suggestions
    }
