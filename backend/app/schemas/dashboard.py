"""
仪表盘相关 Schemas
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class OverviewResponse(BaseModel):
    student_count: int = 0
    teacher_count: int = 0
    class_count: int = 0
    course_count: int = 0
    resource_count: int = 0
    today_attendance_rate: float = 0


class StatisticItem(BaseModel):
    label: str
    value: float
    change: Optional[float] = None
    change_type: Optional[str] = None


class ChartData(BaseModel):
    labels: List[str]
    datasets: List[Dict[str, Any]]


class QuickAction(BaseModel):
    id: str
    name: str
    icon: str
    path: str
    permission: Optional[str] = None


class NotificationItem(BaseModel):
    id: UUID
    title: str
    content: Optional[str] = None
    msg_type: str
    priority: int
    is_read: bool
    created_at: str
