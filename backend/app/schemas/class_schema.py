"""
班级相关 Schemas
"""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class ClassCreate(BaseModel):
    """创建班级请求"""

    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=50)
    grade_id: Optional[UUID] = None
    head_teacher_id: Optional[UUID] = None
    room_no: Optional[str] = None
    academic_year: str = Field(..., max_length=20)
    semester: str = Field(..., max_length=10)
    status: str = "active"


class ClassUpdate(BaseModel):
    """更新班级请求"""

    name: Optional[str] = None
    code: Optional[str] = None
    grade_id: Optional[UUID] = None
    head_teacher_id: Optional[UUID] = None
    room_no: Optional[str] = None
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    student_count: Optional[int] = None
    status: Optional[str] = None


class ClassResponse(BaseModel):
    """班级响应"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    code: str
    grade_id: Optional[UUID] = None
    head_teacher_id: Optional[UUID] = None
    student_count: int
    room_no: Optional[str] = None
    academic_year: str
    semester: str
    status: str


class ClassQuery(BaseModel):
    """班级查询参数"""

    name: Optional[str] = None
    grade_id: Optional[UUID] = None
    status: Optional[str] = None
