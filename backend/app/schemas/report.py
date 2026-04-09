"""
报表相关 Schemas
"""

from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime


class ReportQuery(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    grade_id: Optional[UUID] = None
    class_id: Optional[UUID] = None


class StudentReport(BaseModel):
    total_students: int
    by_grade: List[dict]
    by_class: List[dict]
    enrollment_trend: List[dict]


class ScoreReport(BaseModel):
    avg_score: float
    pass_rate: float
    score_distribution: List[dict]
    subject_ranking: List[dict]


class AttendanceReport(BaseModel):
    attendance_rate: float
    normal_count: int
    late_count: int
    absent_count: int
    trend: List[dict]


class ReportExport(BaseModel):
    report_type: str
    format: str = Field("xlsx", pattern="^(xlsx|csv|pdf)$")
    query: Optional[ReportQuery] = None


class CustomReportCreate(BaseModel):
    name: str
    report_type: str
    config: dict
    is_public: bool = False
