"""
课程相关 Schemas
"""

from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class CourseTypeEnum(str, Enum):
    REQUIRED = "REQUIRED"
    ELECTIVE = "ELECTIVE"


class CourseCreate(BaseModel):
    """创建课程请求"""

    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    category: Optional[str] = Field(None, max_length=50)
    credit: Optional[float] = Field(None, ge=0, le=10)
    hours: Optional[int] = Field(None, ge=0)
    teacher_ids: Optional[List[UUID]] = Field(None)
    grade_id: Optional[UUID] = None
    semester: Optional[str] = Field(None, max_length=20)
    exam_type: Optional[str] = Field(None, max_length=20)
    grade_levels: Optional[List[int]] = Field(default_factory=list)
    course_type: Optional[CourseTypeEnum] = CourseTypeEnum.REQUIRED
    prerequisite_course_ids: Optional[List[UUID]] = Field(default_factory=list)


class CourseUpdate(BaseModel):
    """更新课程请求"""

    name: Optional[str] = None
    category: Optional[str] = None
    credit: Optional[float] = None
    hours: Optional[int] = None
    teacher_ids: Optional[List[UUID]] = None
    grade_id: Optional[UUID] = None
    semester: Optional[str] = None
    exam_type: Optional[str] = None
    status: Optional[str] = None
    grade_levels: Optional[List[int]] = None
    course_type: Optional[CourseTypeEnum] = None
    prerequisite_course_ids: Optional[List[UUID]] = None


class CourseResponse(BaseModel):
    """课程响应"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    category: Optional[str] = None
    credit: Optional[float] = None
    hours: Optional[int] = None
    teacher_ids: Optional[List[UUID]] = Field(default_factory=list)
    grade_id: Optional[UUID] = None
    semester: Optional[str] = None
    exam_type: Optional[str] = None
    status: str
    grade_levels: Optional[List[int]] = Field(default_factory=list)
    course_type: Optional[CourseTypeEnum] = CourseTypeEnum.ELECTIVE
    prerequisite_course_ids: Optional[List[UUID]] = Field(default_factory=list)
