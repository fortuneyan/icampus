from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class RecruitmentPlanCreate(BaseModel):
    name: str
    year: int
    grade_id: Optional[str] = None
    quota: int = 0
    tuition: float = 0
    start_date: datetime
    end_date: datetime
    description: Optional[str] = None
    requirements: Optional[str] = None


class RecruitmentPlanUpdate(BaseModel):
    name: Optional[str] = None
    grade_id: Optional[str] = None
    quota: Optional[int] = None
    tuition: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    status: Optional[str] = None


class ApplicantCreate(BaseModel):
    student_name: str
    gender: Optional[str] = None
    birth_date: Optional[datetime] = None
    phone: str
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    id_card: Optional[str] = None
    address: Optional[str] = None
    current_school: Optional[str] = None
    source: Optional[str] = "offline"
    recruitment_plan_id: Optional[str] = None
    application_year: Optional[int] = None


class ApplicantUpdate(BaseModel):
    student_name: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[datetime] = None
    phone: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    id_card: Optional[str] = None
    address: Optional[str] = None
    current_school: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    enrollment_batch: Optional[str] = None
    remarks: Optional[str] = None
    is_enrolled: Optional[bool] = None


class ApplicantBatchUpdate(BaseModel):
    ids: list[str]
    status: Optional[str] = None
    enrollment_batch: Optional[str] = None
    recruitment_plan_id: Optional[str] = None


class FollowUpCreate(BaseModel):
    follow_type: str
    content: str
    next_follow_date: Optional[datetime] = None


class ApplicantImportRow(BaseModel):
    student_name: str
    gender: Optional[str] = None
    birth_date: Optional[str] = None
    phone: str
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    id_card: Optional[str] = None
    address: Optional[str] = None
    current_school: Optional[str] = None
    source: Optional[str] = "offline"
    recruitment_plan_id: Optional[str] = None
    application_year: Optional[int] = None
    remarks: Optional[str] = None


class ApplicantImportResult(BaseModel):
    success_count: int = 0
    fail_count: int = 0
    errors: list[str] = []