# -*- coding: utf-8 -*-
"""
选课记录模型
T6: 选课管理
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class SelectionStatus(str, Enum):
    """选课状态"""
    PENDING = "pending"             # 待审核
    APPROVED = "approved"           # 已通过
    REJECTED = "rejected"           # 已拒绝
    WAITLISTED = "waitlisted"      # 候补中
    WITHDRAWN = "withdrawn"         # 已撤选
    DROPPED = "dropped"             # 已退选
    FAILED = "failed"              # 选课失败
    LOTTERY_PENDING = "lottery_pending"  # 等待抽签


class LotteryStatus(str, Enum):
    """抽签状态"""
    PENDING = "pending"       # 待抽签
    WINNING = "winning"       # 中签
    LOSING = "losing"          # 未中


class SelectionRecord(BaseModel):
    """选课记录模型"""
    id: Optional[int] = None
    student_id: int = Field(..., description="学生ID")
    student_name: Optional[str] = Field(None, description="学生姓名")
    student_class: Optional[str] = Field(None, description="学生班级")

    course_id: int = Field(..., description="课程ID")
    course_name: Optional[str] = Field(None, description="课程名称")
    course_code: Optional[str] = Field(None, description="课程代码")

    rule_id: int = Field(..., description="选课规则ID")
    academic_year: str = Field(..., description="学年")
    semester: int = Field(..., description="学期")

    # 选课状态
    status: SelectionStatus = Field(SelectionStatus.PENDING, description="选课状态")
    lottery_status: Optional[LotteryStatus] = Field(None, description="抽签状态")

    # 学分
    credits: float = Field(0, description="课程学分", ge=0)

    # 时间信息
    selected_at: datetime = Field(default_factory=datetime.now, description="选课时间")
    confirmed_at: Optional[datetime] = Field(None, description="确认时间")
    dropped_at: Optional[datetime] = Field(None, description="退选时间")

    # 原因
    reject_reason: Optional[str] = Field(None, description="拒绝原因")
    waitlist_position: Optional[int] = Field(None, description="候补位置")
    remarks: Optional[str] = Field(None, description="备注")

    # 操作信息
    operated_by: Optional[int] = Field(None, description="操作人ID")
    operated_at: Optional[datetime] = Field(None, description="操作时间")

    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True
        use_enum_values = True

    def is_active(self) -> bool:
        """检查是否有效选课"""
        return self.status == SelectionStatus.APPROVED

    def can_withdraw(self) -> bool:
        """检查是否可以撤选"""
        return self.status in [SelectionStatus.PENDING, SelectionStatus.WAITLISTED,
                               SelectionStatus.LOTTERY_PENDING]

    def can_drop(self) -> bool:
        """检查是否可以退选"""
        return self.status == SelectionStatus.APPROVED

    def get_waitlist_position(self) -> Optional[int]:
        """获取候补位置"""
        if self.status == SelectionStatus.WAITLISTED:
            return self.waitlist_position
        return None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": self.student_name,
            "course_id": self.course_id,
            "course_name": self.course_name,
            "status": self.status,
            "credits": self.credits,
            "selected_at": self.selected_at.isoformat() if self.selected_at else None
        }


class WaitlistRecord(BaseModel):
    """候补记录模型"""
    id: Optional[int] = None
    record_id: int = Field(..., description="原选课记录ID")
    student_id: int = Field(..., description="学生ID")

    course_id: int = Field(..., description="课程ID")
    rule_id: int = Field(..., description="选课规则ID")

    position: int = Field(..., description="候补位置", ge=1)
    priority_score: float = Field(0, description="优先级分数")

    status: str = Field("waiting", description="候补状态: waiting/notified/expired/converted")
    notified_at: Optional[datetime] = Field(None, description="通知时间")
    responded_at: Optional[datetime] = Field(None, description="响应时间")
    converted_at: Optional[datetime] = Field(None, description="转正时间")

    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    class Config:
        from_attributes = True


class CourseSelectionSummary(BaseModel):
    """选课汇总信息"""
    student_id: int = Field(..., description="学生ID")
    student_name: Optional[str] = Field(None, description="学生姓名")
    class_id: Optional[int] = Field(None, description="班级ID")
    class_name: Optional[str] = Field(None, description="班级名称")

    academic_year: str = Field(..., description="学年")
    semester: int = Field(..., description="学期")

    # 选课统计
    total_courses: int = Field(0, description="总选课数")
    approved_courses: int = Field(0, description="已通过数")
    pending_courses: int = Field(0, description="待审核数")
    waitlisted_courses: int = Field(0, description="候补中数")
    withdrawn_courses: int = Field(0, description="已撤选数")
    dropped_courses: int = Field(0, description="已退选数")

    # 学分统计
    total_credits: float = Field(0, description="总学分")
    approved_credits: float = Field(0, description="已通过学分")
    pending_credits: float = Field(0, description="待审核学分")

    # 必修/选修
    required_count: int = Field(0, description="必修课数")
    elective_count: int = Field(0, description="选修课数")

    # 状态
    selection_complete: bool = Field(False, description="选课是否完成")
    warnings: List[str] = Field(default_factory=list, description="警告信息")

    class Config:
        from_attributes = True


class CourseSelectionReport(BaseModel):
    """选课报表"""
    academic_year: str = Field(..., description="学年")
    semester: int = Field(..., description="学期")

    # 总体统计
    total_courses: int = Field(0, description="总开设课程数")
    total_students: int = Field(0, description="总选课学生数")
    total_selections: int = Field(0, description="总选课人次")
    total_approved: int = Field(0, description="总通过人次")

    # 课程统计
    course_stats: List[Dict[str, Any]] = Field(default_factory=list, description="课程统计")
    popular_courses: List[Dict[str, Any]] = Field(default_factory=list, description="热门课程")
    low_demand_courses: List[Dict[str, Any]] = Field(default_factory=list, description="低需求课程")

    # 班级统计
    class_stats: List[Dict[str, Any]] = Field(default_factory=list, description="班级统计")

    # 候补统计
    waitlist_total: int = Field(0, description="总候补人数")
    converted_count: int = Field(0, description="候补转正人数")

    # 生成信息
    generated_at: datetime = Field(default_factory=datetime.now, description="生成时间")

    class Config:
        from_attributes = True


class StudentCoursePlan(BaseModel):
    """学生选课计划"""
    student_id: int = Field(..., description="学生ID")
    academic_year: str = Field(..., description="学年")
    semester: int = Field(..., description="学期")

    # 课程列表
    courses: List[Dict[str, Any]] = Field(default_factory=list, description="课程列表")

    # 学分
    total_credits: float = Field(0, description="总学分")

    # 时间槽分布
    time_slots: Dict[str, int] = Field(default_factory=dict, description="时间槽分布")

    # 冲突检测
    has_conflicts: bool = Field(False, description="是否有冲突")
    conflicts: List[Dict[str, Any]] = Field(default_factory=list, description="冲突列表")

    # 建议
    suggestions: List[str] = Field(default_factory=list, description="优化建议")

    class Config:
        from_attributes = True


class LotteryResult(BaseModel):
    """抽签结果"""
    lottery_id: str = Field(..., description="抽签批次ID")
    course_id: int = Field(..., description="课程ID")
    course_name: Optional[str] = Field(None, description="课程名称")

    rule_id: int = Field(..., description="选课规则ID")
    max_capacity: int = Field(..., description="最大容量")

    # 抽签结果
    total_participants: int = Field(0, description="总参与人数")
    winners: List[int] = Field(default_factory=list, description="中奖学生ID列表")
    losers: List[int] = Field(default_factory=list, description="未中奖学生ID列表")

    # 状态
    status: str = Field("pending", description="抽签状态: pending/completed/cancelled")
    completed_at: Optional[datetime] = Field(None, description="完成时间")

    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    class Config:
        from_attributes = True

    def get_winning_rate(self) -> float:
        """计算中奖率"""
        if self.total_participants == 0:
            return 0
        return len(self.winners) / min(self.total_participants, self.max_capacity)
