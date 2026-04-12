"""
成绩报表API接口
提供学生成绩报表、班级统计、科目分析、成绩趋势等功能
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.score_report_service import (
    score_report_service, ReportType, GradeLevel,
    StudentScore, StudentReport, ClassReport,
    SubjectReport, ExamReport, TrendReport
)

router = APIRouter(prefix="/reports", tags=["成绩报表"])


# ==================== 请求/响应模型 ====================

class StudentScoreInput(BaseModel):
    """学生成绩输入"""
    student_id: int
    student_name: str
    exam_id: int
    subject_id: int
    subject_name: str
    score: float
    full_score: float = 100.0


class StudentReportRequest(BaseModel):
    """学生报表请求"""
    student_id: int
    student_name: str
    academic_year: str
    semester: int = 1


class ClassReportRequest(BaseModel):
    """班级报表请求"""
    class_id: int
    class_name: str
    academic_year: str
    semester: int = 1
    student_ids: List[int] = []


class SubjectReportRequest(BaseModel):
    """科目报表请求"""
    subject_id: int
    subject_name: str
    academic_year: str
    semester: int = 1


class ExamReportRequest(BaseModel):
    """考试报表请求"""
    exam_id: int
    exam_name: str
    academic_year: str
    semester: int = 1
    exam_date: str = ""


class TrendReportRequest(BaseModel):
    """趋势报表请求"""
    student_id: int
    student_name: str
    academic_year: str


class CompareStudentsRequest(BaseModel):
    """学生对比请求"""
    student_ids: List[int]
    academic_year: str
    semester: int = 1


class CompareClassesRequest(BaseModel):
    """班级对比请求"""
    class_ids: List[int]
    academic_year: str
    semester: int = 1


# ==================== 成绩录入接口 ====================

@router.post("/scores", summary="录入学生成绩")
async def add_student_score(request: StudentScoreInput):
    """录入学生成绩"""
    score = score_report_service.add_student_score(
        student_id=request.student_id,
        student_name=request.student_name,
        exam_id=request.exam_id,
        subject_id=request.subject_id,
        subject_name=request.subject_name,
        score=request.score,
        full_score=request.full_score
    )

    return {
        "code": 0,
        "message": "录入成功",
        "data": {
            "student_id": score.student_id,
            "score": score.score,
            "grade_level": score.grade_level.value,
            "is_pass": score.is_pass()
        }
    }


@router.get("/scores/{student_id}", summary="获取学生成绩列表")
async def get_student_scores(
    student_id: int,
    academic_year: Optional[str] = None
):
    """获取学生成绩列表"""
    scores = score_report_service.get_student_scores(student_id, academic_year)

    return {
        "code": 0,
        "message": "获取成功",
        "data": [
            {
                "student_id": s.student_id,
                "student_name": s.student_name,
                "exam_id": s.exam_id,
                "subject_id": s.subject_id,
                "subject_name": s.subject_name,
                "score": s.score,
                "full_score": s.full_score,
                "rank": s.rank,
                "grade_level": s.grade_level.value,
                "percentile": s.get_percentile(),
                "is_pass": s.is_pass()
            }
            for s in scores
        ]
    }


# ==================== 学生报表接口 ====================

@router.post("/student", summary="生成学生成绩报表")
async def generate_student_report(request: StudentReportRequest):
    """生成学生成绩报表"""
    report = score_report_service.generate_student_report(
        student_id=request.student_id,
        student_name=request.student_name,
        academic_year=request.academic_year,
        semester=request.semester
    )

    return {
        "code": 0,
        "message": "生成成功",
        "data": {
            "student_id": report.student_id,
            "student_name": report.student_name,
            "academic_year": report.academic_year,
            "semester": report.semester,
            "total_courses": report.total_courses,
            "passed_courses": report.passed_courses,
            "failed_courses": report.failed_courses,
            "total_score": report.total_score,
            "average_score": report.average_score,
            "highest_score": report.highest_score,
            "lowest_score": report.lowest_score,
            "gpa": report.gpa,
            "pass_rate": report.get_pass_rate(),
            "completion_rate": report.get_completion_rate(),
            "grades_distribution": {
                "excellent": report.excellent_count,
                "good": report.good_count,
                "average": report.average_count,
                "pass": report.pass_count,
                "fail": report.fail_count
            },
            "class_rank": report.class_rank,
            "grade_rank": report.grade_rank
        }
    }


@router.get("/student/{student_id}/summary", summary="获取学生成绩摘要")
async def get_student_summary(
    student_id: int,
    academic_year: str,
    semester: int = 1
):
    """获取学生成绩摘要"""
    report = score_report_service.generate_student_report(
        student_id=student_id,
        student_name="",
        academic_year=academic_year,
        semester=semester
    )

    return {
        "code": 0,
        "message": "获取成功",
        "data": {
            "student_id": report.student_id,
            "average_score": report.average_score,
            "gpa": report.gpa,
            "pass_rate": report.get_pass_rate(),
            "class_rank": report.class_rank,
            "grade_rank": report.grade_rank
        }
    }


# ==================== 班级报表接口 ====================

@router.post("/class", summary="生成班级成绩报表")
async def generate_class_report(request: ClassReportRequest):
    """生成班级成绩报表"""
    report = score_report_service.generate_class_report(
        class_id=request.class_id,
        class_name=request.class_name,
        academic_year=request.academic_year,
        semester=request.semester,
        student_ids=request.student_ids
    )

    return {
        "code": 0,
        "message": "生成成功",
        "data": {
            "class_id": report.class_id,
            "class_name": report.class_name,
            "academic_year": report.academic_year,
            "semester": report.semester,
            "total_students": report.total_students,
            "total_exams": report.total_exams,
            "class_average": report.class_average,
            "highest_score": report.highest_score,
            "lowest_score": report.lowest_score,
            "score_std": report.score_std,
            "pass_count": report.pass_count,
            "pass_rate": report.pass_rate,
            "excellent_count": report.excellent_count,
            "excellent_rate": report.excellent_rate,
            "subject_averages": report.subject_averages,
            "score_distribution": report.score_distribution
        }
    }


@router.get("/class/{class_id}", summary="获取班级报表")
async def get_class_report(class_id: int):
    """获取班级报表"""
    report = score_report_service._class_reports.get(class_id)

    if not report:
        raise HTTPException(status_code=404, detail="班级报表不存在")

    return {
        "code": 0,
        "message": "获取成功",
        "data": {
            "class_id": report.class_id,
            "class_name": report.class_name,
            "class_average": report.class_average,
            "pass_rate": report.pass_rate,
            "excellent_rate": report.excellent_rate
        }
    }


# ==================== 科目报表接口 ====================

@router.post("/subject", summary="生成科目成绩报表")
async def generate_subject_report(request: SubjectReportRequest):
    """生成科目成绩报表"""
    report = score_report_service.generate_subject_report(
        subject_id=request.subject_id,
        subject_name=request.subject_name,
        academic_year=request.academic_year,
        semester=request.semester
    )

    return {
        "code": 0,
        "message": "生成成功",
        "data": {
            "subject_id": report.subject_id,
            "subject_name": report.subject_name,
            "academic_year": report.academic_year,
            "semester": report.semester,
            "total_students": report.total_students,
            "subject_average": report.subject_average,
            "highest_score": report.highest_score,
            "lowest_score": report.lowest_score,
            "median_score": report.median_score,
            "score_std": report.score_std,
            "pass_count": report.pass_count,
            "pass_rate": report.pass_rate,
            "excellent_rate": report.excellent_rate,
            "good_rate": report.good_rate,
            "average_rate": report.average_rate,
            "score_distribution": report.score_distribution
        }
    }


# ==================== 考试报表接口 ====================

@router.post("/exam", summary="生成考试分析报表")
async def generate_exam_report(request: ExamReportRequest):
    """生成考试分析报表"""
    report = score_report_service.generate_exam_report(
        exam_id=request.exam_id,
        exam_name=request.exam_name,
        academic_year=request.academic_year,
        semester=request.semester,
        exam_date=request.exam_date
    )

    return {
        "code": 0,
        "message": "生成成功",
        "data": {
            "exam_id": report.exam_id,
            "exam_name": report.exam_name,
            "academic_year": report.academic_year,
            "semester": report.semester,
            "exam_date": report.exam_date,
            "total_students": report.total_students,
            "total_subjects": report.total_subjects,
            "overall_average": report.overall_average,
            "highest_score": report.highest_score,
            "lowest_score": report.lowest_score,
            "score_std": report.score_std,
            "pass_count": report.pass_count,
            "pass_rate": report.pass_rate,
            "score_distribution": report.score_distribution,
            "subject_analysis": report.subject_analysis,
            "difficulty_index": report.difficulty_index,
            "discrimination_index": report.discrimination_index
        }
    }


# ==================== 趋势分析接口 ====================

@router.post("/trend", summary="生成成绩趋势报表")
async def generate_trend_report(request: TrendReportRequest):
    """生成成绩趋势报表"""
    report = score_report_service.generate_trend_report(
        student_id=request.student_id,
        student_name=request.student_name,
        academic_year=request.academic_year
    )

    return {
        "code": 0,
        "message": "生成成功",
        "data": {
            "student_id": report.student_id,
            "student_name": report.student_name,
            "academic_year": report.academic_year,
            "semester_scores": report.semester_scores,
            "subject_trends": report.subject_trends,
            "overall_trend": report.overall_trend,
            "improvement_rate": report.improvement_rate,
            "volatility": report.volatility,
            "predicted_next": report.predicted_next
        }
    }


# ==================== 对比分析接口 ====================

@router.post("/compare/students", summary="学生对比分析")
async def compare_students(request: CompareStudentsRequest):
    """对比分析多个学生"""
    results = score_report_service.compare_students(
        student_ids=request.student_ids,
        academic_year=request.academic_year,
        semester=request.semester
    )

    return {
        "code": 0,
        "message": "对比成功",
        "data": {
            "total": len(results),
            "items": results
        }
    }


@router.post("/compare/classes", summary="班级对比分析")
async def compare_classes(request: CompareClassesRequest):
    """对比分析多个班级"""
    results = score_report_service.compare_classes(
        class_ids=request.class_ids,
        academic_year=request.academic_year,
        semester=request.semester
    )

    return {
        "code": 0,
        "message": "对比成功",
        "data": {
            "total": len(results),
            "items": results
        }
    }


# ==================== 数据导出接口 ====================

@router.get("/export/{student_id}", summary="导出学生成绩报表")
async def export_student_report(
    student_id: int,
    academic_year: str,
    semester: int = 1,
    format: str = "json"
):
    """导出学生成绩报表"""
    data = score_report_service.export_student_report(
        student_id=student_id,
        academic_year=academic_year,
        semester=semester,
        format=format
    )

    return {
        "code": 0,
        "message": "导出成功",
        "data": data
    }


# ==================== 统计接口 ====================

@router.get("/statistics/overview", summary="获取成绩统计概览")
async def get_statistics_overview(
    academic_year: str,
    semester: int = 1
):
    """获取成绩统计概览"""
    # 简化统计
    all_scores = []
    for scores in score_report_service._student_scores.values():
        all_scores.extend(scores)

    if not all_scores:
        return {
            "code": 0,
            "message": "获取成功",
            "data": {
                "total_students": 0,
                "total_exams": 0,
                "overall_average": 0.0,
                "overall_pass_rate": 0.0
            }
        }

    # 计算整体统计
    scores_list = [s.score for s in all_scores]
    overall_average = sum(scores_list) / len(scores_list)
    pass_count = sum(1 for s in all_scores if s.is_pass())
    overall_pass_rate = pass_count / len(all_scores)

    return {
        "code": 0,
        "message": "获取成功",
        "data": {
            "total_students": len(set(s.student_id for s in all_scores)),
            "total_exams": len(set(s.exam_id for s in all_scores)),
            "total_subjects": len(set(s.subject_id for s in all_scores)),
            "overall_average": round(overall_average, 2),
            "overall_pass_rate": round(overall_pass_rate, 4),
            "highest_score": max(scores_list),
            "lowest_score": min(scores_list)
        }
    }


@router.get("/statistics/ranking", summary="获取成绩排名")
async def get_ranking(
    academic_year: str,
    semester: int = 1,
    subject_id: Optional[int] = None,
    class_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200)
):
    """获取成绩排名"""
    all_scores = []
    for scores in score_report_service._student_scores.values():
        if subject_id:
            scores = [s for s in scores if s.subject_id == subject_id]
        all_scores.extend(scores)

    # 按学生分组计算平均分
    student_scores: Dict[int, List[float]] = {}
    for s in all_scores:
        if s.student_id not in student_scores:
            student_scores[s.student_id] = []
        student_scores[s.student_id].append(s.score)

    # 排序
    rankings = []
    for sid, scores in student_scores.items():
        avg = sum(scores) / len(scores)
        rankings.append({
            "student_id": sid,
            "average_score": round(avg, 2),
            "total_exams": len(scores)
        })

    rankings.sort(key=lambda x: x["average_score"], reverse=True)

    # 添加排名
    for i, r in enumerate(rankings[:limit]):
        r["rank"] = i + 1

    return {
        "code": 0,
        "message": "获取成功",
        "data": {
            "total": len(rankings),
            "items": rankings[:limit]
        }
    }
