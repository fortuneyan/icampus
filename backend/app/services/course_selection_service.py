# -*- coding: utf-8 -*-
"""
选课服务
T6: 选课管理
提供选课、退选、候补、抽签等核心功能
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import random
from app.models.course_selection_rule import (
    SelectionRule, SelectionMode, SelectionStrategy,
    RuleStatus, CourseCapacity, SelectionPriority
)
from app.models.course_selection_record import (
    SelectionRecord, WaitlistRecord, CourseSelectionSummary,
    CourseSelectionReport, StudentCoursePlan, LotteryResult, LotteryStatus, SelectionStatus
)


class CourseSelectionService:
    """选课服务"""

    def __init__(self):
        self.rules: Dict[int, SelectionRule] = {}  # 规则ID -> 规则
        self.records: Dict[int, SelectionRecord] = {}  # 记录ID -> 记录
        self.capacities: Dict[int, CourseCapacity] = {}  # 课程ID -> 容量
        self.waitlists: Dict[int, List[WaitlistRecord]] = {}  # 课程ID -> 候补列表
        self.lotteries: Dict[str, LotteryResult] = {}  # 抽签ID -> 结果
        self.next_record_id = 1
        self.next_waitlist_id = 1

    # ==================== 规则管理 ====================

    def create_rule(self, rule_data: Dict[str, Any]) -> Tuple[bool, SelectionRule, str]:
        """创建选课规则"""
        try:
            rule = SelectionRule(**rule_data)
            self.rules[rule.id or len(self.rules) + 1] = rule
            return True, rule, "规则创建成功"
        except Exception as e:
            return False, None, f"规则创建失败: {str(e)}"

    def get_active_rule(self, academic_year: str, semester: int) -> Optional[SelectionRule]:
        """获取当前生效的选课规则"""
        for rule in self.rules.values():
            if (rule.academic_year == academic_year and
                rule.semester == semester and
                rule.is_active()):
                return rule
        return None

    def update_rule_status(self, rule_id: int, status: RuleStatus) -> Tuple[bool, str]:
        """更新规则状态"""
        if rule_id not in self.rules:
            return False, "规则不存在"

        self.rules[rule_id].status = status
        return True, "状态更新成功"

    # ==================== 选课核心 ====================

    def select_course(self, student_id: int, course_id: int,
                    rule_id: int, credits: float,
                    student_info: Optional[Dict[str, Any]] = None) -> Tuple[bool, SelectionRecord, str]:
        """
        选课
        返回: (是否成功, 选课记录, 消息)
        """
        # 获取规则
        rule = self.rules.get(rule_id)
        if not rule:
            return False, None, "选课规则不存在"

        # 检查规则状态
        if not rule.is_active():
            if rule.is_expired():
                return False, None, "选课已结束"
            return False, None, "选课未开始"

        # 检查学生已选学分和课程数
        student_records = self.get_student_records(student_id, rule.academic_year, rule.semester)
        current_credits = sum(r.credits for r in student_records if r.status == SelectionStatus.APPROVED)
        current_count = len([r for r in student_records if r.status == SelectionStatus.APPROVED])

        # 检查学分限制
        can_select, reason = rule.can_select(current_credits, current_count)
        if not can_select:
            return False, None, reason

        # 检查课程容量
        capacity = self.capacities.get(course_id)
        if capacity:
            available, msg = capacity.check_availability()
            if not available:
                # 加入候补
                return self._add_to_waitlist(student_id, course_id, rule_id, credits, student_info)
        else:
            # 初始化课程容量
            capacity = CourseCapacity(course_id=course_id, max_capacity=50)
            self.capacities[course_id] = capacity

        # 检查课程冲突
        if self._has_time_conflict(student_id, course_id, rule):
            if not rule.allow_conflicts:
                return False, None, "与已选课程时间冲突"

        # 创建选课记录
        record = SelectionRecord(
            id=self.next_record_id,
            student_id=student_id,
            student_name=student_info.get("name") if student_info else None,
            student_class=student_info.get("class") if student_info else None,
            course_id=course_id,
            rule_id=rule_id,
            academic_year=rule.academic_year,
            semester=rule.semester,
            credits=credits,
            status=SelectionStatus.APPROVED,
            selected_at=datetime.now()
        )

        # 根据选课策略处理
        if rule.selection_mode == SelectionMode.LOTTERY:
            record.status = SelectionStatus.LOTTERY_PENDING
            record.lottery_status = LotteryStatus.PENDING
            result = "选课已提交，等待抽签"
        elif rule.strategy == SelectionStrategy.FIRST_COME_FIRST_SERVED:
            record.status = SelectionStatus.APPROVED
            result = "选课成功"
        else:
            record.status = SelectionStatus.APPROVED
            result = "选课成功"

        self.records[self.next_record_id] = record
        self.next_record_id += 1

        # 更新容量
        if capacity:
            capacity.current_count += 1
            if capacity.current_count >= capacity.max_capacity:
                capacity.is_full = True

        return True, record, result

    def withdraw_course(self, record_id: int, student_id: int) -> Tuple[bool, str]:
        """
        撤选课程（未确认前）
        """
        record = self.records.get(record_id)
        if not record:
            return False, "选课记录不存在"

        if record.student_id != student_id:
            return False, "无权操作此记录"

        if not record.can_withdraw():
            return False, "该状态不允许撤选"

        record.status = SelectionStatus.WITHDRAWN
        record.dropped_at = datetime.now()

        # 更新容量
        capacity = self.capacities.get(record.course_id)
        if capacity and capacity.current_count > 0:
            capacity.current_count -= 1
            capacity.is_full = False

            # 候补转正
            self._convert_from_waitlist(record.course_id)

        return True, "撤选成功"

    def drop_course(self, record_id: int, student_id: int, reason: Optional[str] = None) -> Tuple[bool, str]:
        """
        退选课程（确认后）
        """
        record = self.records.get(record_id)
        if not record:
            return False, "选课记录不存在"

        if record.student_id != student_id:
            return False, "无权操作此记录"

        if not record.can_drop():
            return False, "该状态不允许退选"

        record.status = SelectionStatus.DROPPED
        record.dropped_at = datetime.now()
        record.remarks = reason

        # 更新容量
        capacity = self.capacities.get(record.course_id)
        if capacity and capacity.current_count > 0:
            capacity.current_count -= 1
            capacity.is_full = False

            # 候补转正
            self._convert_from_waitlist(record.course_id)

        return True, "退选成功"

    # ==================== 候补管理 ====================

    def _add_to_waitlist(self, student_id: int, course_id: int,
                        rule_id: int, credits: float,
                        student_info: Optional[Dict[str, Any]] = None) -> Tuple[bool, SelectionRecord, str]:
        """加入候补"""
        # 检查是否已在候补
        existing = self._find_waitlist_record(student_id, course_id)
        if existing:
            return False, None, "已在候补队列中"

        # 获取候补位置
        waitlist = self.waitlists.get(course_id, [])
        position = len(waitlist) + 1

        # 创建候补记录
        waitlist_record = WaitlistRecord(
            id=self.next_waitlist_id,
            student_id=student_id,
            course_id=course_id,
            rule_id=rule_id,
            position=position,
            priority_score=random.random()
        )

        if course_id not in self.waitlists:
            self.waitlists[course_id] = []
        self.waitlists[course_id].append(waitlist_record)

        # 更新容量候补数
        capacity = self.capacities.get(course_id)
        if capacity:
            capacity.waitlist_count += 1

        self.next_waitlist_id += 1

        # 创建选课记录
        record = SelectionRecord(
            id=self.next_record_id,
            student_id=student_id,
            student_name=student_info.get("name") if student_info else None,
            course_id=course_id,
            rule_id=rule_id,
            academic_year=student_info.get("academic_year", "") if student_info else "",
            semester=student_info.get("semester", 1) if student_info else 1,
            credits=credits,
            status=SelectionStatus.WAITLISTED,
            waitlist_position=position
        )

        self.records[self.next_record_id] = record
        self.next_record_id += 1

        return True, record, f"已加入候补队列，位置: {position}"

    def _find_waitlist_record(self, student_id: int, course_id: int) -> Optional[WaitlistRecord]:
        """查找候补记录"""
        waitlist = self.waitlists.get(course_id, [])
        for record in waitlist:
            if record.student_id == student_id:
                return record
        return None

    def _convert_from_waitlist(self, course_id: int) -> Optional[int]:
        """候补转正"""
        waitlist = self.waitlists.get(course_id, [])
        if not waitlist:
            return None

        # 按优先级排序
        waitlist.sort(key=lambda x: x.priority_score, reverse=True)

        # 获取第一个候补
        for i, record in enumerate(waitlist):
            if record.status == "waiting":
                record.status = "converted"
                record.converted_at = datetime.now()

                # 找到对应的选课记录并更新状态
                for rec in self.records.values():
                    if (rec.student_id == record.student_id and
                        rec.course_id == course_id and
                        rec.status == SelectionStatus.WAITLISTED):
                        rec.status = SelectionStatus.APPROVED
                        rec.confirmed_at = datetime.now()
                        break

                # 更新容量
                capacity = self.capacities.get(course_id)
                if capacity and capacity.current_count < capacity.max_capacity:
                    capacity.current_count += 1

                # 移除候补列表
                self.waitlists[course_id] = waitlist[i+1:]
                return record.student_id

        return None

    def get_waitlist_position(self, student_id: int, course_id: int) -> Optional[int]:
        """获取候补位置"""
        waitlist = self.waitlists.get(course_id, [])
        for record in waitlist:
            if record.student_id == student_id and record.status == "waiting":
                return record.position
        return None

    # ==================== 抽签系统 ====================

    def conduct_lottery(self, course_id: int, max_capacity: int) -> LotteryResult:
        """执行抽签"""
        # 收集所有待抽签的学生
        participants = []
        for record in self.records.values():
            if (record.course_id == course_id and
                record.status == SelectionStatus.LOTTERY_PENDING):
                participants.append(record.student_id)

        # 生成抽签结果
        winners = random.sample(participants, min(len(participants), max_capacity))
        losers = [p for p in participants if p not in winners]

        lottery_id = f"lottery_{course_id}_{datetime.now().timestamp()}"
        result = LotteryResult(
            lottery_id=lottery_id,
            course_id=course_id,
            max_capacity=max_capacity,
            total_participants=len(participants),
            winners=winners,
            losers=losers,
            status="completed",
            completed_at=datetime.now()
        )

        self.lotteries[lottery_id] = result

        # 更新选课记录
        for student_id in winners:
            for record in self.records.values():
                if (record.student_id == student_id and
                    record.course_id == course_id and
                    record.status == SelectionStatus.LOTTERY_PENDING):
                    record.status = SelectionStatus.APPROVED
                    record.lottery_status = LotteryStatus.WINNING
                    record.confirmed_at = datetime.now()

        for student_id in losers:
            for record in self.records.values():
                if (record.student_id == student_id and
                    record.course_id == course_id and
                    record.status == SelectionStatus.LOTTERY_PENDING):
                    record.status = SelectionStatus.FAILED
                    record.lottery_status = LotteryStatus.LOSING

        return result

    # ==================== 查询功能 ====================

    def get_student_records(self, student_id: int,
                           academic_year: Optional[str] = None,
                           semester: Optional[int] = None) -> List[SelectionRecord]:
        """获取学生的选课记录"""
        records = []
        for record in self.records.values():
            if record.student_id == student_id:
                if academic_year and record.academic_year != academic_year:
                    continue
                if semester and record.semester != semester:
                    continue
                records.append(record)
        return records

    def get_student_summary(self, student_id: int,
                           academic_year: str,
                           semester: int) -> CourseSelectionSummary:
        """获取学生选课汇总"""
        records = self.get_student_records(student_id, academic_year, semester)

        summary = CourseSelectionSummary(
            student_id=student_id,
            academic_year=academic_year,
            semester=semester
        )

        for record in records:
            if record.status == SelectionStatus.APPROVED:
                summary.approved_courses += 1
                summary.approved_credits += record.credits
                summary.total_credits += record.credits
            elif record.status == SelectionStatus.PENDING:
                summary.pending_courses += 1
                summary.pending_credits += record.credits
                summary.total_credits += record.credits
            elif record.status == SelectionStatus.WAITLISTED:
                summary.waitlisted_courses += 1
                summary.total_credits += record.credits
            elif record.status == SelectionStatus.WITHDRAWN:
                summary.withdrawn_courses += 1
            elif record.status == SelectionStatus.DROPPED:
                summary.dropped_courses += 1

            summary.total_courses += 1

        summary.selection_complete = (summary.pending_courses == 0 and
                                     summary.waitlisted_courses == 0)

        return summary

    def get_course_selection_list(self, course_id: int) -> List[SelectionRecord]:
        """获取课程的选课名单"""
        records = []
        for record in self.records.values():
            if record.course_id == course_id:
                records.append(record)
        return sorted(records, key=lambda x: x.selected_at)

    def get_course_selection_report(self, academic_year: str,
                                    semester: int) -> CourseSelectionReport:
        """生成选课报表"""
        report = CourseSelectionReport(
            academic_year=academic_year,
            semester=semester
        )

        course_stats = {}
        class_stats = {}

        for record in self.records.values():
            if (record.academic_year == academic_year and
                record.semester == semester):

                report.total_selections += 1
                if record.status == SelectionStatus.APPROVED:
                    report.total_approved += 1

                # 课程统计
                if record.course_id not in course_stats:
                    course_stats[record.course_id] = {
                        "course_id": record.course_id,
                        "course_name": record.course_name,
                        "total": 0,
                        "approved": 0,
                        "pending": 0,
                        "waitlisted": 0,
                        "rejected": 0
                    }
                course_stats[record.course_id]["total"] += 1
                if record.status == SelectionStatus.APPROVED:
                    course_stats[record.course_id]["approved"] += 1
                elif record.status == SelectionStatus.PENDING:
                    course_stats[record.course_id]["pending"] += 1
                elif record.status == SelectionStatus.WAITLISTED:
                    course_stats[record.course_id]["waitlisted"] += 1
                elif record.status == SelectionStatus.REJECTED:
                    course_stats[record.course_id]["rejected"] += 1

                # 班级统计
                if record.student_class:
                    if record.student_class not in class_stats:
                        class_stats[record.student_class] = {
                            "class_name": record.student_class,
                            "total": 0,
                            "approved": 0
                        }
                    class_stats[record.student_class]["total"] += 1
                    if record.status == SelectionStatus.APPROVED:
                        class_stats[record.student_class]["approved"] += 1

        report.course_stats = list(course_stats.values())
        report.popular_courses = sorted(
            course_stats.values(),
            key=lambda x: x["approved"],
            reverse=True
        )[:10]
        report.low_demand_courses = sorted(
            course_stats.values(),
            key=lambda x: x["approved"]
        )[:10]
        report.class_stats = list(class_stats.values())

        report.total_courses = len(course_stats)
        report.total_students = len(set(r.student_id for r in self.records.values()
                                       if r.academic_year == academic_year and
                                       r.semester == semester))

        return report

    def validate_student_plan(self, student_id: int,
                             course_ids: List[int],
                             rule: SelectionRule) -> Tuple[bool, StudentCoursePlan]:
        """
        验证学生选课计划
        返回: (是否有效, 选课计划)
        """
        plan = StudentCoursePlan(
            student_id=student_id,
            academic_year=rule.academic_year,
            semester=rule.semester,
            courses=[]
        )

        # 获取已选课程
        existing = self.get_student_records(student_id, rule.academic_year, rule.semester)
        existing_approved = [r for r in existing if r.status == SelectionStatus.APPROVED]

        total_credits = sum(r.credits for r in existing_approved)

        # 检查新增课程
        for cid in course_ids:
            capacity = self.capacities.get(cid)
            if not capacity:
                capacity = CourseCapacity(course_id=cid, max_capacity=50)

            plan.courses.append({
                "course_id": cid,
                "name": f"Course {cid}",
                "credits": 3.0,
                "status": "new"
            })
            total_credits += 3.0

            # 检查容量
            if capacity.is_full:
                plan.warnings.append(f"课程{cid}已满")

        plan.total_credits = total_credits

        # 检查学分
        if total_credits > rule.max_credits:
            plan.warnings.append(f"学分超过限制: {total_credits} > {rule.max_credits}")

        if total_credits < rule.min_credits:
            plan.warnings.append(f"学分不足: {total_credits} < {rule.min_credits}")

        plan.suggestions = self._generate_suggestions(plan)

        return len(plan.warnings) == 0, plan

    def _has_time_conflict(self, student_id: int, course_id: int, rule: SelectionRule) -> bool:
        """检查时间冲突"""
        # 获取学生已选课程
        existing = self.get_student_records(student_id, rule.academic_year, rule.semester)
        approved = [r for r in existing if r.status == SelectionStatus.APPROVED]

        # 这里需要实际的课程时间表进行冲突检测
        # 简化实现：假设每门课每周5节课
        return False

    def _generate_suggestions(self, plan: StudentCoursePlan) -> List[str]:
        """生成优化建议"""
        suggestions = []

        if plan.has_conflicts:
            suggestions.append("存在时间冲突，请调整课程安排")

        if plan.total_credits < 20:
            suggestions.append("学分偏低，建议多选一门选修课")

        if plan.total_credits > 30:
            suggestions.append("学分偏高，请注意学习压力")

        return suggestions

    # ==================== 批量操作 ====================

    def batch_select(self, student_id: int,
                    course_ids: List[Tuple[int, float]],
                    rule_id: int,
                    student_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """批量选课"""
        results = {
            "success": [],
            "failed": [],
            "waitlisted": []
        }

        for course_id, credits in course_ids:
            success, record, msg = self.select_course(
                student_id, course_id, rule_id, credits, student_info
            )
            if success:
                if record.status == SelectionStatus.WAITLISTED:
                    results["waitlisted"].append({
                        "course_id": course_id,
                        "position": record.waitlist_position
                    })
                else:
                    results["success"].append(course_id)
            else:
                results["failed"].append({
                    "course_id": course_id,
                    "reason": msg
                })

        return results
