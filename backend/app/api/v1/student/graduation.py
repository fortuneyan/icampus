"""
毕业管理API接口
提供毕业审核、证书管理、离校手续、校友管理等功能
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.models.graduation import (
    GraduationAudit, GraduationCertificate, LeaveSchoolRecord,
    AlumniRecord, GraduationStatistics, GraduationReport,
    GraduationStatus, AuditType, CertificateStatus,
    LeaveSchoolStatus, CheckpointType, GraduationRequirement
)
from app.services.graduation_service import graduation_service

router = APIRouter(prefix="/graduation", tags=["毕业管理"])


# ==================== 请求/响应模型 ====================

class GraduationAuditCreate(BaseModel):
    """创建毕业审核请求"""
    student_id: int
    academic_year: str
    semester: int = 1
    audit_type: str = "preliminary"


class AcademicInfoUpdate(BaseModel):
    """更新学业信息请求"""
    total_credits: float
    major_credits: float
    elective_credits: float
    practice_credits: float
    completed_courses: int
    gpa: float
    passed_required: List[int] = []
    failed_required: List[int] = []


class AuditSubmit(BaseModel):
    """提交审核请求"""
    comment: str = ""


class BatchAuditRequest(BaseModel):
    """批量审核请求"""
    audit_ids: List[int]
    approved: bool = True
    comment: str = ""


class CertificateCreate(BaseModel):
    """创建证书请求"""
    student_id: int
    student_name: str
    academic_year: str
    major: str = ""
    major_code: str = ""


class CertificateIssue(BaseModel):
    """发放证书请求"""
    issued_by: int


class CertificatePrint(BaseModel):
    """打印证书请求"""
    printed_by: int


class CertificateRevoke(BaseModel):
    """吊销证书请求"""
    reason: str = ""


class LeaveRecordCreate(BaseModel):
    """创建离校记录请求"""
    student_id: int
    student_name: str
    academic_year: str
    semester: int = 2
    leave_type: str = "graduation"


class CheckpointComplete(BaseModel):
    """完成检查点请求"""
    checkpoint_type: str
    checked_by: int
    result: str = ""


class CheckpointExempt(BaseModel):
    """豁免检查点请求"""
    checkpoint_type: str
    reason: str
    exempted_by: int


class AlumniCreate(BaseModel):
    """创建校友请求"""
    student_id: int
    name: str
    admission_year: int
    graduation_year: int
    major: str = ""
    degree: str = ""


class AlumniUpdate(BaseModel):
    """更新校友请求"""
    employer: str = ""
    position: str = ""
    industry: str = ""
    phone: str = ""
    email: str = ""


class EligibilityCheck(BaseModel):
    """毕业资格检查请求"""
    student_id: int
    academic_year: str


# ==================== 毕业审核接口 ====================

@router.post("/audits", summary="创建毕业审核记录")
async def create_audit(request: GraduationAuditCreate):
    """创建毕业审核记录"""
    audit_type = AuditType(request.audit_type)
    audit = graduation_service.create_audit(
        student_id=request.student_id,
        academic_year=request.academic_year,
        semester=request.semester,
        audit_type=audit_type
    )
    return {
        "code": 0,
        "message": "创建成功",
        "data": {
            "id": audit.id,
            "student_id": audit.student_id,
            "academic_year": audit.academic_year,
            "semester": audit.semester,
            "audit_type": audit.audit_type.value,
            "status": audit.status.value
        }
    }


@router.put("/audits/{audit_id}/academic", summary="更新学业信息")
async def update_academic_info(
    audit_id: int,
    request: AcademicInfoUpdate
):
    """更新审核记录的学业信息"""
    audit = graduation_service.update_audit_academic_info(
        audit_id=audit_id,
        total_credits=request.total_credits,
        major_credits=request.major_credits,
        elective_credits=request.elective_credits,
        practice_credits=request.practice_credits,
        completed_courses=request.completed_courses,
        gpa=request.gpa,
        passed_required=request.passed_required,
        failed_required=request.failed_required
    )

    if not audit:
        raise HTTPException(status_code=404, detail="审核记录不存在")

    return {
        "code": 0,
        "message": "更新成功",
        "data": {
            "id": audit.id,
            "total_credits": audit.total_credits,
            "major_credits": audit.major_credits,
            "gpa": audit.gpa,
            "is_eligible": audit.is_eligible,
            "completion_rate": audit.get_completion_rate()
        }
    }


@router.post("/audits/{audit_id}/eligibility", summary="检查毕业资格")
async def check_eligibility(audit_id: int):
    """检查学生毕业资格"""
    audit = graduation_service.get_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="审核记录不存在")

    is_eligible, reasons, completion_rate = \
        graduation_service.check_graduation_eligibility(
            audit.student_id,
            audit.academic_year
        )

    return {
        "code": 0,
        "message": "检查完成",
        "data": {
            "is_eligible": is_eligible,
            "reasons": reasons,
            "completion_rate": completion_rate
        }
    }


@router.post("/audits/{audit_id}/submit", summary="提交审核")
async def submit_audit(
    audit_id: int,
    auditor_id: int,
    request: AuditSubmit
):
    """提交毕业审核"""
    audit = graduation_service.submit_audit(
        audit_id=audit_id,
        auditor_id=auditor_id,
        comment=request.comment
    )

    if not audit:
        raise HTTPException(status_code=404, detail="审核记录不存在")

    return {
        "code": 0,
        "message": "审核提交成功",
        "data": {
            "id": audit.id,
            "status": audit.status.value,
            "is_eligible": audit.is_eligible,
            "audit_time": audit.audit_time.isoformat() if audit.audit_time else None
        }
    }


@router.post("/audits/batch", summary="批量审核")
async def batch_audit(request: BatchAuditRequest, auditor_id: int):
    """批量审核毕业资格"""
    results = graduation_service.batch_audit(
        audit_ids=request.audit_ids,
        auditor_id=auditor_id,
        approved=request.approved,
        comment=request.comment
    )

    return {
        "code": 0,
        "message": "批量审核完成",
        "data": results
    }


@router.get("/audits", summary="获取审核列表")
async def get_audits(
    student_id: Optional[int] = None,
    academic_year: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """获取毕业审核列表"""
    if student_id:
        audits = graduation_service.get_student_audits(student_id)
    elif academic_year:
        if status:
            audits = graduation_service.get_pending_audits(academic_year)
            audits = [a for a in audits if a.status.value == status]
        else:
            audits = graduation_service.get_pending_audits(academic_year)
    else:
        audits = graduation_service.get_pending_audits()

    # 分页
    total = len(audits)
    start = (page - 1) * page_size
    end = start + page_size
    audits = audits[start:end]

    return {
        "code": 0,
        "message": "获取成功",
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "id": a.id,
                    "student_id": a.student_id,
                    "academic_year": a.academic_year,
                    "semester": a.semester,
                    "status": a.status.value,
                    "total_credits": a.total_credits,
                    "gpa": a.gpa,
                    "is_eligible": a.is_eligible,
                    "completion_rate": a.get_completion_rate()
                }
                for a in audits
            ]
        }
    }


@router.get("/audits/{audit_id}", summary="获取审核详情")
async def get_audit_detail(audit_id: int):
    """获取毕业审核详情"""
    audit = graduation_service.get_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="审核记录不存在")

    return {
        "code": 0,
        "message": "获取成功",
        "data": {
            "id": audit.id,
            "student_id": audit.student_id,
            "academic_year": audit.academic_year,
            "semester": audit.semester,
            "audit_type": audit.audit_type.value,
            "status": audit.status.value,
            "total_credits": audit.total_credits,
            "major_credits": audit.major_credits,
            "elective_credits": audit.elective_credits,
            "practice_credits": audit.practice_credits,
            "completed_courses": audit.completed_courses,
            "gpa": audit.gpa,
            "passed_required": audit.passed_required,
            "failed_required": audit.failed_required,
            "is_eligible": audit.is_eligible,
            "audit_comment": audit.audit_comment,
            "auditor_id": audit.auditor_id,
            "audit_time": audit.audit_time.isoformat() if audit.audit_time else None,
            "completion_rate": audit.get_completion_rate()
        }
    }


# ==================== 毕业证书接口 ====================

@router.post("/certificates", summary="创建毕业证书")
async def create_certificate(request: CertificateCreate):
    """创建毕业证书"""
    cert = graduation_service.create_certificate(
        student_id=request.student_id,
        student_name=request.student_name,
        academic_year=request.academic_year,
        major=request.major,
        major_code=request.major_code
    )

    return {
        "code": 0,
        "message": "创建成功",
        "data": {
            "id": cert.id,
            "student_id": cert.student_id,
            "student_name": cert.student_name,
            "certificate_number": cert.certificate_number,
            "status": cert.status.value
        }
    }


@router.post("/certificates/{certificate_id}/print", summary="打印证书")
async def print_certificate(
    certificate_id: int,
    request: CertificatePrint
):
    """打印毕业证书"""
    cert = graduation_service.print_certificate(
        certificate_id=certificate_id,
        printed_by=request.printed_by
    )

    if not cert:
        raise HTTPException(status_code=404, detail="证书不存在")

    return {
        "code": 0,
        "message": "打印成功",
        "data": {
            "id": cert.id,
            "status": cert.status.value,
            "printed_at": cert.printed_at.isoformat() if cert.printed_at else None
        }
    }


@router.post("/certificates/{certificate_id}/issue", summary="发放证书")
async def issue_certificate(
    certificate_id: int,
    request: CertificateIssue
):
    """发放毕业证书"""
    cert = graduation_service.issue_certificate(
        certificate_id=certificate_id,
        issued_by=request.issued_by
    )

    if not cert:
        raise HTTPException(status_code=404, detail="证书不存在")

    return {
        "code": 0,
        "message": "发放成功",
        "data": {
            "id": cert.id,
            "status": cert.status.value,
            "issued_at": cert.issued_at.isoformat() if cert.issued_at else None
        }
    }


@router.post("/certificates/{certificate_id}/revoke", summary="吊销证书")
async def revoke_certificate(
    certificate_id: int,
    request: CertificateRevoke
):
    """吊销毕业证书"""
    cert = graduation_service.revoke_certificate(
        certificate_id=certificate_id,
        reason=request.reason
    )

    if not cert:
        raise HTTPException(status_code=404, detail="证书不存在")

    return {
        "code": 0,
        "message": "吊销成功",
        "data": {
            "id": cert.id,
            "status": cert.status.value
        }
    }


@router.get("/certificates/verify/{certificate_number}", summary="验证证书")
async def verify_certificate(certificate_number: str):
    """验证毕业证书"""
    is_valid, result = graduation_service.verify_certificate(certificate_number)

    return {
        "code": 0,
        "message": "验证完成",
        "data": {
            "is_valid": is_valid,
            "result": result
        }
    }


@router.get("/certificates/{certificate_id}", summary="获取证书详情")
async def get_certificate(certificate_id: int):
    """获取毕业证书详情"""
    cert = graduation_service.get_certificate(certificate_id)
    if not cert:
        raise HTTPException(status_code=404, detail="证书不存在")

    return {
        "code": 0,
        "message": "获取成功",
        "data": {
            "id": cert.id,
            "student_id": cert.student_id,
            "student_name": cert.student_name,
            "certificate_number": cert.certificate_number,
            "academic_year": cert.academic_year,
            "graduation_year": cert.graduation_year,
            "major": cert.major,
            "degree": cert.degree_type,
            "status": cert.status.value,
            "gpa": cert.gpa,
            "is_valid": cert.is_valid()
        }
    }


@router.get("/certificates/student/{student_id}", summary="获取学生证书")
async def get_student_certificate(student_id: int):
    """获取学生的毕业证书"""
    cert = graduation_service.get_student_certificate(student_id)

    if not cert:
        return {
            "code": 0,
            "message": "未找到证书",
            "data": None
        }

    return {
        "code": 0,
        "message": "获取成功",
        "data": {
            "id": cert.id,
            "certificate_number": cert.certificate_number,
            "status": cert.status.value,
            "graduation_year": cert.graduation_year
        }
    }


# ==================== 离校手续接口 ====================

@router.post("/leave-records", summary="创建离校记录")
async def create_leave_record(request: LeaveRecordCreate):
    """创建离校记录"""
    record = graduation_service.create_leave_record(
        student_id=request.student_id,
        student_name=request.student_name,
        academic_year=request.academic_year,
        semester=request.semester,
        leave_type=request.leave_type
    )

    return {
        "code": 0,
        "message": "创建成功",
        "data": {
            "id": record.id,
            "student_id": record.student_id,
            "status": record.status.value,
            "completion_rate": record.get_completion_rate()
        }
    }


@router.post("/leave-records/{leave_id}/checkpoints/{checkpoint_type}/complete",
             summary="完成检查点")
async def complete_checkpoint(
    leave_id: int,
    checkpoint_type: str,
    request: CheckpointComplete
):
    """完成离校检查点"""
    cp_type = CheckpointType(checkpoint_type)
    record = graduation_service.complete_checkpoint(
        leave_id=leave_id,
        checkpoint_type=cp_type,
        checked_by=request.checked_by,
        result=request.result
    )

    if not record:
        raise HTTPException(status_code=404, detail="离校记录不存在")

    return {
        "code": 0,
        "message": "完成成功",
        "data": {
            "leave_id": record.id,
            "status": record.status.value,
            "completion_rate": record.get_completion_rate()
        }
    }


@router.post("/leave-records/{leave_id}/checkpoints/{checkpoint_type}/exempt",
             summary="豁免检查点")
async def exempt_checkpoint(
    leave_id: int,
    checkpoint_type: str,
    request: CheckpointExempt
):
    """豁免离校检查点"""
    cp_type = CheckpointType(checkpoint_type)
    record = graduation_service.exempt_checkpoint(
        leave_id=leave_id,
        checkpoint_type=cp_type,
        reason=request.reason,
        exempted_by=request.exempted_by
    )

    if not record:
        raise HTTPException(status_code=404, detail="离校记录不存在")

    return {
        "code": 0,
        "message": "豁免成功",
        "data": {
            "leave_id": record.id,
            "status": record.status.value,
            "completion_rate": record.get_completion_rate()
        }
    }


@router.get("/leave-records/{leave_id}", summary="获取离校记录详情")
async def get_leave_record(leave_id: int):
    """获取离校记录详情"""
    record = graduation_service.get_leave_record(leave_id)
    if not record:
        raise HTTPException(status_code=404, detail="离校记录不存在")

    return {
        "code": 0,
        "message": "获取成功",
        "data": {
            "id": record.id,
            "student_id": record.student_id,
            "student_name": record.student_name,
            "leave_type": record.leave_type,
            "status": record.status.value,
            "completion_rate": record.get_completion_rate(),
            "checkpoints": [
                {
                    "type": c.checkpoint_type.value,
                    "name": c.name,
                    "status": c.status.value,
                    "required": c.required,
                    "result": c.check_result,
                    "checked_at": c.checked_at.isoformat() if c.checked_at else None
                }
                for c in record.checkpoints
            ]
        }
    }


@router.get("/leave-records/pending", summary="获取待办理离校记录")
async def get_pending_leave_records():
    """获取待办理离校记录列表"""
    records = graduation_service.get_pending_leave_records()

    return {
        "code": 0,
        "message": "获取成功",
        "data": [
            {
                "id": r.id,
                "student_id": r.student_id,
                "student_name": r.student_name,
                "leave_type": r.leave_type,
                "status": r.status.value,
                "completion_rate": r.get_completion_rate()
            }
            for r in records
        ]
    }


# ==================== 校友管理接口 ====================

@router.post("/alumni", summary="创建校友记录")
async def create_alumni(request: AlumniCreate):
    """创建校友记录"""
    alumni = graduation_service.create_alumni(
        student_id=request.student_id,
        name=request.name,
        admission_year=request.admission_year,
        graduation_year=request.graduation_year,
        major=request.major,
        degree=request.degree
    )

    return {
        "code": 0,
        "message": "创建成功",
        "data": {
            "id": alumni.id,
            "student_id": alumni.student_id,
            "name": alumni.name
        }
    }


@router.post("/alumni/convert", summary="毕业生转校友")
async def convert_to_alumni(
    student_id: int,
    name: str,
    admission_year: int,
    graduation_year: int,
    major: str = "",
    student_class: str = ""
):
    """将毕业生转为校友"""
    alumni = graduation_service.convert_to_alumni(
        student_id=student_id,
        name=name,
        admission_year=admission_year,
        graduation_year=graduation_year,
        major=major,
        student_class=student_class
    )

    return {
        "code": 0,
        "message": "转换成功",
        "data": {
            "id": alumni.id,
            "student_id": alumni.student_id,
            "name": alumni.name,
            "graduation_year": alumni.graduation_year
        }
    }


@router.put("/alumni/{alumni_id}", summary="更新校友信息")
async def update_alumni(
    alumni_id: int,
    request: AlumniUpdate
):
    """更新校友信息"""
    alumni = graduation_service.update_alumni_info(
        alumni_id=alumni_id,
        employer=request.employer,
        position=request.position,
        industry=request.industry,
        phone=request.phone,
        email=request.email
    )

    if not alumni:
        raise HTTPException(status_code=404, detail="校友记录不存在")

    return {
        "code": 0,
        "message": "更新成功",
        "data": {
            "id": alumni.id,
            "employer": alumni.employer,
            "position": alumni.position,
            "industry": alumni.industry
        }
    }


@router.get("/alumni/{alumni_id}", summary="获取校友详情")
async def get_alumni(alumni_id: int):
    """获取校友详情"""
    alumni = graduation_service.get_alumni(alumni_id)
    if not alumni:
        raise HTTPException(status_code=404, detail="校友记录不存在")

    return {
        "code": 0,
        "message": "获取成功",
        "data": {
            "id": alumni.id,
            "student_id": alumni.student_id,
            "name": alumni.name,
            "phone": alumni.phone,
            "email": alumni.email,
            "major": alumni.major,
            "graduation_year": alumni.graduation_year,
            "employer": alumni.employer,
            "position": alumni.position,
            "industry": alumni.industry,
            "alumni_association": alumni.alumni_association,
            "alumni_level": alumni.alumni_level,
            "contributions": alumni.contributions
        }
    }


@router.get("/alumni/search", summary="搜索校友")
async def search_alumni(
    major: str = "",
    graduation_year: int = 0,
    industry: str = "",
    employer: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """搜索校友"""
    alumni_list = graduation_service.search_alumni(
        major=major,
        graduation_year=graduation_year,
        industry=industry,
        employer=employer
    )

    # 分页
    total = len(alumni_list)
    start = (page - 1) * page_size
    end = start + page_size
    alumni_list = alumni_list[start:end]

    return {
        "code": 0,
        "message": "搜索成功",
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "id": a.id,
                    "name": a.name,
                    "major": a.major,
                    "graduation_year": a.graduation_year,
                    "employer": a.employer,
                    "industry": a.industry
                }
                for a in alumni_list
            ]
        }
    }


@router.get("/alumni/statistics", summary="校友统计")
async def get_alumni_statistics(graduation_year: int = 0):
    """获取校友统计"""
    stats = graduation_service.get_alumni_statistics(graduation_year or None)

    return {
        "code": 0,
        "message": "获取成功",
        "data": stats
    }


# ==================== 统计报表接口 ====================

@router.get("/reports/{audit_id}", summary="生成毕业报告")
async def generate_report(audit_id: int):
    """生成毕业报告"""
    report = graduation_service.generate_graduation_report(audit_id)

    if not report:
        raise HTTPException(status_code=404, detail="审核记录不存在")

    return {
        "code": 0,
        "message": "生成成功",
        "data": {
            "audit_id": report.audit_id,
            "student_id": report.student_id,
            "student_name": report.student_name,
            "total_credits": report.total_credits,
            "major_credits": report.major_credits,
            "gpa": report.gpa,
            "is_eligible": report.is_eligible,
            "completion_rate": report.completion_rate,
            "missing_requirements": report.missing_requirements,
            "suggestions": report.suggestions,
            "generated_at": report.generated_at.isoformat()
        }
    }


@router.get("/statistics/{academic_year}", summary="毕业统计")
async def get_graduation_statistics(academic_year: str):
    """获取毕业统计"""
    stats = graduation_service.get_graduation_statistics(academic_year)

    return {
        "code": 0,
        "message": "获取成功",
        "data": {
            "academic_year": stats.academic_year,
            "semester": stats.semester,
            "total_students": stats.total_students,
            "graduated_count": stats.graduated_count,
            "pending_count": stats.pending_count,
            "deferred_count": stats.deferred_count,
            "average_gpa": stats.average_gpa,
            "highest_gpa": stats.highest_gpa,
            "lowest_gpa": stats.lowest_gpa,
            "graduation_rate": stats.get_graduation_rate()
        }
    }
