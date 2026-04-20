from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class RecruitmentPlanCreate(BaseModel):
    name: str
    year: int
    grade_id: Optional[str] = None
    quota: int = 0
    start_date: datetime
    end_date: datetime
    description: Optional[str] = None


class RecruitmentPlanUpdate(BaseModel):
    name: Optional[str] = None
    grade_id: Optional[str] = None
    quota: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    description: Optional[str] = None
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
    source: Optional[str] = None
    recruitment_plan_id: Optional[str] = None


class ApplicantUpdate(BaseModel):
    student_name: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[datetime] = None
    phone: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    id_card: Optional[str] = None
    address: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    remarks: Optional[str] = None
    is_enrolled: Optional[bool] = None


class FollowUpCreate(BaseModel):
    follow_type: str
    content: str
    next_follow_date: Optional[datetime] = None
