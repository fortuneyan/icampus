"""
成绩报表单元测试
测试学生报表、班级报表、科目报表、考试报表、趋势分析等功能
"""
import unittest
from datetime import datetime

from app.services.score_report_service import (
    ScoreReportService, ReportType, GradeLevel, ScoreDistribution,
    StudentScore, StudentReport, ClassReport, SubjectReport,
    ExamReport, TrendReport
)


class TestScoreDistribution(unittest.TestCase):
    """测试分数分布"""

    def test_add_score(self):
        """测试添加分数"""
        dist = ScoreDistribution()
        dist.add_score(85)
        self.assertEqual(dist.total, 1)
        self.assertEqual(dist.bins["80-89"], 1)

    def test_get_distribution(self):
        """测试获取分布比例"""
        dist = ScoreDistribution()
        for score in [55, 65, 75, 85, 95]:
            dist.add_score(score)

        result = dist.get_distribution()
        self.assertEqual(result["0-59"], 0.2)
        self.assertEqual(result["90-100"], 0.2)

    def test_pass_rate(self):
        """测试及格率"""
        dist = ScoreDistribution()
        for score in [55, 65, 75, 85]:
            dist.add_score(score)

        self.assertEqual(dist.get_pass_rate(), 0.75)


class TestStudentScore(unittest.TestCase):
    """测试学生成绩"""

    def test_create_student_score(self):
        """测试创建学生成绩"""
        score = StudentScore(
            student_id=1001,
            student_name="张三",
            exam_id=1,
            subject_id=1,
            subject_name="数学",
            score=85,
            full_score=100,
            grade_level=GradeLevel.GOOD  # 手动设置等级
        )

        self.assertEqual(score.student_id, 1001)
        self.assertEqual(score.score, 85)
        self.assertEqual(score.grade_level, GradeLevel.GOOD)

    def test_percentile(self):
        """测试百分位计算"""
        score = StudentScore(
            student_id=1001,
            student_name="张三",
            exam_id=1,
            subject_id=1,
            subject_name="数学",
            score=90,
            full_score=100
        )

        self.assertEqual(score.get_percentile(), 90.0)

    def test_is_pass(self):
        """测试是否及格"""
        pass_score = StudentScore(
            student_id=1001,
            student_name="张三",
            exam_id=1,
            subject_id=1,
            subject_name="数学",
            score=60
        )
        self.assertTrue(pass_score.is_pass())

        fail_score = StudentScore(
            student_id=1002,
            student_name="李四",
            exam_id=1,
            subject_id=1,
            subject_name="数学",
            score=55
        )
        self.assertFalse(fail_score.is_pass())


class TestStudentReport(unittest.TestCase):
    """测试学生报表"""

    def test_create_student_report(self):
        """测试创建学生报表"""
        report = StudentReport(
            student_id=1001,
            student_name="张三",
            academic_year="2025-2026",
            semester=1,
            total_courses=8,
            passed_courses=7,
            failed_courses=1,
            total_score=680,
            average_score=85.0,
            highest_score=95,
            lowest_score=55,
            gpa=3.2
        )

        self.assertEqual(report.student_id, 1001)
        self.assertEqual(report.total_courses, 8)
        self.assertEqual(report.get_pass_rate(), 0.875)

    def test_get_completion_rate(self):
        """测试完成率"""
        report = StudentReport(
            student_id=1001,
            student_name="张三",
            academic_year="2025-2026",
            semester=1,
            total_courses=10,
            passed_courses=8,
            failed_courses=2
        )

        self.assertEqual(report.get_completion_rate(), 0.8)


class TestScoreReportService(unittest.TestCase):
    """测试成绩报表服务"""

    def setUp(self):
        self.service = ScoreReportService()

    def test_add_student_score(self):
        """测试添加学生成绩"""
        score = self.service.add_student_score(
            student_id=1001,
            student_name="张三",
            exam_id=1,
            subject_id=1,
            subject_name="数学",
            score=85
        )

        self.assertIsNotNone(score)
        self.assertEqual(score.student_id, 1001)
        self.assertEqual(score.score, 85)
        self.assertEqual(score.grade_level, GradeLevel.GOOD)

    def test_get_student_scores(self):
        """测试获取学生成绩列表"""
        self.service.add_student_score(1001, "张三", 1, 1, "数学", 85)
        self.service.add_student_score(1001, "张三", 1, 2, "语文", 90)

        scores = self.service.get_student_scores(1001)
        self.assertEqual(len(scores), 2)

    def test_generate_student_report(self):
        """测试生成学生报表"""
        self.service.add_student_score(1001, "张三", 1, 1, "数学", 85)
        self.service.add_student_score(1001, "张三", 1, 2, "语文", 90)
        self.service.add_student_score(1001, "张三", 1, 3, "英语", 78)
        self.service.add_student_score(1001, "张三", 1, 4, "物理", 55)  # 不及格

        report = self.service.generate_student_report(
            student_id=1001,
            student_name="张三",
            academic_year="2025-2026",
            semester=1
        )

        self.assertEqual(report.total_courses, 4)
        self.assertEqual(report.passed_courses, 3)
        self.assertEqual(report.failed_courses, 1)
        self.assertGreater(report.average_score, 70)
        self.assertGreater(report.gpa, 2.0)

    def test_generate_class_report(self):
        """测试生成班级报表"""
        # 添加多个学生成绩
        for student_id in range(1001, 1011):
            for subject_id in range(1, 5):
                score = 70 + (student_id - 1000) + (subject_id * 2)
                self.service.add_student_score(
                    student_id, f"学生{student_id}", 1, subject_id,
                    f"科目{subject_id}", min(score, 100)
                )

        report = self.service.generate_class_report(
            class_id=1,
            class_name="高一(1)班",
            academic_year="2025-2026",
            semester=1,
            student_ids=list(range(1001, 1011))
        )

        self.assertEqual(report.class_id, 1)
        self.assertEqual(report.total_students, 10)
        self.assertGreater(report.class_average, 0)

    def test_generate_subject_report(self):
        """测试生成科目报表"""
        for student_id in range(1001, 1021):
            score = 60 + (student_id - 1000)
            self.service.add_student_score(
                student_id, f"学生{student_id}", 1, 1, "数学", min(score, 100)
            )

        report = self.service.generate_subject_report(
            subject_id=1,
            subject_name="数学",
            academic_year="2025-2026",
            semester=1
        )

        self.assertEqual(report.subject_id, 1)
        self.assertEqual(report.total_students, 20)
        self.assertGreater(report.subject_average, 0)

    def test_generate_exam_report(self):
        """测试生成考试报表"""
        for student_id in range(1001, 1021):
            for subject_id in range(1, 4):
                score = 65 + (student_id - 1000) + (subject_id * 3)
                self.service.add_student_score(
                    student_id, f"学生{student_id}", 1, subject_id,
                    f"科目{subject_id}", min(score, 100)
                )

        report = self.service.generate_exam_report(
            exam_id=1,
            exam_name="期中考试",
            academic_year="2025-2026",
            semester=1,
            exam_date="2025-11-15"
        )

        self.assertEqual(report.exam_id, 1)
        self.assertEqual(report.total_students, 20)
        self.assertEqual(report.total_subjects, 3)
        self.assertGreater(report.overall_average, 0)

    def test_compare_students(self):
        """测试学生对比分析"""
        self.service.add_student_score(1001, "张三", 1, 1, "数学", 90)
        self.service.add_student_score(1002, "李四", 1, 1, "数学", 80)
        self.service.add_student_score(1003, "王五", 1, 1, "数学", 70)

        results = self.service.compare_students(
            student_ids=[1001, 1002, 1003],
            academic_year="2025-2026",
            semester=1
        )

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["rank"], 1)
        self.assertEqual(results[0]["student_id"], 1001)

    def test_export_student_report(self):
        """测试导出学生报表"""
        self.service.add_student_score(1001, "张三", 1, 1, "数学", 85)
        self.service.add_student_score(1001, "张三", 1, 2, "语文", 90)

        data = self.service.export_student_report(
            student_id=1001,
            academic_year="2025-2026",
            semester=1,
            format="json"
        )

        self.assertEqual(data["student_id"], 1001)
        self.assertEqual(len(data["grades"]), 2)

    def test_grade_levels(self):
        """测试成绩等级"""
        # 优秀
        score_a = self.service.add_student_score(1001, "张三", 1, 1, "数学", 95)
        self.assertEqual(score_a.grade_level, GradeLevel.EXCELLENT)

        # 良好
        score_b = self.service.add_student_score(1002, "李四", 1, 1, "数学", 85)
        self.assertEqual(score_b.grade_level, GradeLevel.GOOD)

        # 中等
        score_c = self.service.add_student_score(1003, "王五", 1, 1, "数学", 75)
        self.assertEqual(score_c.grade_level, GradeLevel.AVERAGE)

        # 及格
        score_d = self.service.add_student_score(1004, "赵六", 1, 1, "数学", 65)
        self.assertEqual(score_d.grade_level, GradeLevel.PASS)

        # 不及格
        score_f = self.service.add_student_score(1005, "孙七", 1, 1, "数学", 55)
        self.assertEqual(score_f.grade_level, GradeLevel.FAIL)


class TestReportGeneration(unittest.TestCase):
    """测试报表生成"""

    def setUp(self):
        self.service = ScoreReportService()

    def test_multiple_exams(self):
        """测试多次考试"""
        # 第一次考试
        self.service.add_student_score(1001, "张三", 1, 1, "数学", 75)
        # 第二次考试
        self.service.add_student_score(1001, "张三", 2, 1, "数学", 80)
        # 第三次考试
        self.service.add_student_score(1001, "张三", 3, 1, "数学", 88)

        report = self.service.generate_student_report(
            student_id=1001,
            student_name="张三",
            academic_year="2025-2026",
            semester=1
        )

        self.assertEqual(report.total_courses, 3)

    def test_score_variance(self):
        """测试分数标准差"""
        for i in range(10):
            score = 70 + (i * 3)
            self.service.add_student_score(
                1001 + i, f"学生{i}", 1, 1, "数学", min(score, 100)
            )

        report = self.service.generate_subject_report(
            subject_id=1,
            subject_name="数学",
            academic_year="2025-2026",
            semester=1
        )

        self.assertGreater(report.score_std, 0)


if __name__ == "__main__":
    unittest.main()
