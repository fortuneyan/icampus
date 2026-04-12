# -*- coding: utf-8 -*-
"""
T5: 智能排课
排课服务

提供智能排课的核心算法和业务逻辑。
采用回溯算法 + 贪心策略 + 局部搜索进行排课优化。
"""

import random
import time
from datetime import date, datetime
from typing import Optional, List, Dict, Any, Set, Tuple
from copy import deepcopy

from ..models.scheduling_constraint import (
    TimeSlot, SchedulingConstraint, TeacherAvailability,
    ClassroomAvailability, ConflictInfo, SchedulingPreference,
    ConstraintType, TimeSlotType
)
from ..models.scheduling_plan import (
    SchedulingPlan, CourseAssignment, CourseAssignmentStatus,
    ScheduleStatus, OptimizationResult
)


class SchedulingService:
    """
    排课服务

    核心排课算法，支持：
    - 回溯搜索
    - 贪心分配
    - 局部优化
    """

    def __init__(
        self,
        constraints: Optional[List[SchedulingConstraint]] = None,
        teacher_availability: Optional[List[TeacherAvailability]] = None,
        classroom_availability: Optional[List[ClassroomAvailability]] = None,
        preference: Optional[SchedulingPreference] = None,
    ):
        self.constraints = constraints or []
        self.teacher_availability = teacher_availability or []
        self.classroom_availability = classroom_availability or []
        self.preference = preference or SchedulingPreference()

        # 可用时间段集合
        self.available_slots: Set[Tuple[int, int]] = self._generate_available_slots()

    def _generate_available_slots(self) -> Set[Tuple[int, int]]:
        """生成所有可用时间段"""
        slots = set()
        # 周一到周五，每天10节课
        for day in range(1, 6):  # 1-5
            for period in range(1, 11):  # 1-10
                slots.add((day, period))
        return slots

    def optimize_schedule(
        self,
        plan: SchedulingPlan,
        max_iterations: int = 1000,
        time_limit: float = 60.0,
    ) -> OptimizationResult:
        """
        优化排课方案

        使用混合算法进行优化：
        1. 贪心初始化
        2. 局部搜索优化
        3. 冲突修复
        """
        start_time = time.time()
        plan.status = ScheduleStatus.OPTIMIZING

        # 获取未分配的课程
        unassigned = [a for a in plan.assignments if not a.is_locked and not a.time_slot]

        if not unassigned:
            # 所有课程都已分配，直接优化
            return self._local_search_optimize(plan, max_iterations, time_limit, start_time)

        # 第一阶段：贪心分配
        plan = self._greedy_assign(plan, unassigned)

        # 第二阶段：局部搜索优化
        result = self._local_search_optimize(plan, max_iterations, time_limit, start_time)

        return result

    def _greedy_assign(
        self,
        plan: SchedulingPlan,
        unassigned: List[CourseAssignment]
    ) -> SchedulingPlan:
        """
        贪心分配

        按优先级顺序为课程分配时间槽。
        """
        # 按约束严格程度排序
        sorted_assignments = self._sort_by_constraints(unassigned)

        for assignment in sorted_assignments:
            # 找到最佳时间槽
            best_slot = self._find_best_slot(assignment)
            if best_slot:
                assignment.time_slot = best_slot
                assignment.status = CourseAssignmentStatus.ASSIGNED

                # 找到最佳教室
                best_classroom = self._find_best_classroom(assignment)
                if best_classroom:
                    assignment.classroom_id = best_classroom.classroom_id
                    assignment.classroom_name = best_classroom.classroom_name

        return plan

    def _sort_by_constraints(self, assignments: List[CourseAssignment]) -> List[CourseAssignment]:
        """按约束严格程度排序"""
        def get_constraint_priority(a: CourseAssignment) -> int:
            priority = 0

            # 有硬约束的课程优先
            for c in self.constraints:
                if c.constraint_type == ConstraintType.HARD:
                    if c.course_id == a.course_id:
                        priority += c.priority

            # 教师可用性限制
            for ta in self.teacher_availability:
                if ta.teacher_id == a.teacher_id:
                    priority += len(ta.available_slots)

            return -priority

        return sorted(assignments, key=get_constraint_priority)

    def _find_best_slot(self, assignment: CourseAssignment) -> Optional[TimeSlot]:
        """
        找到最佳时间槽

        考虑：
        - 教师可用性
        - 班级已有课程
        - 优化偏好
        """
        candidate_slots = []

        for slot_tuple in self.available_slots:
            day, period = slot_tuple
            slot = TimeSlot(day_of_week=day, period=period)

            # 检查教师可用性
            if not self._is_teacher_available(assignment.teacher_id, slot):
                continue

            # 检查班级冲突
            if self._has_class_conflict(assignment.class_id, slot, plan_assignments=[]):
                continue

            # 检查教室可用性
            if assignment.classroom_id:
                if not self._is_classroom_available(assignment.classroom_id, slot):
                    continue

            # 计算评分
            score = self._evaluate_slot(assignment, slot)
            candidate_slots.append((slot, score))

        if not candidate_slots:
            return None

        # 选择评分最高的时间槽
        candidate_slots.sort(key=lambda x: x[1], reverse=True)
        return candidate_slots[0][0]

    def _is_teacher_available(self, teacher_id: int, slot: TimeSlot) -> bool:
        """检查教师是否可用"""
        for ta in self.teacher_availability:
            if ta.teacher_id == teacher_id:
                return ta.is_available(slot)
        return True  # 默认可用

    def _is_classroom_available(self, classroom_id: int, slot: TimeSlot) -> bool:
        """检查教室是否可用"""
        for ca in self.classroom_availability:
            if ca.classroom_id == classroom_id:
                return ca.is_available(slot)
        return True  # 默认可用

    def _has_class_conflict(
        self,
        class_id: int,
        slot: TimeSlot,
        plan_assignments: List[CourseAssignment]
    ) -> bool:
        """检查班级是否有时间冲突"""
        for a in plan_assignments:
            if a.class_id == class_id and a.time_slot:
                if slot.day_of_week == a.time_slot.day_of_week:
                    # 检查课时重叠
                    for i in range(a.duration):
                        if slot.period == a.time_slot.period + i:
                            return True
        return False

    def _evaluate_slot(
        self,
        assignment: CourseAssignment,
        slot: TimeSlot
    ) -> float:
        """评估时间槽的适合程度"""
        score = 100.0

        # 教师偏好
        for ta in self.teacher_availability:
            if ta.teacher_id == assignment.teacher_id:
                if slot in ta.preferred_slots:
                    score += 20

        # 避免碎片化
        if self.preference.avoid_fragmentation:
            # 倾向于上午的课
            if slot.slot_type == TimeSlotType.MORNING:
                score += 10

        # 连堂课优化
        if self.preference.consecutive_class_limit:
            # 倾向于有前序或后续课程的时间
            consecutive_bonus = 5
            score += consecutive_bonus

        return score

    def _find_best_classroom(
        self,
        assignment: CourseAssignment
    ) -> Optional[ClassroomAvailability]:
        """找到最佳教室"""
        if not assignment.time_slot:
            return None

        candidates = []

        for ca in self.classroom_availability:
            if not ca.is_available(assignment.time_slot):
                continue

            score = 0

            # 容量评分
            if ca.capacity >= 40:  # 标准班级
                score += 10

            # 设备评分
            if "投影仪" in ca.equipment:
                score += 5

            candidates.append((ca, score))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def _local_search_optimize(
        self,
        plan: SchedulingPlan,
        max_iterations: int,
        time_limit: float,
        start_time: float
    ) -> OptimizationResult:
        """
        局部搜索优化

        使用爬山法进行局部优化。
        """
        iterations = 0
        conflicts_before = len(plan.conflicts)

        while iterations < max_iterations:
            # 检查时间限制
            if time.time() - start_time > time_limit:
                break

            # 检测冲突
            plan.detect_conflicts()

            if not plan.conflicts:
                # 没有冲突，优化完成
                break

            # 选择一个冲突进行修复
            conflict = plan.conflicts[0]
            improved = self._fix_conflict(plan, conflict)

            if not improved:
                # 无法改进，尝试随机调整
                self._random_adjustment(plan)

            iterations += 1

        # 计算最终评分
        plan.calculate_score(self.preference)
        plan.optimization_iterations = iterations
        plan.status = ScheduleStatus.OPTIMIZED if not plan.conflicts else ScheduleStatus.REVIEWING

        conflicts_resolved = conflicts_before - len(plan.conflicts)

        return OptimizationResult(
            success=len(plan.conflicts) == 0,
            plan=plan,
            iterations=iterations,
            final_score=plan.score,
            conflicts_resolved=max(0, conflicts_resolved),
            runtime_seconds=time.time() - start_time,
            message="优化完成" if len(plan.conflicts) == 0 else "存在未解决的冲突",
        )

    def _fix_conflict(
        self,
        plan: SchedulingPlan,
        conflict: ConflictInfo
    ) -> bool:
        """修复冲突"""
        conflict_type = conflict.conflict_type

        if conflict_type == "teacher_conflict":
            return self._fix_teacher_conflict(plan, conflict)
        elif conflict_type == "class_conflict":
            return self._fix_class_conflict(plan, conflict)
        elif conflict_type == "classroom_conflict":
            return self._fix_classroom_conflict(plan, conflict)

        return False

    def _fix_teacher_conflict(
        self,
        plan: SchedulingPlan,
        conflict: ConflictInfo
    ) -> bool:
        """修复教师冲突"""
        teacher_ids = conflict.involved_entities.get("teacher_id", [])
        if not teacher_ids:
            return False

        teacher_id = teacher_ids[0]
        teacher_assignments = plan.get_assignments_by_teacher(teacher_id)

        # 找到冲突的时间槽
        slot_assignments: Dict[Tuple[int, int], List[CourseAssignment]] = {}
        for a in teacher_assignments:
            if a.time_slot:
                for ts in a.get_time_slots():
                    key = (ts.day_of_week, ts.period)
                    if key not in slot_assignments:
                        slot_assignments[key] = []
                    slot_assignments[key].append(a)

        # 找到冲突的时间槽
        for key, assignments in slot_assignments.items():
            if len(assignments) > 1:
                # 保持第一个，移动其他的
                for a in assignments[1:]:
                    if a.is_locked:
                        continue

                    # 尝试找到新的时间槽
                    new_slot = self._find_best_slot(a)
                    if new_slot:
                        a.time_slot = new_slot
                        return True

        return False

    def _fix_class_conflict(
        self,
        plan: SchedulingPlan,
        conflict: ConflictInfo
    ) -> bool:
        """修复班级冲突"""
        class_ids = conflict.involved_entities.get("class_id", [])
        if not class_ids:
            return False

        class_id = class_ids[0]
        class_assignments = plan.get_assignments_by_class(class_id)

        # 找到冲突的时间槽
        slot_assignments: Dict[Tuple[int, int], List[CourseAssignment]] = {}
        for a in class_assignments:
            if a.time_slot:
                for ts in a.get_time_slots():
                    key = (ts.day_of_week, ts.period)
                    if key not in slot_assignments:
                        slot_assignments[key] = []
                    slot_assignments[key].append(a)

        # 找到冲突的时间槽
        for key, assignments in slot_assignments.items():
            if len(assignments) > 1:
                for a in assignments[1:]:
                    if a.is_locked:
                        continue

                    new_slot = self._find_best_slot(a)
                    if new_slot:
                        a.time_slot = new_slot
                        return True

        return False

    def _fix_classroom_conflict(
        self,
        plan: SchedulingPlan,
        conflict: ConflictInfo
    ) -> bool:
        """修复教室冲突"""
        classroom_ids = conflict.involved_entities.get("classroom_id", [])
        if not classroom_ids:
            return False

        classroom_id = classroom_ids[0]

        # 找到使用该教室的分配
        for a in plan.assignments:
            if a.classroom_id == classroom_id and a.time_slot and not a.is_locked:
                # 尝试更换教室
                new_classroom = self._find_best_classroom(a)
                if new_classroom and new_classroom.classroom_id != classroom_id:
                    a.classroom_id = new_classroom.classroom_id
                    a.classroom_name = new_classroom.classroom_name
                    return True

                # 尝试更换时间
                new_slot = self._find_best_slot(a)
                if new_slot:
                    a.time_slot = new_slot
                    return True

        return False

    def _random_adjustment(self, plan: SchedulingPlan) -> None:
        """随机调整"""
        unlocked = [a for a in plan.assignments if not a.is_locked and a.time_slot]
        if not unlocked:
            return

        # 随机选择一个分配
        assignment = random.choice(unlocked)
        original_slot = assignment.time_slot

        # 尝试新的时间槽
        new_slot = self._find_best_slot(assignment)
        if new_slot and new_slot != original_slot:
            assignment.time_slot = new_slot


class ConflictDetector:
    """
    冲突检测器

    检测排课方案中的各种冲突。
    """

    def __init__(self):
        self.conflicts: List[ConflictInfo] = []

    def detect_all_conflicts(
        self,
        assignments: List[CourseAssignment]
    ) -> List[ConflictInfo]:
        """检测所有类型的冲突"""
        self.conflicts = []

        # 教师冲突
        self._detect_teacher_conflicts(assignments)

        # 班级冲突
        self._detect_class_conflicts(assignments)

        # 教室冲突
        self._detect_classroom_conflicts(assignments)

        # 可用性冲突
        self._detect_availability_conflicts(assignments)

        return self.conflicts

    def _detect_teacher_conflicts(self, assignments: List[CourseAssignment]) -> None:
        """检测教师冲突"""
        teacher_slots: Dict[int, Dict[Tuple[int, int], CourseAssignment]] = {}

        for a in assignments:
            if a.time_slot:
                if a.teacher_id not in teacher_slots:
                    teacher_slots[a.teacher_id] = {}

                for ts in a.get_time_slots():
                    key = (ts.day_of_week, ts.period)
                    if key in teacher_slots[a.teacher_id]:
                        self.conflicts.append(ConflictInfo(
                            conflict_type="teacher_conflict",
                            severity=4,
                            description=f"教师{a.teacher_name}在同一时间段有多门课程",
                            involved_entities={"teacher_id": [a.teacher_id]},
                            suggestion="调整其中一门课程的时间",
                        ))
                    else:
                        teacher_slots[a.teacher_id][key] = a

    def _detect_class_conflicts(self, assignments: List[CourseAssignment]) -> None:
        """检测班级冲突"""
        class_slots: Dict[int, Dict[Tuple[int, int], CourseAssignment]] = {}

        for a in assignments:
            if a.time_slot:
                if a.class_id not in class_slots:
                    class_slots[a.class_id] = {}

                for ts in a.get_time_slots():
                    key = (ts.day_of_week, ts.period)
                    if key in class_slots[a.class_id]:
                        self.conflicts.append(ConflictInfo(
                            conflict_type="class_conflict",
                            severity=5,
                            description=f"班级{a.class_name}在同一时间段有多门课程",
                            involved_entities={"class_id": [a.class_id]},
                            suggestion="检查课程分配",
                        ))
                    else:
                        class_slots[a.class_id][key] = a

    def _detect_classroom_conflicts(self, assignments: List[CourseAssignment]) -> None:
        """检测教室冲突"""
        classroom_slots: Dict[int, Dict[Tuple[int, int], CourseAssignment]] = {}

        for a in assignments:
            if a.classroom_id and a.time_slot:
                if a.classroom_id not in classroom_slots:
                    classroom_slots[a.classroom_id] = {}

                for ts in a.get_time_slots():
                    key = (ts.day_of_week, ts.period)
                    if key in classroom_slots[a.classroom_id]:
                        self.conflicts.append(ConflictInfo(
                            conflict_type="classroom_conflict",
                            severity=3,
                            description=f"教室{a.classroom_name}在同一时间段被多次使用",
                            involved_entities={"classroom_id": [a.classroom_id]},
                            suggestion="更换教室或调整时间",
                        ))
                    else:
                        classroom_slots[a.classroom_id][key] = a

    def _detect_availability_conflicts(
        self,
        assignments: List[CourseAssignment]
    ) -> None:
        """检测可用性冲突"""
        for a in assignments:
            if a.time_slot and hasattr(a, 'teacher_available_slots'):
                # 检查教师是否可用
                if not any(ts == a.time_slot for ts in a.teacher_available_slots):
                    self.conflicts.append(ConflictInfo(
                        conflict_type="teacher_unavailable",
                        severity=4,
                        description=f"教师{a.teacher_name}在指定时间不可用",
                        involved_entities={"teacher_id": [a.teacher_id]},
                        suggestion="更换上课时间或教师",
                    ))
