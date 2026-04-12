# -*- coding: utf-8 -*-
"""
T5: 智能排课
排课约束模型

定义排课系统中的各类约束条件，包括：
- 时间约束
- 空间约束（教室）
- 教师约束
- 课程约束
- 班级约束
"""

from datetime import date, time, datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Set, Tuple


class ConstraintType(str, Enum):
    """约束类型"""
    HARD = "hard"           # 硬约束（必须满足）
    SOFT = "soft"          # 软约束（尽量满足）


class TimeSlotType(str, Enum):
    """时间段类型"""
    MORNING = "morning"     # 上午
    AFTERNOON = "afternoon" # 下午
    EVENING = "evening"     # 晚自习


class ConflictType(str, Enum):
    """冲突类型"""
    TEACHER_CONFLICT = "teacher_conflict"           # 教师冲突
    CLASSROOM_CONFLICT = "classroom_conflict"       # 教室冲突
    CLASS_CONFLICT = "class_conflict"               # 班级冲突
    TIME_CONFLICT = "time_conflict"                 # 时间冲突
    TEACHER_UNAVAILABLE = "teacher_unavailable"     # 教师不可用
    CLASSROOM_UNAVAILABLE = "classroom_unavailable" # 教室不可用
    CONSECUTIVE_CLASSES = "consecutive_classes"    # 连堂课过多


class TimeSlot:
    """
    时间段

    表示一个具体的上课时间段。
    """

    def __init__(
        self,
        day_of_week: int,  # 1-7 (周一到周日)
        period: int,        # 第几节课 1-10
        start_time: time = None,
        end_time: time = None,
        slot_type: TimeSlotType = TimeSlotType.MORNING,
    ):
        self.day_of_week = day_of_week
        self.period = period
        self.slot_type = slot_type

        # 默认时间设置
        if start_time is None:
            start_time = self._get_default_start_time(period)
        if end_time is None:
            end_time = self._get_default_end_time(period)

        self.start_time = start_time
        self.end_time = end_time

    @staticmethod
    def _get_default_start_time(period: int) -> time:
        """获取默认开始时间"""
        default_times = {
            1: time(8, 0),
            2: time(8, 55),
            3: time(9, 50),
            4: time(10, 45),
            5: time(11, 30),
            6: time(14, 0),
            7: time(14, 55),
            8: time(15, 50),
            9: time(16, 45),
            10: time(19, 0),
        }
        return default_times.get(period, time(8, 0))

    @staticmethod
    def _get_default_end_time(period: int) -> time:
        """获取默认结束时间"""
        default_times = {
            1: time(8, 45),
            2: time(9, 40),
            3: time(10, 35),
            4: time(11, 20),
            5: time(12, 5),
            6: time(14, 45),
            7: time(15, 40),
            8: time(16, 35),
            9: time(17, 30),
            10: time(20, 45),
        }
        return default_times.get(period, time(8, 45))

    def __str__(self) -> str:
        days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        return f"{days[self.day_of_week - 1]} 第{self.period}节"

    def __repr__(self) -> str:
        return f"<TimeSlot(day={self.day_of_week}, period={self.period})>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "day_of_week": self.day_of_week,
            "period": self.period,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "slot_type": self.slot_type.value if isinstance(self.slot_type, Enum) else self.slot_type,
        }

    def __eq__(self, other) -> bool:
        if not isinstance(other, TimeSlot):
            return False
        return self.day_of_week == other.day_of_week and self.period == other.period

    def __hash__(self) -> int:
        return hash((self.day_of_week, self.period))


class SchedulingConstraint:
    """
    排课约束

    定义一个排课约束条件。
    """

    def __init__(
        self,
        id: int,
        constraint_type: ConstraintType,
        name: str,
        description: str,
        priority: int = 1,
        enabled: bool = True,
        teacher_id: Optional[int] = None,
        class_id: Optional[int] = None,
        classroom_id: Optional[int] = None,
        course_id: Optional[int] = None,
        day_of_week: Optional[int] = None,
        periods: Optional[List[int]] = None,
        time_slots: Optional[List[TimeSlot]] = None,
        max_consecutive: Optional[int] = None,
        max_daily: Optional[int] = None,
        required_room_type: Optional[str] = None,
        same_day_courses: Optional[List[int]] = None,
    ):
        self.id = id
        self.constraint_type = constraint_type
        self.name = name
        self.description = description
        self.priority = priority
        self.enabled = enabled

        # 约束对象
        self.teacher_id = teacher_id
        self.class_id = class_id
        self.classroom_id = classroom_id
        self.course_id = course_id

        # 时间约束
        self.day_of_week = day_of_week
        self.periods = periods or []
        self.time_slots = time_slots or []

        # 数量约束
        self.max_consecutive = max_consecutive
        self.max_daily = max_daily

        # 其他约束
        self.required_room_type = required_room_type
        self.same_day_courses = same_day_courses or []

    def is_hard_constraint(self) -> bool:
        """是否为硬约束"""
        return self.constraint_type == ConstraintType.HARD

    def is_soft_constraint(self) -> bool:
        """是否为软约束"""
        return self.constraint_type == ConstraintType.SOFT

    def check_violation(self, assignment: 'CourseAssignment') -> Tuple[bool, Optional[str]]:
        """
        检查是否违反约束

        Returns:
            (是否违反, 违反原因)
        """
        if not self.enabled:
            return False, None

        # 检查教师冲突
        if self.teacher_id and assignment.teacher_id == self.teacher_id:
            # 检查同一时间段
            if self.day_of_week and assignment.time_slot:
                if assignment.time_slot.day_of_week == self.day_of_week:
                    if self.periods and assignment.time_slot.period in self.periods:
                        return True, f"教师{self.teacher_id}在指定时间已有课程"

        # 检查班级冲突
        if self.class_id and assignment.class_id == self.class_id:
            if self.day_of_week and assignment.time_slot:
                if assignment.time_slot.day_of_week == self.day_of_week:
                    if self.periods and assignment.time_slot.period in self.periods:
                        return True, f"班级{self.class_id}在指定时间已有课程"

        # 检查教室冲突
        if self.classroom_id and assignment.classroom_id == self.classroom_id:
            if self.day_of_week and assignment.time_slot:
                if assignment.time_slot.day_of_week == self.day_of_week:
                    if self.periods and assignment.time_slot.period in self.periods:
                        return True, f"教室{self.classroom_id}在指定时间已被占用"

        return False, None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "constraint_type": self.constraint_type.value if isinstance(self.constraint_type, Enum) else self.constraint_type,
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "enabled": self.enabled,
            "teacher_id": self.teacher_id,
            "class_id": self.class_id,
            "classroom_id": self.classroom_id,
            "course_id": self.course_id,
            "day_of_week": self.day_of_week,
            "periods": self.periods,
            "time_slots": [ts.to_dict() for ts in self.time_slots] if self.time_slots else [],
            "max_consecutive": self.max_consecutive,
            "max_daily": self.max_daily,
            "required_room_type": self.required_room_type,
            "same_day_courses": self.same_day_courses,
        }


class TeacherAvailability:
    """
    教师可用时间

    定义教师的可用上课时间。
    """

    def __init__(
        self,
        teacher_id: int,
        teacher_name: str,
        available_slots: List[TimeSlot],
        preferred_slots: Optional[List[TimeSlot]] = None,
        unavailable_reasons: Optional[Dict[TimeSlot, str]] = None,
    ):
        self.teacher_id = teacher_id
        self.teacher_name = teacher_name
        self.available_slots = available_slots
        self.preferred_slots = preferred_slots or []
        self.unavailable_reasons = unavailable_reasons or {}

    def is_available(self, slot: TimeSlot) -> bool:
        """检查是否可用"""
        return slot in self.available_slots

    def get_unavailable_reason(self, slot: TimeSlot) -> Optional[str]:
        """获取不可用原因"""
        return self.unavailable_reasons.get(slot)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "teacher_id": self.teacher_id,
            "teacher_name": self.teacher_name,
            "available_slots": [ts.to_dict() for ts in self.available_slots],
            "preferred_slots": [ts.to_dict() for ts in self.preferred_slots],
            "unavailable_reasons": {
                f"{k.day_of_week}_{k.period}": v
                for k, v in self.unavailable_reasons.items()
            },
        }


class ClassroomAvailability:
    """
    教室可用性

    定义教室的可用情况。
    """

    def __init__(
        self,
        classroom_id: int,
        classroom_name: str,
        room_type: str,
        capacity: int,
        available_slots: List[TimeSlot],
        equipment: Optional[List[str]] = None,
    ):
        self.classroom_id = classroom_id
        self.classroom_name = classroom_name
        self.room_type = room_type
        self.capacity = capacity
        self.available_slots = available_slots
        self.equipment = equipment or []

    def is_available(self, slot: TimeSlot) -> bool:
        """检查是否可用"""
        return slot in self.available_slots

    def can_accommodate(self, class_size: int) -> bool:
        """检查是否能容纳班级人数"""
        return self.capacity >= class_size

    def has_equipment(self, equipment: str) -> bool:
        """检查是否有指定设备"""
        return equipment in self.equipment

    def to_dict(self) -> Dict[str, Any]:
        return {
            "classroom_id": self.classroom_id,
            "classroom_name": self.classroom_name,
            "room_type": self.room_type,
            "capacity": self.capacity,
            "available_slots": [ts.to_dict() for ts in self.available_slots],
            "equipment": self.equipment,
        }


class ConflictInfo:
    """
    冲突信息

    记录排课冲突的详细信息。
    """

    def __init__(
        self,
        conflict_type: ConflictType,
        severity: int,  # 1-5, 5为最严重
        description: str,
        involved_entities: Dict[str, List[int]],
        suggestion: Optional[str] = None,
    ):
        self.conflict_type = conflict_type
        self.severity = severity
        self.description = description
        self.involved_entities = involved_entities
        self.suggestion = suggestion

    def is_hard_conflict(self) -> bool:
        """是否为硬冲突"""
        return self.severity >= 4

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_type": self.conflict_type.value if isinstance(self.conflict_type, Enum) else self.conflict_type,
            "severity": self.severity,
            "description": self.description,
            "involved_entities": self.involved_entities,
            "suggestion": self.suggestion,
        }


class SchedulingPreference:
    """
    排课偏好

    定义排课的优化目标。
    """

    def __init__(
        self,
        balance_teacher_workload: bool = True,
        minimize_gaps: bool = True,
        spread_courses_evenly: bool = True,
        morning_preference: Optional[List[int]] = None,  # 教师ID列表
        consecutive_class_limit: int = 3,
        max_courses_per_day: int = 6,
        avoid_fragmentation: bool = True,
        group_same_grade: bool = False,
    ):
        self.balance_teacher_workload = balance_teacher_workload
        self.minimize_gaps = minimize_gaps
        self.spread_courses_evenly = spread_courses_evenly
        self.morning_preference = morning_preference or []
        self.consecutive_class_limit = consecutive_class_limit
        self.max_courses_per_day = max_courses_per_day
        self.avoid_fragmentation = avoid_fragmentation
        self.group_same_grade = group_same_grade

    def to_dict(self) -> Dict[str, Any]:
        return {
            "balance_teacher_workload": self.balance_teacher_workload,
            "minimize_gaps": self.minimize_gaps,
            "spread_courses_evenly": self.spread_courses_evenly,
            "morning_preference": self.morning_preference,
            "consecutive_class_limit": self.consecutive_class_limit,
            "max_courses_per_day": self.max_courses_per_day,
            "avoid_fragmentation": self.avoid_fragmentation,
            "group_same_grade": self.group_same_grade,
        }


# 约束工厂函数

def create_teacher_time_constraint(
    teacher_id: int,
    unavailable_days: List[int],
    unavailable_periods: List[int],
    reason: str = "教师不可用"
) -> SchedulingConstraint:
    """创建教师时间约束"""
    return SchedulingConstraint(
        id=0,
        constraint_type=ConstraintType.HARD,
        name=f"教师{teacher_id}时间约束",
        description=reason,
        teacher_id=teacher_id,
        periods=unavailable_periods,
        priority=10,
    )


def create_classroom_capacity_constraint(
    classroom_id: int,
    min_capacity: int,
    max_capacity: int
) -> SchedulingConstraint:
    """创建教室容量约束"""
    return SchedulingConstraint(
        id=0,
        constraint_type=ConstraintType.HARD,
        name=f"教室{classroom_id}容量约束",
        description=f"班级人数需在{min_capacity}-{max_capacity}之间",
        classroom_id=classroom_id,
        priority=5,
    )


def create_teacher_consecutive_constraint(
    teacher_id: int,
    max_consecutive: int = 3
) -> SchedulingConstraint:
    """创建教师连堂课约束"""
    return SchedulingConstraint(
        id=0,
        constraint_type=ConstraintType.SOFT,
        name=f"教师{teacher_id}连堂课约束",
        description=f"教师最多连上{max_consecutive}节课",
        teacher_id=teacher_id,
        max_consecutive=max_consecutive,
        priority=3,
    )
