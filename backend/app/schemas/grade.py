"""
年级相关 Schemas
"""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class GradeCreate(BaseModel):
    """创建年级请求"""

    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=50)
    academic_year: str = Field(..., max_length=20)
    year: Optional[int] = None
    grade_level: Optional[int] = None
    head_teacher_id: Optional[UUID] = None
    status: str = "active"
    description: Optional[str] = None


class GradeUpdate(BaseModel):
    """更新年级请求"""

    name: Optional[str] = None
    code: Optional[str] = None
    academic_year: Optional[str] = None
    year: Optional[int] = None
    grade_level: Optional[int] = None
    head_teacher_id: Optional[UUID] = None
    student_count: Optional[int] = None
    class_count: Optional[int] = None
    status: Optional[str] = None
    description: Optional[str] = None


class GradeResponse(BaseModel):
    """年级响应"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    code: str
    academic_year: str
    year: Optional[int] = None
    grade_level: Optional[int] = None
    head_teacher_id: Optional[UUID] = None
    student_count: int = 0
    class_count: int = 0
    status: str
    description: Optional[str] = None


class GradeQuery(BaseModel):
    """年级查询参数"""

    name: Optional[str] = None
    code: Optional[str] = None
    academic_year: Optional[str] = None
    year: Optional[int] = None
    status: Optional[str] = None
