"""
毕业审核服务
提供毕业资格审核、证书管理、离校手续、校友管理等业务逻辑
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import random

from app.models.graduation import (
    GraduationAudit, GraduationCertificate, LeaveSchoolRecord,
    LeaveSchoolCheckpoint, AlumniRecord, GraduationStatistics,
    GraduationReport, GraduationRequirement, GraduationStatus,
    AuditType, CertificateStatus, LeaveSchoolStatus, CheckpointType
)


class GraduationService:
    """毕业审核服务"""

    def __init__(self):
        self._audits: Dict[int, GraduationAudit] = {}
        self._certificates: Dict[int, GraduationCertificate] = {}
        self._leave_records: Dict[int, LeaveSchoolRecord] = {}
        self._alumni_records: Dict[int, AlumniRecord] = {}
        self._next_audit_id = 1
        self._next_certificate_id = 1
        self._next_leave_id = 1
        self._next_alumni_id = 1

    # ==================== 毕业审核 ====================

    def create_audit(
        self,
        student_id: int,
        academic_year: str,
        semester: int,
        audit_type: AuditType = AuditType.PRELIMINARY
    ) -> GraduationAudit:
        """
        创建毕业审核记录
        """
        audit = GraduationAudit(
            id=self._next_audit_id,
            student_id=student_id,
            academic_year=academic_year,
            semester=semester,
            audit_type=audit_type,
            status=GraduationStatus.PENDING,
            requirements=GraduationRequirement()
        )
        self._audits[self._next_audit_id] = audit
        self._next_audit_id += 1
        return audit

    def update_audit_academic_info(
        self,
        audit_id: int,
        total_credits: float,
        major_credits: float,
        elective_credits: float,
        practice_credits: float,
        completed_courses: int,
        gpa: float,
        passed_required: List[int],
        failed_required: List[int]
    ) -> Optional[GraduationAudit]:
        """
        更新审核记录的学业信息
        """
        audit = self._audits.get(audit_id)
        if not audit:
            return None

        audit.total_credits = total_credits
        audit.major_credits = major_credits
        audit.elective_credits = elective_credits
        audit.practice_credits = practice_credits
        audit.completed_courses = completed_courses
        audit.gpa = gpa
        audit.passed_required = passed_required
        audit.failed_required = failed_required
        audit.updated_at = datetime.now()

        # 检查是否满足毕业要求
        audit.check_requirements()

        return audit

    def check_graduation_eligibility(
        self,
        student_id: int,
        academic_year: str
    ) -> Tuple[bool, List[str], float]:
        """
        检查学生毕业资格
        返回: (是否满足条件, 不满足原因列表, 完成度)
        """
        # 查找最新的审核记录
        audit = None
        for a in self._audits.values():
            if a.student_id == student_id and a.academic_year == academic_year:
                if audit is None or a.id > audit.id:
                    audit = a

        if not audit:
            return False, ["未找到毕业审核记录"], 0.0

        is_eligible, reasons = audit.check_requirements()
        return is_eligible, reasons, audit.get_completion_rate()

    def submit_audit(
        self,
        audit_id: int,
        auditor_id: int,
        comment: str = ""
    ) -> Optional[GraduationAudit]:
        """
        提交审核
        """
        audit = self._audits.get(audit_id)
        if not audit:
            return None

        # 再次检查资格
        audit.check_requirements()

        if audit.is_eligible:
            audit.status = GraduationStatus.APPROVED
        else:
            audit.status = GraduationStatus.REJECTED

        audit.auditor_id = auditor_id
        audit.audit_time = datetime.now()
        audit.audit_comment = comment
        audit.updated_at = datetime.now()

        return audit

    def batch_audit(
        self,
        audit_ids: List[int],
        auditor_id: int,
        approved: bool = True,
        comment: str = ""
    ) -> Dict[str, Any]:
        """
        批量审核
        """
        results = {
            "total": len(audit_ids),
            "approved": 0,
            "rejected": 0,
            "failed": 0,
            "details": []
        }

        for audit_id in audit_ids:
            audit = self._audits.get(audit_id)
            if not audit:
                results["failed"] += 1
                results["details"].append({
                    "audit_id": audit_id,
                    "status": "failed",
                    "reason": "审核记录不存在"
                })
                continue

            audit.check_requirements()
            if approved and audit.is_eligible:
                audit.status = GraduationStatus.APPROVED
                results["approved"] += 1
            else:
                audit.status = GraduationStatus.REJECTED
                results["rejected"] += 1

            audit.auditor_id = auditor_id
            audit.audit_time = datetime.now()
            audit.audit_comment = comment

            results["details"].append({
                "audit_id": audit_id,
                "student_id": audit.student_id,
                "status": "approved" if audit.status == GraduationStatus.APPROVED else "rejected",
                "is_eligible": audit.is_eligible
            })

        return results

    def get_audit(self, audit_id: int) -> Optional[GraduationAudit]:
        """获取审核记录"""
        return self._audits.get(audit_id)

    def get_student_audits(self, student_id: int) -> List[GraduationAudit]:
        """获取学生的所有审核记录"""
        return [
            a for a in self._audits.values()
            if a.student_id == student_id
        ]

    def get_pending_audits(
        self,
        academic_year: Optional[str] = None
    ) -> List[GraduationAudit]:
        """获取待审核记录"""
        audits = [
            a for a in self._audits.values()
            if a.status == GraduationStatus.PENDING
        ]

        if academic_year:
            audits = [a for a in audits if a.academic_year == academic_year]

        return audits

    # ==================== 毕业证书 ====================

    def create_certificate(
        self,
        student_id: int,
        student_name: str,
        academic_year: str,
        major: str = "",
        major_code: str = ""
    ) -> GraduationCertificate:
        """
        创建毕业证书
        """
        now = datetime.now()
        cert = GraduationCertificate(
            id=self._next_certificate_id,
            student_id=student_id,
            student_name=student_name,
            certificate_number="",  # 待生成
            academic_year=academic_year,
            graduation_year=now.year,
            graduation_month=now.month,
            major=major,
            major_code=major_code,
            status=CertificateStatus.PENDING
        )

        # 生成证书编号
        cert.certificate_number = cert.generate_certificate_number()

        self._certificates[self._next_certificate_id] = cert
        self._next_certificate_id += 1

        return cert

    def issue_certificate(
        self,
        certificate_id: int,
        issued_by: int
    ) -> Optional[GraduationCertificate]:
        """
        发放证书
        """
        cert = self._certificates.get(certificate_id)
        if not cert:
            return None

        cert.status = CertificateStatus.ISSUED
        cert.issued_by = issued_by
        cert.issued_at = datetime.now()
        cert.updated_at = datetime.now()

        return cert

    def print_certificate(
        self,
        certificate_id: int,
        printed_by: int
    ) -> Optional[GraduationCertificate]:
        """
        打印证书
        """
        cert = self._certificates.get(certificate_id)
        if not cert:
            return None

        cert.status = CertificateStatus.PRINTED
        cert.printed_by = printed_by
        cert.printed_at = datetime.now()
        cert.updated_at = datetime.now()

        return cert

    def revoke_certificate(
        self,
        certificate_id: int,
        reason: str = ""
    ) -> Optional[GraduationCertificate]:
        """
        吊销证书
        """
        cert = self._certificates.get(certificate_id)
        if not cert:
            return None

        cert.status = CertificateStatus.REVOKED
        cert.remarks = reason
        cert.updated_at = datetime.now()

        return cert

    def verify_certificate(
        self,
        certificate_number: str
    ) -> Tuple[bool, Optional[str]]:
        """
        验证证书
        返回: (是否有效, 学生姓名或错误信息)
        """
        for cert in self._certificates.values():
            if cert.certificate_number == certificate_number:
                if cert.is_valid():
                    return True, cert.student_name
                else:
                    return False, f"证书已{cert.status.value}"

        return False, "证书不存在"

    def get_certificate(self, certificate_id: int) -> Optional[GraduationCertificate]:
        """获取证书"""
        return self._certificates.get(certificate_id)

    def get_student_certificate(
        self,
        student_id: int
    ) -> Optional[GraduationCertificate]:
        """获取学生的证书"""
        for cert in self._certificates.values():
            if cert.student_id == student_id:
                return cert
        return None

    # ==================== 离校手续 ====================

    def create_leave_record(
        self,
        student_id: int,
        student_name: str,
        academic_year: str,
        semester: int,
        leave_type: str = "graduation"
    ) -> LeaveSchoolRecord:
        """
        创建离校记录
        """
        record = LeaveSchoolRecord(
            id=self._next_leave_id,
            student_id=student_id,
            student_name=student_name,
            academic_year=academic_year,
            semester=semester,
            leave_type=leave_type,
            status=LeaveSchoolStatus.PENDING
        )

        # 添加默认检查点
        default_checkpoints = [
            LeaveSchoolCheckpoint(
                checkpoint_type=CheckpointType.LIBRARY,
                name="图书馆清退",
                required=True
            ),
            LeaveSchoolCheckpoint(
                checkpoint_type=CheckpointType.FINANCIAL,
                name="财务结算",
                required=True
            ),
            LeaveSchoolCheckpoint(
                checkpoint_type=CheckpointType.DORMITORY,
                name="宿舍清退",
                required=True
            ),
            LeaveSchoolCheckpoint(
                checkpoint_type=CheckpointType.EQUIPMENT,
                name="设备归还",
                required=True
            ),
            LeaveSchoolCheckpoint(
                checkpoint_type=CheckpointType.ACADEMIC,
                name="学业完成",
                required=True
            ),
        ]

        for cp in default_checkpoints:
            record.add_checkpoint(cp)

        self._leave_records[self._next_leave_id] = record
        self._next_leave_id += 1

        return record

    def complete_checkpoint(
        self,
        leave_id: int,
        checkpoint_type: CheckpointType,
        checked_by: int,
        result: str = ""
    ) -> Optional[LeaveSchoolRecord]:
        """
        完成检查点
        """
        record = self._leave_records.get(leave_id)
        if not record:
            return None

        for checkpoint in record.checkpoints:
            if checkpoint.checkpoint_type == checkpoint_type:
                checkpoint.complete(checked_by, result)
                break

        # 检查是否全部完成
        if record.is_completed():
            record.status = LeaveSchoolStatus.COMPLETED
            record.graduation_date = datetime.now()
            record.processed_by = checked_by
            record.processed_at = datetime.now()

        record.updated_at = datetime.now()
        return record

    def exempt_checkpoint(
        self,
        leave_id: int,
        checkpoint_type: CheckpointType,
        reason: str,
        exempted_by: int
    ) -> Optional[LeaveSchoolRecord]:
        """
        豁免检查点
        """
        record = self._leave_records.get(leave_id)
        if not record:
            return None

        for checkpoint in record.checkpoints:
            if checkpoint.checkpoint_type == checkpoint_type:
                checkpoint.exempt(reason, exempted_by)
                break

        if record.is_completed():
            record.status = LeaveSchoolStatus.COMPLETED
            record.graduation_date = datetime.now()

        record.updated_at = datetime.now()
        return record

    def get_leave_record(self, leave_id: int) -> Optional[LeaveSchoolRecord]:
        """获取离校记录"""
        return self._leave_records.get(leave_id)

    def get_student_leave_record(
        self,
        student_id: int
    ) -> Optional[LeaveSchoolRecord]:
        """获取学生的离校记录"""
        for record in self._leave_records.values():
            if record.student_id == student_id:
                return record
        return None

    def get_pending_leave_records(self) -> List[LeaveSchoolRecord]:
        """获取待办理离校记录"""
        return [
            r for r in self._leave_records.values()
            if r.status in [
                LeaveSchoolStatus.PENDING,
                LeaveSchoolStatus.IN_PROGRESS
            ]
        ]

    # ==================== 校友管理 ====================

    def create_alumni(
        self,
        student_id: int,
        name: str,
        admission_year: int,
        graduation_year: int,
        major: str = "",
        degree: str = ""
    ) -> AlumniRecord:
        """
        创建校友记录
        """
        alumni = AlumniRecord(
            id=self._next_alumni_id,
            student_id=student_id,
            name=name,
            admission_year=admission_year,
            graduation_year=graduation_year,
            major=major,
            degree=degree
        )

        self._alumni_records[self._next_alumni_id] = alumni
        self._next_alumni_id += 1

        return alumni

    def convert_to_alumni(
        self,
        student_id: int,
        name: str,
        admission_year: int,
        graduation_year: int,
        major: str = "",
        student_class: str = ""
    ) -> AlumniRecord:
        """
        将毕业生转为校友
        """
        # 检查是否已存在
        for alumni in self._alumni_records.values():
            if alumni.student_id == student_id:
                return alumni

        return self.create_alumni(
            student_id=student_id,
            name=name,
            admission_year=admission_year,
            graduation_year=graduation_year,
            major=major
        )

    def update_alumni_info(
        self,
        alumni_id: int,
        employer: str = "",
        position: str = "",
        industry: str = "",
        phone: str = "",
        email: str = ""
    ) -> Optional[AlumniRecord]:
        """
        更新校友信息
        """
        alumni = self._alumni_records.get(alumni_id)
        if not alumni:
            return None

        if employer:
            alumni.employer = employer
        if position:
            alumni.position = position
        if industry:
            alumni.industry = industry
        if phone:
            alumni.phone = phone
        if email:
            alumni.email = email

        alumni.last_contact = datetime.now()
        alumni.updated_at = datetime.now()

        return alumni

    def get_alumni(self, alumni_id: int) -> Optional[AlumniRecord]:
        """获取校友记录"""
        return self._alumni_records.get(alumni_id)

    def get_alumni_by_student_id(
        self,
        student_id: int
    ) -> Optional[AlumniRecord]:
        """根据学生ID获取校友记录"""
        for alumni in self._alumni_records.values():
            if alumni.student_id == student_id:
                return alumni
        return None

    def search_alumni(
        self,
        major: str = "",
        graduation_year: int = 0,
        industry: str = "",
        employer: str = ""
    ) -> List[AlumniRecord]:
        """
        搜索校友
        """
        results = list(self._alumni_records.values())

        if major:
            results = [a for a in results if major in a.major]
        if graduation_year:
            results = [a for a in results if a.graduation_year == graduation_year]
        if industry:
            results = [a for a in results if industry in a.industry]
        if employer:
            results = [a for a in results if employer in a.employer]

        return results

    def get_alumni_statistics(
        self,
        graduation_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取校友统计
        """
        alumni_list = list(self._alumni_records.values())

        if graduation_year:
            alumni_list = [
                a for a in alumni_list
                if a.graduation_year == graduation_year
            ]

        stats = {
            "total": len(alumni_list),
            "by_industry": {},
            "by_level": {},
            "employment_rate": 0.0,
            "alumni_association_rate": 0.0
        }

        employed_count = 0
        association_count = 0

        for alumni in alumni_list:
            # 行业统计
            if alumni.industry:
                stats["by_industry"][alumni.industry] = \
                    stats["by_industry"].get(alumni.industry, 0) + 1

            # 级别统计
            stats["by_level"][alumni.alumni_level] = \
                stats["by_level"].get(alumni.alumni_level, 0) + 1

            # 就业率
            if alumni.employment_status == "employed":
                employed_count += 1

            # 校友会参与率
            if alumni.alumni_association:
                association_count += 1

        if alumni_list:
            stats["employment_rate"] = round(
                employed_count / len(alumni_list), 4
            )
            stats["alumni_association_rate"] = round(
                association_count / len(alumni_list), 4
            )

        return stats

    # ==================== 统计报告 ====================

    def generate_graduation_report(
        self,
        audit_id: int
    ) -> Optional[GraduationReport]:
        """
        生成毕业报告
        """
        audit = self._audits.get(audit_id)
        if not audit:
            return None

        report = GraduationReport(
            audit_id=audit_id,
            student_id=audit.student_id,
            student_name=f"学生{audit.student_id}",  # 简化
            total_credits=audit.total_credits,
            major_credits=audit.major_credits,
            elective_credits=audit.elective_credits,
            practice_credits=audit.practice_credits,
            gpa=audit.gpa,
            is_eligible=audit.is_eligible,
            completion_rate=audit.get_completion_rate()
        )

        # 补充未满足要求
        if not audit.is_eligible:
            _, report.missing_requirements = audit.check_requirements()

        # 添加建议
        if audit.total_credits < 160:
            report.suggestions.append("建议选修更多学分课程")
        if audit.practice_credits < 15:
            report.suggestions.append("建议参加更多实践活动")
        if audit.gpa < 2.0:
            report.suggestions.append("建议提高学业成绩")

        return report

    def get_graduation_statistics(
        self,
        academic_year: str
    ) -> GraduationStatistics:
        """
        获取毕业统计
        """
        stats = GraduationStatistics(
            academic_year=academic_year,
            semester=2  # 默认第二学期
        )

        for audit in self._audits.values():
            if audit.academic_year != academic_year:
                continue

            stats.total_students += 1

            if audit.status == GraduationStatus.GRADUATED:
                stats.graduated_count += 1
            elif audit.status == GraduationStatus.PENDING:
                stats.pending_count += 1
            elif audit.status == GraduationStatus.DEFERRED:
                stats.deferred_count += 1

            # GPA统计
            if audit.gpa > 0:
                if stats.highest_gpa == 0 or audit.gpa > stats.highest_gpa:
                    stats.highest_gpa = audit.gpa
                if stats.lowest_gpa == 0 or audit.gpa < stats.lowest_gpa:
                    stats.lowest_gpa = audit.gpa

        # 计算平均值
        if stats.total_students > 0:
            gpas = [a.gpa for a in self._audits.values()
                    if a.academic_year == academic_year and a.gpa > 0]
            if gpas:
                stats.average_gpa = round(sum(gpas) / len(gpas), 2)

            stats.average_completion_rate = round(
                sum(a.get_completion_rate() for a in self._audits.values()
                    if a.academic_year == academic_year) / stats.total_students, 4
            )

        return stats


# 创建全局服务实例
graduation_service = GraduationService()
