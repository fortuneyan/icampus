# -*- coding: utf-8 -*-
"""
选课管理单元测试
T6: 选课管理
"""
import unittest
from datetime import datetime, timedelta
from app.models.course_selection_rule import (
    SelectionRule, SelectionMode, SelectionStrategy,
    RuleStatus, CourseCapacity, SelectionPriority, CourseConflict
)
from app.models.course_selection_record import (
    SelectionRecord, WaitlistRecord, CourseSelectionSummary,
    CourseSelectionReport, StudentCoursePlan, LotteryResult, SelectionStatus
)
from app.services.course_selection_service import CourseSelectionService


class TestSelectionRule(unittest.TestCase):
    """测试选课规则"""

    def setUp(self):
        self.rule = SelectionRule(
            id=1,
            name="Test Rule",
            academic_year="2025-2026",
            semester=1,
            period_type="first",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(days=7),
            min_credits=15,
            max_credits=30,
            default_credits=25,
            min_courses=5,
            max_courses=10,
            status="active"
        )

    def test_rule_creation(self):
        """测试规则创建"""
        self.assertEqual(self.rule.name, "Test Rule")
        self.assertEqual(self.rule.academic_year, "2025-2026")
        self.assertEqual(self.rule.semester, 1)
        self.assertEqual(self.rule.status, "active")

    def test_rule_is_active(self):
        """测试规则激活状态"""
        self.assertTrue(self.rule.is_active())

    def test_rule_is_expired(self):
        """测试规则过期状态"""
        expired_rule = SelectionRule(
            id=2,
            name="Expired Rule",
            academic_year="2024-2025",
            semester=1,
            period_type="first",
            start_time=datetime.now() - timedelta(days=14),
            end_time=datetime.now() - timedelta(days=7),
            status="active"
        )
        self.assertTrue(expired_rule.is_expired())

    def test_can_select_within_limits(self):
        """测试学分范围内选课"""
        can_select, reason = self.rule.can_select(20, 5)
        self.assertTrue(can_select)

    def test_can_select_credits_too_high(self):
        """测试学分超限"""
        # 设置一个高学分值
        rule = SelectionRule(
            id=1,
            name="Test Rule",
            academic_year="2025-2026",
            semester=1,
            period_type="first",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(days=7),
            max_credits=30,
            max_courses=10,
            status="active"
        )
        can_select, reason = rule.can_select(35, 5)  # 超过30学分
        self.assertFalse(can_select)
        self.assertIn("学分超限", reason)


class TestCourseCapacity(unittest.TestCase):
    """测试课程容量"""

    def test_capacity_check_available(self):
        """测试容量检查-可加入"""
        capacity = CourseCapacity(course_id=1, max_capacity=50)
        available, msg = capacity.check_availability()
        self.assertTrue(available)

    def test_capacity_check_full(self):
        """测试容量检查-已满"""
        capacity = CourseCapacity(course_id=1, max_capacity=50, current_count=50)
        capacity.is_full = True
        available, msg = capacity.check_availability()
        self.assertFalse(available)
        self.assertEqual(msg, "课程已满")

    def test_waitlist_check_available(self):
        """测试候补检查-可加入"""
        capacity = CourseCapacity(course_id=1, max_capacity=50, current_count=50)
        available, msg = capacity.check_waitlist()
        self.assertTrue(available)

    def test_waitlist_check_full(self):
        """测试候补检查-队列已满"""
        capacity = CourseCapacity(course_id=1, max_capacity=50, current_count=50, waitlist_count=25)
        available, msg = capacity.check_waitlist()
        self.assertFalse(available)


class TestSelectionRecord(unittest.TestCase):
    """测试选课记录"""

    def setUp(self):
        self.record = SelectionRecord(
            id=1,
            student_id=1001,
            student_name="张三",
            course_id=101,
            course_name="高等数学",
            rule_id=1,
            academic_year="2025-2026",
            semester=1,
            credits=4.0,
            status="pending"
        )

    def test_record_creation(self):
        """测试记录创建"""
        self.assertEqual(self.record.student_id, 1001)
        self.assertEqual(self.record.course_id, 101)
        self.assertEqual(self.record.status, "pending")

    def test_record_is_active(self):
        """测试记录有效性"""
        self.record.status = "approved"
        self.assertTrue(self.record.is_active())

    def test_can_withdraw_pending(self):
        """测试待审核状态可撤选"""
        self.record.status = "pending"
        self.assertTrue(self.record.can_withdraw())

    def test_can_withdraw_waitlisted(self):
        """测试候补状态可撤选"""
        self.record.status = "waitlisted"
        self.assertTrue(self.record.can_withdraw())

    def test_can_drop_approved(self):
        """测试已通过状态可退选"""
        self.record.status = "approved"
        self.assertTrue(self.record.can_drop())

    def test_can_drop_pending(self):
        """测试待审核状态不可退选"""
        self.record.status = "pending"
        self.assertFalse(self.record.can_drop())


class TestCourseSelectionService(unittest.TestCase):
    """测试选课服务"""

    def setUp(self):
        self.service = CourseSelectionService()

        # 创建测试规则
        rule_data = {
            "id": 1,
            "name": "Test Rule",
            "academic_year": "2025-2026",
            "semester": 1,
            "period_type": "first",
            "start_time": datetime.now(),
            "end_time": datetime.now() + timedelta(days=7),
            "min_credits": 15,
            "max_credits": 30,
            "default_credits": 25,
            "min_courses": 5,
            "max_courses": 10,
            "status": "active"
        }
        self.service.rules[1] = SelectionRule(**rule_data)

        # 设置课程容量
        self.service.capacities[101] = CourseCapacity(
            course_id=101,
            max_capacity=50,
            current_count=0
        )

    def test_service_initialization(self):
        """测试服务初始化"""
        self.assertIsNotNone(self.service)
        self.assertEqual(len(self.service.rules), 1)
        self.assertEqual(len(self.service.records), 0)

    def test_select_course_success(self):
        """测试选课成功"""
        success, record, msg = self.service.select_course(
            student_id=1001,
            course_id=101,
            rule_id=1,
            credits=4.0,
            student_info={"name": "张三", "class": "计算机1班"}
        )
        self.assertTrue(success)
        self.assertIsNotNone(record)
        self.assertEqual(record.student_id, 1001)

    def test_select_course_rule_not_found(self):
        """测试选课失败-规则不存在"""
        success, record, msg = self.service.select_course(
            student_id=1001,
            course_id=101,
            rule_id=999,
            credits=4.0
        )
        self.assertFalse(success)
        self.assertIsNone(record)
        self.assertIn("规则不存在", msg)

    def test_get_student_records(self):
        """测试获取学生选课记录"""
        # 选多门课
        self.service.select_course(1001, 101, 1, 4.0)
        self.service.select_course(1002, 101, 1, 4.0)  # 其他学生

        records = self.service.get_student_records(1001, "2025-2026", 1)
        self.assertGreaterEqual(len(records), 1)

    def test_get_student_summary(self):
        """测试获取学生选课汇总"""
        # 选课
        self.service.select_course(1001, 101, 1, 4.0)

        summary = self.service.get_student_summary(1001, "2025-2026", 1)
        self.assertEqual(summary.student_id, 1001)

    def test_batch_select(self):
        """测试批量选课"""
        results = self.service.batch_select(
            student_id=1001,
            course_ids=[(101, 4.0)],
            rule_id=1
        )
        self.assertIsNotNone(results)


class TestLottery(unittest.TestCase):
    """测试抽签功能"""

    def setUp(self):
        self.service = CourseSelectionService()

        # 创建规则
        rule_data = {
            "id": 1,
            "name": "Test Rule",
            "academic_year": "2025-2026",
            "semester": 1,
            "period_type": "first",
            "start_time": datetime.now(),
            "end_time": datetime.now() + timedelta(days=7),
            "status": "active"
        }
        self.service.rules[1] = SelectionRule(**rule_data)

        # 设置课程容量
        self.service.capacities[201] = CourseCapacity(
            course_id=201,
            max_capacity=2,
            current_count=0
        )

    def test_lottery_result_creation(self):
        """测试抽签结果创建"""
        result = LotteryResult(
            lottery_id="lottery_1",
            course_id=201,
            rule_id=1,
            max_capacity=50,
            total_participants=10,
            winners=[1, 2, 3],
            losers=[4, 5, 6, 7, 8, 9, 10],
            status="completed"
        )
        self.assertEqual(len(result.winners), 3)
        self.assertEqual(result.get_winning_rate(), 0.3)


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def setUp(self):
        self.service = CourseSelectionService()

    def test_empty_records(self):
        """测试空记录查询"""
        records = self.service.get_student_records(9999, "2025-2026", 1)
        self.assertEqual(len(records), 0)

    def test_summary_no_records(self):
        """测试无记录汇总"""
        summary = self.service.get_student_summary(9999, "2025-2026", 1)
        self.assertEqual(summary.student_id, 9999)

    def test_invalid_rule(self):
        """测试无效规则"""
        success, rule, msg = self.service.create_rule({
            "name": "Test",
            "academic_year": "2025-2026",
            "semester": 1,
            "period_type": "first",
            "start_time": datetime.now(),
            "end_time": datetime.now() - timedelta(days=1)  # 结束时间早于开始时间
        })
        self.assertFalse(success)


if __name__ == '__main__':
    unittest.main()
