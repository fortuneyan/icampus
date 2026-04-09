"""
学生相关 Schemas
"""

from typing import Optional
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class StudentCreate(BaseModel):
    """创建学生请求"""

    student_no: str = Field(..., min_length=5, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    id_card: Optional[str] = Field(None, max_length=18)
    nation: Optional[str] = Field(None, max_length=50)
    origin_type: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    guardian_name: Optional[str] = Field(None, max_length=100)
    guardian_phone: Optional[str] = Field(None, max_length=20)
    enrollment_date: Optional[date] = None
    grade_id: Optional[UUID] = None
    class_id: Optional[UUID] = None
    photo_url: Optional[str] = None
    remarks: Optional[str] = None


class StudentUpdate(BaseModel):
    """更新学生请求"""

    name: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    id_card: Optional[str] = None
    nation: Optional[str] = None
    origin_type: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    enrollment_date: Optional[date] = None
    grade_id: Optional[UUID] = None
    class_id: Optional[UUID] = None
    photo_url: Optional[str] = None
    status: Optional[str] = None
    remarks: Optional[str] = None


class StudentResponse(BaseModel):
    """学生响应"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_no: str
    name: str
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    id_card: Optional[str] = None
    nation: Optional[str] = None
    origin_type: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    enrollment_date: Optional[date] = None
    grade_id: Optional[UUID] = None
    class_id: Optional[UUID] = None
    status: str
    photo_url: Optional[str] = None
    remarks: Optional[str] = None


class StudentQuery(BaseModel):
    """学生查询参数"""

    keyword: Optional[str] = None
    grade_id: Optional[UUID] = None
    class_id: Optional[UUID] = None
    status: Optional[str] = None
