# -*- coding: utf-8 -*-
"""
T5: 智能排课
排课计划模型

定义排课计划、课程分配和课表相关的数据模型。
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Set, Tuple
from dataclasses import dataclass, field

from .scheduling_constraint import TimeSlot, ConflictInfo, SchedulingPreference


class ScheduleStatus(str, Enum):
    """排课状态"""
    DRAFT = "draft"           # 草稿
    OPTIMIZING = "optimizing" # 优化中
    OPTIMIZED = "optimized"  # 已优化
    REVIEWING = "reviewing"  # 审核中
    PUBLISHED = "published"   # 已发布
    ARCHIVED = "archived"     # 已归档


class CourseAssignmentStatus(str, Enum):
    """课程分配状态"""
    PENDING = "pending"      # 待分配
    ASSIGNED = "assigned"    # 已分配
    CONFLICT = "conflict"    # 有冲突
    OPTIMIZED = "optimized"  # 已优化
    MANUAL_ADJUSTED = "manual_adjusted"  # 手动调整


class CourseAssignment:
    """
    课程分配

    表示将一门课程分配到具体的时间、地点。
    """

    def __init__(
        self,
        id: int,
        course_id: int,
        course_name: str,
        teacher_id: int,
        teacher_name: str,
        class_id: int,
        class_name: str,
        classroom_id: Optional[int] = None,
        classroom_name: Optional[str] = None,
        time_slot: Optional[TimeSlot] = None,
        duration: int = 1,  # 持续几节课
        status: CourseAssignmentStatus = CourseAssignmentStatus.PENDING,
        assignment_score: float = 0.0,  # 分配评分
        is_locked: bool = False,  # 是否锁定
        note: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.course_id = course_id
        self.course_name = course_name
        self.teacher_id = teacher_id
        self.teacher_name = teacher_name
        self.class_id = class_id
        self.class_name = class_name
        self.classroom_id = classroom_id
        self.classroom_name = classroom_name
        self.time_slot = time_slot
        self.duration = duration
        self.status = status
        self.assignment_score = assignment_score
        self.is_locked = is_locked
        self.note = note
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

    def get_time_slots(self) -> List[TimeSlot]:
        """获取所有涉及的时间段"""
        if not self.time_slot:
            return []
        return [
            TimeSlot(
                day_of_week=self.time_slot.day_of_week,
                period=self.time_slot.period + i,
                slot_type=self.time_slot.slot_type,
            )
            for i in range(self.duration)
        ]

    def has_conflict_with(self, other: 'CourseAssignment') -> bool:
        """检查是否与另一个分配冲突"""
        # 教师冲突
        if self.teacher_id == other.teacher_id:
            self_slots = self.get_time_slots()
            other_slots = other.get_time_slots()
            for s1 in self_slots:
                for s2 in other_slots:
                    if s1 == s2:
                        return True

        # 班级冲突
        if self.class_id == other.class_id:
            self_slots = self.get_time_slots()
            other_slots = other.get_time_slots()
            for s1 in self_slots:
                for s2 in other_slots:
                    if s1 == s2:
                        return True

        # 教室冲突
        if self.classroom_id and other.classroom_id:
            if self.classroom_id == other.classroom_id:
                self_slots = self.get_time_slots()
                other_slots = other.get_time_slots()
                for s1 in self_slots:
                    for s2 in other_slots:
                        if s1 == s2:
                            return True

        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "course_id": self.course_id,
            "course_name": self.course_name,
            "teacher_id": self.teacher_id,
            "teacher_name": self.teacher_name,
            "class_id": self.class_id,
            "class_name": self.class_name,
            "classroom_id": self.classroom_id,
            "classroom_name": self.classroom_name,
            "time_slot": self.time_slot.to_dict() if self.time_slot else None,
            "duration": self.duration,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "assignment_score": self.assignment_score,
            "is_locked": self.is_locked,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SchedulingPlan:
    """
    排课计划

    包含一个完整的排课方案。
    """

    def __init__(
        self,
        id: int,
        name: str,
        academic_year: str,
        semester: str,
        start_date: date,
        end_date: date,
        status: ScheduleStatus = ScheduleStatus.DRAFT,
        assignments: Optional[List[CourseAssignment]] = None,
        conflicts: Optional[List[ConflictInfo]] = None,
        score: float = 0.0,
        optimization_iterations: int = 0,
        generated_by: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.name = name
        self.academic_year = academic_year
        self.semester = semester
        self.start_date = start_date
        self.end_date = end_date
        self.status = status
        self.assignments = assignments or []
        self.conflicts = conflicts or []
        self.score = score
        self.optimization_iterations = optimization_iterations
        self.generated_by = generated_by
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

    def add_assignment(self, assignment: CourseAssignment) -> None:
        """添加课程分配"""
        self.assignments.append(assignment)

    def remove_assignment(self, assignment_id: int) -> bool:
        """移除课程分配"""
        for i, a in enumerate(self.assignments):
            if a.id == assignment_id:
                self.assignments.pop(i)
                return True
        return False

    def get_assignments_by_teacher(self, teacher_id: int) -> List[CourseAssignment]:
        """获取指定教师的课程分配"""
        return [a for a in self.assignments if a.teacher_id == teacher_id]

    def get_assignments_by_class(self, class_id: int) -> List[CourseAssignment]:
        """获取指定班级的课程分配"""
        return [a for a in self.assignments if a.class_id == class_id]

    def get_assignments_by_time_slot(self, time_slot: TimeSlot) -> List[CourseAssignment]:
        """获取指定时间段的课程分配"""
        result = []
        for a in self.assignments:
            for ts in a.get_time_slots():
                if ts == time_slot:
                    result.append(a)
                    break
        return result

    def detect_conflicts(self) -> List[ConflictInfo]:
        """检测排课冲突"""
        conflicts = []

        # 检查教师冲突
        teacher_slots: Dict[int, Set[TimeSlot]] = {}
        for a in self.assignments:
            if a.teacher_id not in teacher_slots:
                teacher_slots[a.teacher_id] = set()
            for ts in a.get_time_slots():
                if ts in teacher_slots[a.teacher_id]:
                    conflicts.append(ConflictInfo(
                        conflict_type="teacher_conflict",
                        severity=4,
                        description=f"教师{a.teacher_name}在同一时间段有多门课程",
                        involved_entities={"teacher_id": [a.teacher_id]},
                        suggestion="调整其中一门课程的时间",
                    ))
                else:
                    teacher_slots[a.teacher_id].add(ts)

        # 检查班级冲突
        class_slots: Dict[int, Set[TimeSlot]] = {}
        for a in self.assignments:
            if a.class_id not in class_slots:
                class_slots[a.class_id] = set()
            for ts in a.get_time_slots():
                if ts in class_slots[a.class_id]:
                    conflicts.append(ConflictInfo(
                        conflict_type="class_conflict",
                        severity=5,
                        description=f"班级{a.class_name}在同一时间段有多门课程",
                        involved_entities={"class_id": [a.class_id]},
                        suggestion="检查课程分配",
                    ))
                else:
                    class_slots[a.class_id].add(ts)

        # 检查教室冲突
        classroom_slots: Dict[int, Set[TimeSlot]] = {}
        for a in self.assignments:
            if a.classroom_id:
                if a.classroom_id not in classroom_slots:
                    classroom_slots[a.classroom_id] = set()
                for ts in a.get_time_slots():
                    if ts in classroom_slots[a.classroom_id]:
                        conflicts.append(ConflictInfo(
                            conflict_type="classroom_conflict",
                            severity=3,
                            description=f"教室{a.classroom_name}在同一时间段被多次使用",
                            involved_entities={"classroom_id": [a.classroom_id]},
                            suggestion="更换教室或调整时间",
                        ))
                    else:
                        classroom_slots[a.classroom_id].add(ts)

        self.conflicts = conflicts
        return conflicts

    def calculate_score(self, preference: SchedulingPreference) -> float:
        """计算排课评分"""
        score = 100.0

        # 扣除冲突分
        for conflict in self.conflicts:
            if conflict.is_hard_conflict():
                score -= 20
            else:
                score -= 5

        # 检查软约束
        teacher_daily: Dict[int, Dict[int, int]] = {}
        for a in self.assignments:
            if a.teacher_id not in teacher_daily:
                teacher_daily[a.teacher_id] = {}
            ts = a.time_slot
            if ts:
                day = ts.day_of_week
                teacher_daily[a.teacher_id][day] = teacher_daily[a.teacher_id].get(day, 0) + 1

        # 检查教师每天课程数
        if preference.max_courses_per_day:
            for teacher_id, daily in teacher_daily.items():
                for day, count in daily.items():
                    if count > preference.max_courses_per_day:
                        score -= (count - preference.max_courses_per_day) * 2

        self.score = max(0, score)
        return self.score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "academic_year": self.academic_year,
            "semester": self.semester,
            "start_date": self.start_date.isoformat() if isinstance(self.start_date, date) else self.start_date,
            "end_date": self.end_date.isoformat() if isinstance(self.end_date, date) else self.end_date,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "assignments": [a.to_dict() for a in self.assignments],
            "conflicts": [c.to_dict() for c in self.conflicts],
            "score": self.score,
            "optimization_iterations": self.optimization_iterations,
            "generated_by": self.generated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ScheduleTable:
    """
    课表

    以网格形式展示的课表。
    """

    def __init__(
        self,
        plan: SchedulingPlan,
        days: int = 7,
        periods: int = 10,
    ):
        self.plan = plan
        self.days = days
        self.periods = periods
        self._grid: Dict[int, Dict[int, List[CourseAssignment]]] = {}

        # 构建网格
        for day in range(1, days + 1):
            self._grid[day] = {}
            for period in range(1, periods + 1):
                self._grid[day][period] = []

        # 填充分配
        for a in plan.assignments:
            if a.time_slot:
                day = a.time_slot.day_of_week
                for i in range(a.duration):
                    period = a.time_slot.period + i
                    if 1 <= period <= periods:
                        self._grid[day][period].append(a)

    def get_cell(self, day: int, period: int) -> List[CourseAssignment]:
        """获取指定单元格的内容"""
        if day in self._grid and period in self._grid[day]:
            return self._grid[day][period]
        return []

    def to_dict(self) -> Dict[str, Any]:
        grid_data = {}
        for day in range(1, self.days + 1):
            grid_data[day] = {}
            for period in range(1, self.periods + 1):
                grid_data[day][period] = [a.to_dict() for a in self._grid[day][period]]

        return {
            "plan_id": self.plan.id,
            "plan_name": self.plan.name,
            "days": self.days,
            "periods": self.periods,
            "grid": grid_data,
        }


class OptimizationResult:
    """
    优化结果

    记录排课优化的结果。
    """

    def __init__(
        self,
        success: bool,
        plan: Optional[SchedulingPlan] = None,
        iterations: int = 0,
        final_score: float = 0.0,
        conflicts_resolved: int = 0,
        runtime_seconds: float = 0.0,
        message: str = "",
    ):
        self.success = success
        self.plan = plan
        self.iterations = iterations
        self.final_score = final_score
        self.conflicts_resolved = conflicts_resolved
        self.runtime_seconds = runtime_seconds
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "plan": self.plan.to_dict() if self.plan else None,
            "iterations": self.iterations,
            "final_score": self.final_score,
            "conflicts_resolved": self.conflicts_resolved,
            "runtime_seconds": self.runtime_seconds,
            "message": self.message,
        }
