"""
成绩相关 Schemas
"""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class ScoreCreate(BaseModel):
    """创建成绩请求"""

    student_id: UUID
    course_id: UUID
    semester: str = Field(..., max_length=20)
    score_type: str = Field(..., max_length=20)
    score: Optional[float] = Field(None, ge=0, le=100)
    grade_letter: Optional[str] = Field(None, max_length=5)
    remarks: Optional[str] = None


class ScoreUpdate(BaseModel):
    """更新成绩请求"""

    score: Optional[float] = Field(None, ge=0, le=100)
    grade_letter: Optional[str] = None
    remarks: Optional[str] = None


class ScoreResponse(BaseModel):
    """成绩响应"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    course_id: UUID
    semester: Optional[str] = None
    score_type: Optional[str] = None
    score: Optional[float] = None
    grade_letter: Optional[str] = None
    rank: Optional[int] = None
    remarks: Optional[str] = None


class ScoreQuery(BaseModel):
    """成绩查询参数"""

    student_id: Optional[UUID] = None
    course_id: Optional[UUID] = None
    semester: Optional[str] = None


class ScoreStatistics(BaseModel):
    """成绩统计"""

    total: int
    avg_score: float
    max_score: float
    min_score: float
    pass_rate: float
