from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class LeaveRequestCreate(BaseModel):
    student_id: str
    leave_type: str = "personal"
    start_date: datetime
    end_date: datetime
    reason: Optional[str] = None


class LeaveRequestUpdate(BaseModel):
    leave_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    reason: Optional[str] = None


class LeaveApproval(BaseModel):
    status: str
    approver_comment: Optional[str] = None


class LeaveQuotaCreate(BaseModel):
    student_id: Optional[str] = None
    class_id: Optional[str] = None
    grade_id: Optional[str] = None
    leave_type: str
    year: int
    total_days: int = 0