# -*- coding: utf-8 -*-
"""
选课规则模型
T6: 选课管理
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class SelectionPeriodType(str, Enum):
    """选课时段类型"""
    FIRST = "first"           # 第一轮选课
    SECOND = "second"        # 第二轮选课
    ADD = "add"               # 补选
    DROP = "drop"             # 退选


class SelectionMode(str, Enum):
    """选课模式"""
    CREDIT_BASED = "credit"      # 学分制选课
    COURSE_BASED = "course"       # 课程制选课
    LOTTERY = "lottery"           # 抽签制选课


class SelectionStrategy(str, Enum):
    """选课策略"""
    FIRST_COME_FIRST_SERVED = "fcfs"       # 先到先得
    PRIORITY = "priority"                     # 优先级选课
    RANDOM = "random"                         # 随机抽签
    WEIGHTED = "weighted"                     # 加权随机


class RuleStatus(str, Enum):
    """规则状态"""
    DRAFT = "draft"         # 草稿
    ACTIVE = "active"       # 生效中
    SUSPENDED = "suspended" # 已暂停
    EXPIRED = "expired"     # 已过期


class SelectionRule(BaseModel):
    """选课规则模型"""
    id: Optional[int] = None
    name: str = Field(..., description="规则名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="规则描述")

    # 学年学期
    academic_year: str = Field(..., description="学年", min_length=9, max_length=9)
    semester: int = Field(..., description="学期", ge=1, le=3)

    # 选课时段
    period_type: SelectionPeriodType = Field(..., description="选课时段类型")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")

    # 选课模式
    selection_mode: SelectionMode = Field(SelectionMode.COURSE_BASED, description="选课模式")

    # 选课策略
    strategy: SelectionStrategy = Field(SelectionStrategy.FIRST_COME_FIRST_SERVED,
                                         description="选课策略")

    # 学分限制
    min_credits: int = Field(0, description="最低学分要求", ge=0)
    max_credits: int = Field(50, description="最高学分限制", ge=0)
    default_credits: int = Field(25, description="默认学分", ge=0)

    # 课程限制
    min_courses: int = Field(0, description="最少选课数", ge=0)
    max_courses: int = Field(20, description="最多选课数", ge=0)

    # 互斥课程组（同一组内只能选一门）
    exclusive_groups: List[str] = Field(default_factory=list, description="互斥课程组")

    # 必修课程（不需要选课但自动入课）
    required_course_ids: List[int] = Field(default_factory=list, description="必修课程ID列表")

    # 年级限制
    allowed_grades: List[int] = Field(default_factory=list, description="允许选课的年级")

    # 班级限制
    allowed_class_ids: List[int] = Field(default_factory=list, description="允许选课的班级")

    # 冲突检测
    allow_conflicts: bool = Field(False, description="是否允许时间冲突")
    allow_overcapacity: bool = Field(False, description="是否允许超容量")

    # 权重配置（用于加权随机策略）
    priority_weights: Dict[str, float] = Field(default_factory=dict,
                                                 description="优先级权重配置")

    # 状态
    status: RuleStatus = Field(RuleStatus.DRAFT, description="规则状态")

    # 备注
    remarks: Optional[str] = Field(None, description="备注")

    created_by: Optional[int] = Field(None, description="创建人ID")
    updated_by: Optional[int] = Field(None, description="更新人ID")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True
        use_enum_values = True

    @field_validator('max_credits')
    @classmethod
    def validate_credits(cls, v: int, info) -> int:
        if 'min_credits' in info.data and v < info.data['min_credits']:
            raise ValueError('max_credits must be >= min_credits')
        return v

    @field_validator('end_time')
    @classmethod
    def validate_end_time(cls, v: datetime, info) -> datetime:
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('end_time must be after start_time')
        return v

    def is_active(self) -> bool:
        """检查规则是否生效"""
        now = datetime.now()
        return (self.status == RuleStatus.ACTIVE and
                self.start_time <= now <= self.end_time)

    def is_expired(self) -> bool:
        """检查规则是否过期"""
        return datetime.now() > self.end_time

    def get_available_period(self) -> Optional[Dict[str, Any]]:
        """获取可选时段信息"""
        now = datetime.now()
        if now < self.start_time:
            return {
                "status": "pending",
                "remaining_seconds": int((self.start_time - now).total_seconds())
            }
        elif now <= self.end_time:
            return {
                "status": "active",
                "remaining_seconds": int((self.end_time - now).total_seconds())
            }
        else:
            return {
                "status": "expired",
                "remaining_seconds": 0
            }

    def can_select(self, student_credits: int, course_count: int) -> tuple[bool, str]:
        """
        检查学生是否满足选课条件
        返回: (是否可以选课, 原因)
        """
        # 检查规则状态
        if not self.is_active():
            if self.is_expired():
                return False, "选课已结束"
            return False, "选课未开始"

        # 检查学分范围（学生当前学分是否满足最低要求）
        # 注意：第一次选课时student_credits为0，这是正常的
        # 只有当学生已选学分超过最大值时才拒绝
        if student_credits > self.max_credits:
            return False, f"学分超限，最多可选{self.max_credits}学分"

        # 检查课程数量
        if course_count >= self.max_courses:
            return False, f"课程数量已达上限，最多可选{self.max_courses}门"

        return True, "可以选课"

    def validate_conflict(self, existing_course_ids: List[int],
                         new_course_ids: List[int]) -> bool:
        """检查是否与已选课程冲突"""
        if self.allow_conflicts:
            return True

        # 检查互斥课程
        for group in self.exclusive_groups:
            # 实际实现需要检查课程是否属于同一互斥组
            existing_in_group = any(cid in group for cid in existing_course_ids)
            new_in_group = any(cid in group for cid in new_course_ids)
            if existing_in_group and new_in_group:
                return False

        return True

    def validate_required(self, student_id: int,
                          selected_course_ids: List[int]) -> List[int]:
        """获取需要自动添加的必修课程"""
        auto_add = []
        for course_id in self.required_course_ids:
            if course_id not in selected_course_ids:
                auto_add.append(course_id)
        return auto_add


class CourseCapacity(BaseModel):
    """课程容量配置"""
    course_id: int = Field(..., description="课程ID")
    max_capacity: int = Field(..., description="最大容量", ge=1)
    min_capacity: int = Field(1, description="最小开课容量", ge=1)
    current_count: int = Field(0, description="当前已选人数", ge=0)
    waitlist_count: int = Field(0, description="候补人数", ge=0)

    is_full: bool = Field(False, description="是否已满")
    can_add: bool = Field(True, description="是否可以加入")

    class Config:
        from_attributes = True

    def check_availability(self) -> tuple[bool, str]:
        """检查是否可以选课"""
        if self.current_count >= self.max_capacity:
            return False, "课程已满"
        return True, "可以选课"

    def check_waitlist(self) -> tuple[bool, str]:
        """检查是否可以加入候补"""
        total = self.current_count + self.waitlist_count
        if total >= self.max_capacity * 1.5:  # 候补最多50%
            return False, "候补队列已满"
        return True, "可以加入候补"


class SelectionPriority(BaseModel):
    """选课优先级"""
    student_id: int = Field(..., description="学生ID")
    course_id: int = Field(..., description="课程ID")
    priority: int = Field(1, description="优先级(数字越小优先级越高)", ge=1)

    # 优先级来源
    priority_type: str = Field("manual", description="优先级类型: manual/manual/auto")
    reason: Optional[str] = Field(None, description="优先级原因")

    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    class Config:
        from_attributes = True


class CourseConflict(BaseModel):
    """课程冲突信息"""
    course_id_1: int = Field(..., description="课程1 ID")
    course_id_2: int = Field(..., description="课程2 ID")
    conflict_type: str = Field(..., description="冲突类型: time/teacher/classroom")

    # 冲突详情
    time_slot_1: Optional[str] = Field(None, description="课程1时间槽")
    time_slot_2: Optional[str] = Field(None, description="课程2时间槽")
    day_of_week: Optional[int] = Field(None, description="星期几")
    period: Optional[int] = Field(None, description="第几节课")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "course_ids": [self.course_id_1, self.course_id_2],
            "conflict_type": self.conflict_type,
            "day_of_week": self.day_of_week,
            "period": self.period
        }
