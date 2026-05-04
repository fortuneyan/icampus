"""
智能排课模块 Pydantic Schemas
"""

from typing import Optional, List
from datetime import date, time, datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class ConstraintType(str, Enum):
    """约束类型"""
    HARD = "HARD"  # 硬约束（必须满足）
    SOFT = "SOFT"  # 软约束（尽量满足）


class CreateType(str, Enum):
    """创建类型"""
    MANUAL = "manual"  # 手动
    AUTO_FILL = "auto_fill"  # 自动填充
    AI_OPTIMIZE = "ai_optimize"  # AI优化


class PatchType(str, Enum):
    """调课类型"""
    SWAP = "swap"  # 换课
    SUBSTITUTE = "substitute"  # 代课
    CANCEL = "cancel"  # 停课
    SELF_STUDY = "self_study"  # 转自习


class EventType(str, Enum):
    """事件类型"""
    SPORTS_MEET = "sports_meet"  # 运动会
    EXCURSION = "excursion"  # 春游/研学
    EXAM = "exam"  # 考试
    ORIENTATION = "orientation"  # 入学教育
    CUSTOM = "custom"  # 自定义


# ============ 学期相关 ============

class SemesterBase(BaseModel):
    """学期基础Schema"""
    name: str = Field(..., max_length=50)
    academic_year: str = Field(..., max_length=9)
    semester: int = Field(..., ge=1, le=2)
    start_date: date
    end_date: date


class SemesterCreate(SemesterBase):
    """创建学期"""
    pass


class SemesterUpdate(BaseModel):
    """更新学期"""
    name: Optional[str] = Field(None, max_length=50)
    academic_year: Optional[str] = Field(None, max_length=9)
    semester: Optional[int] = Field(None, ge=1, le=2)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None


class SemesterResponse(SemesterBase):
    """学期响应"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    created_at: datetime


# ============ 周次组合 ============

class CycleBase(BaseModel):
    """周次组合基础Schema"""
    id: str = Field(..., max_length=32)
    semester_id: str
    start_date: date
    end_date: date
    cycle_type: str = "regular"


class CycleCreate(CycleBase):
    """创建周次组合"""
    pass


class CycleUpdate(BaseModel):
    """更新周次组合"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None
    cycle_type: Optional[str] = None
    remark: Optional[str] = None


class CycleResponse(CycleBase):
    """周次组合响应"""
    model_config = ConfigDict(from_attributes=True)

    is_current: bool
    remark: Optional[str] = None
    created_at: datetime


# ============ 日历映射 ============

class CalendarMapBase(BaseModel):
    """日历映射基础Schema"""
    natural_date: date
    cycle_id: str
    exec_day: int = Field(..., ge=1, le=7)
    is_workday: bool = True
    is_holiday: bool = False


class CalendarMapCreate(CalendarMapBase):
    """创建日历映射"""
    pass


class CalendarMapBatchCreate(BaseModel):
    """批量创建日历映射"""
    items: List[CalendarMapCreate]


class CalendarMapUpdate(BaseModel):
    """更新日历映射"""
    cycle_id: Optional[str] = None
    exec_day: Optional[int] = Field(None, ge=1, le=7)
    is_workday: Optional[bool] = None
    is_holiday: Optional[bool] = None
    remark: Optional[str] = None


class CalendarMapResponse(CalendarMapBase):
    """日历映射响应"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    remark: Optional[str] = None
    created_at: datetime


class CalendarMapQuery(BaseModel):
    """查询日历映射"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_holiday: Optional[bool] = None


# ============ 课表模板 ============

class TemplateBase(BaseModel):
    """课表模板基础Schema"""
    semester_id: str
    name: str = Field(..., max_length=50)
    template_type: str = "regular"


class TemplateCreate(TemplateBase):
    """创建课表模板"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    priority: int = 0


class TemplateUpdate(BaseModel):
    """更新课表模板"""
    name: Optional[str] = Field(None, max_length=50)
    template_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


class TemplateResponse(TemplateBase):
    """课表模板响应"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    priority: int
    is_active: bool
    remark: Optional[str] = None
    created_at: datetime


# ============ 节次 ============

class PeriodBase(BaseModel):
    """节次基础Schema"""
    period_index: int = Field(..., ge=1, le=15)
    start_time: str = Field(..., max_length=5)
    end_time: str = Field(..., max_length=5)
    period_type: str = "normal"


class PeriodCreate(PeriodBase):
    """创建节次"""
    template_id: UUID
    duration: int = 45


class PeriodUpdate(BaseModel):
    """更新节次"""
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    period_type: Optional[str] = None
    duration: Optional[int] = None


class PeriodResponse(PeriodBase):
    """节次响应"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    template_id: UUID
    duration: int
    remark: Optional[str] = None


# ============ 课程规划 ============

class PlanBase(BaseModel):
    """课程规划基础Schema"""
    cycle_id: str
    class_id: UUID
    teacher_id: UUID
    course_id: UUID
    total_hours: int = Field(..., ge=1)


class PlanCreate(PlanBase):
    """创建课程规划"""
    is_continuous: bool = False
    continuous_length: int = 1
    priority: int = 0


class PlanBatchCreate(BaseModel):
    """批量创建课程规划"""
    items: List[PlanCreate]


class PlanUpdate(BaseModel):
    """更新课程规划"""
    teacher_id: Optional[UUID] = None
    course_id: Optional[UUID] = None
    total_hours: Optional[int] = None
    is_continuous: Optional[bool] = None
    continuous_length: Optional[int] = None
    priority: Optional[int] = None


class PlanResponse(PlanBase):
    """课程规划响应"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_continuous: bool
    continuous_length: int
    priority: int
    remark: Optional[str] = None
    created_at: datetime


# ============ 排课结果 ============

class ResultBase(BaseModel):
    """排课结果基础Schema"""
    cycle_id: str
    class_id: UUID
    teacher_id: UUID
    course_id: UUID
    day_index: int = Field(..., ge=1, le=7)
    period_index: int = Field(..., ge=1, le=15)


class ResultCreate(ResultBase):
    """创建排课结果"""
    room_id: Optional[UUID] = None
    week_start: Optional[int] = None
    week_end: Optional[int] = None
    is_locked: bool = False
    create_type: str = "auto"
    template_id: Optional[UUID] = None


class ResultBatchCreate(BaseModel):
    """批量创建排课结果"""
    items: List[ResultCreate]


class ResultUpdate(BaseModel):
    """更新排课结果"""
    teacher_id: Optional[UUID] = None
    course_id: Optional[UUID] = None
    room_id: Optional[UUID] = None
    day_index: Optional[int] = Field(None, ge=1, le=7)
    period_index: Optional[int] = Field(None, ge=1, le=15)
    week_start: Optional[int] = None
    week_end: Optional[int] = None
    is_locked: Optional[bool] = None
    create_type: Optional[str] = None


class ResultResponse(ResultBase):
    """排课结果响应"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    room_id: Optional[UUID] = None
    week_start: Optional[int] = None
    week_end: Optional[int] = None
    is_locked: bool
    create_type: str
    template_id: Optional[UUID] = None
    remark: Optional[str] = None
    created_at: datetime


class ResultQuery(BaseModel):
    """查询排课结果"""
    cycle_id: Optional[str] = None
    class_id: Optional[UUID] = None
    teacher_id: Optional[UUID] = None
    course_id: Optional[UUID] = None
    day_index: Optional[int] = None
    template_id: Optional[UUID] = None


# ============ 调课补丁 ============

class PatchBase(BaseModel):
    """调课补丁基础Schema"""
    natural_date: date
    class_id: UUID
    day_index: int = Field(..., ge=1, le=7)
    period_index: int = Field(..., ge=1, le=15)


class PatchCreate(PatchBase):
    """创建调课补丁"""
    original_teacher_id: Optional[UUID] = None
    patch_teacher_id: Optional[UUID] = None
    original_course_id: Optional[UUID] = None
    patch_course_id: Optional[UUID] = None
    original_room_id: Optional[UUID] = None
    patch_room_id: Optional[UUID] = None
    patch_type: str = "swap"
    reason: Optional[str] = None


class PatchUpdate(BaseModel):
    """更新调课补丁"""
    patch_teacher_id: Optional[UUID] = None
    patch_course_id: Optional[UUID] = None
    patch_room_id: Optional[UUID] = None
    patch_type: Optional[str] = None
    status: Optional[str] = None
    reason: Optional[str] = None
    approver_id: Optional[UUID] = None


class PatchResponse(PatchBase):
    """调课补丁响应"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_teacher_id: Optional[UUID] = None
    patch_teacher_id: Optional[UUID] = None
    original_course_id: Optional[UUID] = None
    patch_course_id: Optional[UUID] = None
    original_room_id: Optional[UUID] = None
    patch_room_id: Optional[UUID] = None
    patch_type: str
    status: str
    reason: Optional[str] = None
    applicant_id: Optional[UUID] = None
    approver_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    remark: Optional[str] = None
    created_at: datetime


class PatchQuery(BaseModel):
    """查询调课补丁"""
    natural_date: Optional[date] = None
    class_id: Optional[UUID] = None
    original_teacher_id: Optional[UUID] = None
    status: Optional[str] = None


# ============ 约束 ============

class ConstraintBase(BaseModel):
    """约束基础Schema"""
    constraint_type: ConstraintType
    name: str = Field(..., max_length=100)
    description: Optional[str] = None


class ConstraintCreate(ConstraintBase):
    """创建约束"""
    semester_id: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[UUID] = None
    day_index: Optional[int] = Field(None, ge=1, le=7)
    period_start: Optional[int] = Field(None, ge=1, le=15)
    period_end: Optional[int] = Field(None, ge=1, le=15)
    priority: int = 0


class ConstraintUpdate(BaseModel):
    """更新约束"""
    constraint_type: Optional[ConstraintType] = None
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    day_index: Optional[int] = Field(None, ge=1, le=7)
    period_start: Optional[int] = Field(None, ge=1, le=15)
    period_end: Optional[int] = Field(None, ge=1, le=15)
    is_active: Optional[bool] = None
    priority: Optional[int] = None


class ConstraintResponse(ConstraintBase):
    """约束响应"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    semester_id: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[UUID] = None
    day_index: Optional[int] = None
    period_start: Optional[int] = None
    period_end: Optional[int] = None
    is_active: bool
    priority: int
    created_at: datetime


# ============ 批量事件 ============

class EventBase(BaseModel):
    """事件基础Schema"""
    semester_id: str
    name: str = Field(..., max_length=100)
    event_type: EventType
    start_date: date
    end_date: date


class EventCreate(EventBase):
    """创建事件"""
    scope: str = "all"
    target_grade_id: Optional[UUID] = None
    target_class_id: Optional[UUID] = None
    affect_schedule: bool = True


class EventUpdate(BaseModel):
    """更新事件"""
    name: Optional[str] = Field(None, max_length=100)
    event_type: Optional[EventType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    scope: Optional[str] = None
    target_grade_id: Optional[UUID] = None
    target_class_id: Optional[UUID] = None
    affect_schedule: Optional[bool] = None
    status: Optional[str] = None


class EventResponse(EventBase):
    """事件响应"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scope: str
    target_grade_id: Optional[UUID] = None
    target_class_id: Optional[UUID] = None
    affect_schedule: bool
    status: str
    remark: Optional[str] = None
    created_at: datetime


# ============ 长期代课 ============

class ReplaceBase(BaseModel):
    """代课替换基础Schema"""
    original_teacher_id: UUID
    replace_teacher_id: UUID
    start_date: date
    end_date: date


class ReplaceCreate(ReplaceBase):
    """创建代课替换"""
    course_id: Optional[UUID] = None
    semester_id: Optional[str] = None
    reason: Optional[str] = None


class ReplaceUpdate(BaseModel):
    """更新代课替换"""
    replace_teacher_id: Optional[UUID] = None
    course_id: Optional[UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    reason: Optional[str] = None
    status: Optional[str] = None


class ReplaceResponse(ReplaceBase):
    """代课替换响应"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: Optional[UUID] = None
    semester_id: Optional[str] = None
    reason: Optional[str] = None
    status: str
    created_at: datetime


# ============ 智能排课计划 ============

class SchedulingPlanCreate(BaseModel):
    """创建智能排课计划"""
    name: str = Field(..., max_length=100)
    semester_id: str
    cycle_id: str
    description: Optional[str] = None


class SchedulingPlanUpdate(BaseModel):
    """更新智能排课计划"""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    status: Optional[str] = None


class SchedulingPlanResponse(BaseModel):
    """智能排课计划响应"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    semester_id: str
    cycle_id: str
    description: Optional[str] = None
    status: str
    score: float = 0.0
    created_at: datetime
    updated_at: datetime


# ============ 课表视图 ============

class ScheduleCell(BaseModel):
    """课表单元格"""
    result_id: Optional[UUID] = None
    course_id: Optional[UUID] = None
    course_name: str = ""
    teacher_id: Optional[UUID] = None
    teacher_name: str = ""
    room_id: Optional[UUID] = None
    room_name: str = ""
    is_locked: bool = False
    create_type: str = ""


class DaySchedule(BaseModel):
    """一天的课表"""
    day_index: int
    day_name: str = ""
    periods: List[ScheduleCell] = []


class ClassScheduleResponse(BaseModel):
    """班级课表响应"""
    class_id: UUID
    class_name: str
    cycle_id: str
    days: List[DaySchedule] = []


class TeacherScheduleResponse(BaseModel):
    """教师课表响应"""
    teacher_id: UUID
    teacher_name: str
    cycle_id: str
    days: List[DaySchedule] = []


class RoomScheduleResponse(BaseModel):
    """教室课表响应"""
    room_id: UUID
    room_name: str
    cycle_id: str
    days: List[DaySchedule] = []


# ============ 冲突信息 ============

class ConflictInfo(BaseModel):
    """冲突信息"""
    conflict_type: str
    severity: int
    message: str
    related_ids: List[str] = []


class ConflictCheckResponse(BaseModel):
    """冲突检测响应"""
    has_conflicts: bool
    conflicts: List[ConflictInfo] = []


# ============ 优化结果 ============

class OptimizationResult(BaseModel):
    """优化结果"""
    success: bool
    score: float
    message: str
    changes_count: int = 0
    locked_count: int = 0


# ============ 拖拽调整 ============

class DragAdjustRequest(BaseModel):
    """拖拽调整请求"""
    result_id: UUID
    new_day_index: int = Field(..., ge=1, le=7)
    new_period_index: int = Field(..., ge=1, le=15)
    check_conflict: bool = True


class DragAdjustResponse(BaseModel):
    """拖拽调整响应"""
    success: bool
    message: str
    has_conflict: bool
    conflicts: List[ConflictInfo] = []
