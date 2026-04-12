"""
毕业管理单元测试
测试毕业审核、证书管理、离校手续、校友管理等功能
"""
import unittest
from datetime import datetime, timedelta

from app.models.graduation import (
    GraduationAudit, GraduationCertificate, LeaveSchoolRecord,
    LeaveSchoolCheckpoint, AlumniRecord, GraduationStatistics,
    GraduationReport, GraduationRequirement,
    GraduationStatus, AuditType, CertificateStatus,
    LeaveSchoolStatus, CheckpointType
)
from app.services.graduation_service import GraduationService


class TestGraduationAudit(unittest.TestCase):
    """测试毕业审核"""

    def setUp(self):
        self.service = GraduationService()

    def test_create_audit(self):
        """测试创建审核记录"""
        audit = self.service.create_audit(
            student_id=1001,
            academic_year="2025-2026",
            semester=2,
            audit_type=AuditType.PRELIMINARY
        )

        self.assertIsNotNone(audit)
        self.assertEqual(audit.student_id, 1001)
        self.assertEqual(audit.academic_year, "2025-2026")
        self.assertEqual(audit.semester, 2)
        self.assertEqual(audit.audit_type, AuditType.PRELIMINARY)
        self.assertEqual(audit.status, GraduationStatus.PENDING)

    def test_update_academic_info(self):
        """测试更新学业信息"""
        audit = self.service.create_audit(
            student_id=1001,
            academic_year="2025-2026",
            semester=2
        )

        updated = self.service.update_audit_academic_info(
            audit_id=audit.id,
            total_credits=165,
            major_credits=85,
            elective_credits=25,
            practice_credits=20,
            completed_courses=45,
            gpa=3.5,
            passed_required=[1, 2, 3, 4, 5],
            failed_required=[6]
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated.total_credits, 165)
        self.assertEqual(updated.gpa, 3.5)
        self.assertEqual(len(updated.passed_required), 5)
        self.assertEqual(len(updated.failed_required), 1)

    def test_check_requirements_pass(self):
        """测试满足毕业要求"""
        audit = self.service.create_audit(
            student_id=1001,
            academic_year="2025-2026",
            semester=2
        )

        self.service.update_audit_academic_info(
            audit_id=audit.id,
            total_credits=165,
            major_credits=85,
            elective_credits=25,
            practice_credits=20,
            completed_courses=45,
            gpa=3.5,
            passed_required=[1, 2, 3, 4, 5],
            failed_required=[]
        )

        is_eligible, reasons = audit.check_requirements()
        self.assertTrue(is_eligible)
        self.assertEqual(len(reasons), 0)

    def test_check_requirements_fail(self):
        """测试不满足毕业要求"""
        audit = self.service.create_audit(
            student_id=1001,
            academic_year="2025-2026",
            semester=2
        )

        self.service.update_audit_academic_info(
            audit_id=audit.id,
            total_credits=100,  # 学分不足
            major_credits=50,   # 专业学分不足
            elective_credits=10,
            practice_credits=5,
            completed_courses=30,
            gpa=2.0,
            passed_required=[1, 2],
            failed_required=[3, 4, 5]  # 有未通过的必修课
        )

        is_eligible, reasons = audit.check_requirements()
        self.assertFalse(is_eligible)
        self.assertGreater(len(reasons), 0)

    def test_completion_rate(self):
        """测试完成度计算"""
        audit = self.service.create_audit(
            student_id=1001,
            academic_year="2025-2026",
            semester=2
        )

        self.service.update_audit_academic_info(
            audit_id=audit.id,
            total_credits=120,
            major_credits=60,
            elective_credits=15,
            practice_credits=10,
            completed_courses=35,
            gpa=2.8,
            passed_required=[1, 2, 3],
            failed_required=[4, 5]
        )

        rate = audit.get_completion_rate()
        self.assertGreater(rate, 0)
        self.assertLessEqual(rate, 1.0)

    def test_submit_audit_approved(self):
        """测试提交审核通过"""
        audit = self.service.create_audit(
            student_id=1001,
            academic_year="2025-2026",
            semester=2
        )

        self.service.update_audit_academic_info(
            audit_id=audit.id,
            total_credits=165,
            major_credits=85,
            elective_credits=25,
            practice_credits=20,
            completed_courses=45,
            gpa=3.5,
            passed_required=[1, 2, 3],
            failed_required=[]
        )

        submitted = self.service.submit_audit(
            audit_id=audit.id,
            auditor_id=1,
            comment="审核通过"
        )

        self.assertEqual(submitted.status, GraduationStatus.APPROVED)
        self.assertTrue(submitted.is_eligible)

    def test_submit_audit_rejected(self):
        """测试提交审核拒绝"""
        audit = self.service.create_audit(
            student_id=1001,
            academic_year="2025-2026",
            semester=2
        )

        self.service.update_audit_academic_info(
            audit_id=audit.id,
            total_credits=100,
            major_credits=50,
            elective_credits=10,
            practice_credits=5,
            completed_courses=30,
            gpa=2.0,
            passed_required=[],
            failed_required=[1, 2, 3, 4, 5]
        )

        submitted = self.service.submit_audit(
            audit_id=audit.id,
            auditor_id=1,
            comment="学分不足"
        )

        self.assertEqual(submitted.status, GraduationStatus.REJECTED)
        self.assertFalse(submitted.is_eligible)


class TestGraduationCertificate(unittest.TestCase):
    """测试毕业证书"""

    def setUp(self):
        self.service = GraduationService()

    def test_create_certificate(self):
        """测试创建证书"""
        cert = self.service.create_certificate(
            student_id=1001,
            student_name="张三",
            academic_year="2025-2026",
            major="计算机科学与技术",
            major_code="080901"
        )

        self.assertIsNotNone(cert)
        self.assertEqual(cert.student_id, 1001)
        self.assertEqual(cert.student_name, "张三")
        self.assertIsNotNone(cert.certificate_number)
        self.assertGreaterEqual(len(cert.certificate_number), 8)  # 至少8位

    def test_certificate_number_generation(self):
        """测试证书编号生成"""
        cert = self.service.create_certificate(
            student_id=1001,
            student_name="李四",
            academic_year="2025-2026"
        )

        cert_no = cert.generate_certificate_number()
        self.assertGreaterEqual(len(cert_no), 8)  # 至少8位
        self.assertTrue(cert_no.startswith("26"))  # 毕业年份后两位

    def test_issue_certificate(self):
        """测试发放证书"""
        cert = self.service.create_certificate(
            student_id=1001,
            student_name="王五",
            academic_year="2025-2026"
        )

        issued = self.service.issue_certificate(
            certificate_id=cert.id,
            issued_by=1
        )

        self.assertEqual(issued.status, CertificateStatus.ISSUED)
        self.assertIsNotNone(issued.issued_at)

    def test_verify_certificate_valid(self):
        """测试验证有效证书"""
        cert = self.service.create_certificate(
            student_id=1001,
            student_name="赵六",
            academic_year="2025-2026"
        )

        self.service.issue_certificate(cert.id, 1)

        is_valid, result = self.service.verify_certificate(
            cert.certificate_number
        )

        self.assertTrue(is_valid)
        self.assertEqual(result, "赵六")

    def test_verify_certificate_invalid(self):
        """测试验证无效证书"""
        is_valid, result = self.service.verify_certificate("INVALID123")
        self.assertFalse(is_valid)
        self.assertEqual(result, "证书不存在")


class TestLeaveSchool(unittest.TestCase):
    """测试离校手续"""

    def setUp(self):
        self.service = GraduationService()

    def test_create_leave_record(self):
        """测试创建离校记录"""
        record = self.service.create_leave_record(
            student_id=1001,
            student_name="张三",
            academic_year="2025-2026",
            semester=2
        )

        self.assertIsNotNone(record)
        self.assertEqual(record.student_id, 1001)
        self.assertEqual(len(record.checkpoints), 5)  # 默认5个检查点

    def test_complete_checkpoint(self):
        """测试完成检查点"""
        record = self.service.create_leave_record(
            student_id=1001,
            student_name="李四",
            academic_year="2025-2026",
            semester=2
        )

        updated = self.service.complete_checkpoint(
            leave_id=record.id,
            checkpoint_type=CheckpointType.LIBRARY,
            checked_by=1,
            result="已清退"
        )

        self.assertIsNotNone(updated)
        library_cp = next(
            c for c in updated.checkpoints
            if c.checkpoint_type == CheckpointType.LIBRARY
        )
        self.assertEqual(library_cp.status, LeaveSchoolStatus.COMPLETED)

    def test_exempt_checkpoint(self):
        """测试豁免检查点"""
        record = self.service.create_leave_record(
            student_id=1001,
            student_name="王五",
            academic_year="2025-2026",
            semester=2
        )

        updated = self.service.exempt_checkpoint(
            leave_id=record.id,
            checkpoint_type=CheckpointType.EQUIPMENT,
            reason="已损坏，无法归还",
            exempted_by=1
        )

        self.assertIsNotNone(updated)
        equipment_cp = next(
            c for c in updated.checkpoints
            if c.checkpoint_type == CheckpointType.EQUIPMENT
        )
        self.assertEqual(equipment_cp.status, LeaveSchoolStatus.EXEMPTED)

    def test_leave_completion(self):
        """测试离校完成"""
        record = self.service.create_leave_record(
            student_id=1001,
            student_name="赵六",
            academic_year="2025-2026",
            semester=2
        )

        # 完成所有检查点
        for cp_type in CheckpointType:
            self.service.complete_checkpoint(
                leave_id=record.id,
                checkpoint_type=cp_type,
                checked_by=1
            )

        final_record = self.service.get_leave_record(record.id)
        self.assertEqual(final_record.status, LeaveSchoolStatus.COMPLETED)
        self.assertTrue(final_record.is_completed())

    def test_completion_rate(self):
        """测试办理进度"""
        record = self.service.create_leave_record(
            student_id=1001,
            student_name="孙七",
            academic_year="2025-2026",
            semester=2
        )

        rate = record.get_completion_rate()
        self.assertEqual(rate, 0.0)

        # 完成2个检查点
        self.service.complete_checkpoint(
            leave_id=record.id,
            checkpoint_type=CheckpointType.LIBRARY,
            checked_by=1
        )
        self.service.complete_checkpoint(
            leave_id=record.id,
            checkpoint_type=CheckpointType.FINANCIAL,
            checked_by=1
        )

        updated = self.service.get_leave_record(record.id)
        rate = updated.get_completion_rate()
        self.assertGreater(rate, 0.0)


class TestAlumni(unittest.TestCase):
    """测试校友管理"""

    def setUp(self):
        self.service = GraduationService()

    def test_create_alumni(self):
        """测试创建校友"""
        alumni = self.service.create_alumni(
            student_id=1001,
            name="张三",
            admission_year=2022,
            graduation_year=2026,
            major="计算机科学与技术"
        )

        self.assertIsNotNone(alumni)
        self.assertEqual(alumni.student_id, 1001)
        self.assertEqual(alumni.graduation_year, 2026)

    def test_convert_to_alumni(self):
        """测试毕业生转校友"""
        alumni = self.service.convert_to_alumni(
            student_id=1002,
            name="李四",
            admission_year=2022,
            graduation_year=2026,
            major="软件工程"
        )

        self.assertIsNotNone(alumni)
        self.assertEqual(alumni.name, "李四")

    def test_update_alumni_info(self):
        """测试更新校友信息"""
        alumni = self.service.create_alumni(
            student_id=1001,
            name="王五",
            admission_year=2022,
            graduation_year=2026
        )

        updated = self.service.update_alumni_info(
            alumni_id=alumni.id,
            employer="某科技公司",
            position="软件工程师",
            industry="互联网",
            phone="13800138000",
            email="wang@example.com"
        )

        self.assertEqual(updated.employer, "某科技公司")
        self.assertEqual(updated.position, "软件工程师")
        self.assertIsNotNone(updated.last_contact)

    def test_add_contribution(self):
        """测试添加贡献值"""
        alumni = self.service.create_alumni(
            student_id=1001,
            name="赵六",
            admission_year=2022,
            graduation_year=2026
        )

        alumni.add_contribution(2000)
        self.assertEqual(alumni.contributions, 2000)
        self.assertEqual(alumni.alumni_level, "silver")

        alumni.add_contribution(5000)
        self.assertEqual(alumni.contributions, 7000)
        self.assertEqual(alumni.alumni_level, "gold")

        alumni.add_contribution(5000)
        self.assertEqual(alumni.contributions, 12000)
        self.assertEqual(alumni.alumni_level, "platinum")

    def test_search_alumni(self):
        """测试搜索校友"""
        self.service.create_alumni(
            student_id=1001,
            name="张三",
            admission_year=2022,
            graduation_year=2026,
            major="计算机科学与技术"
        )
        self.service.create_alumni(
            student_id=1002,
            name="李四",
            admission_year=2022,
            graduation_year=2026,
            major="软件工程"
        )
        self.service.create_alumni(
            student_id=1003,
            name="王五",
            admission_year=2021,
            graduation_year=2025,
            major="计算机科学与技术"
        )

        # 按专业搜索
        results = self.service.search_alumni(major="计算机")
        self.assertEqual(len(results), 2)

        # 按毕业年份搜索
        results = self.service.search_alumni(graduation_year=2026)
        self.assertEqual(len(results), 2)


class TestGraduationReport(unittest.TestCase):
    """测试毕业报告"""

    def setUp(self):
        self.service = GraduationService()

    def test_generate_report(self):
        """测试生成毕业报告"""
        audit = self.service.create_audit(
            student_id=1001,
            academic_year="2025-2026",
            semester=2
        )

        self.service.update_audit_academic_info(
            audit_id=audit.id,
            total_credits=165,
            major_credits=85,
            elective_credits=25,
            practice_credits=20,
            completed_courses=45,
            gpa=3.5,
            passed_required=[1, 2, 3],
            failed_required=[]
        )

        report = self.service.generate_graduation_report(audit.id)

        self.assertIsNotNone(report)
        self.assertEqual(report.student_id, 1001)
        self.assertTrue(report.is_eligible)
        self.assertGreater(report.completion_rate, 0.9)


class TestGraduationStatistics(unittest.TestCase):
    """测试毕业统计"""

    def setUp(self):
        self.service = GraduationService()

    def test_graduation_rate(self):
        """测试毕业率计算"""
        # 创建多个审核记录
        self.service.create_audit(1001, "2025-2026", 2)
        self.service.create_audit(1002, "2025-2026", 2)
        self.service.create_audit(1003, "2025-2026", 2)

        stats = self.service.get_graduation_statistics("2025-2026")

        self.assertEqual(stats.total_students, 3)


if __name__ == "__main__":
    unittest.main()
