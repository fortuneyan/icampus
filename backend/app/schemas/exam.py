"""
考试相关 Schemas
"""

from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class PaperCreate(BaseModel):
    title: str = Field(..., max_length=200)
    paper_type: str = "practice"
    total_score: Optional[float] = 100
    duration: int = Field(90, ge=1)
    course_id: Optional[UUID] = None
    status: str = "draft"


class PaperUpdate(BaseModel):
    title: Optional[str] = None
    paper_type: Optional[str] = None
    total_score: Optional[float] = None
    duration: Optional[int] = None
    status: Optional[str] = None


class PaperResponse(BaseModel):
    id: UUID
    title: str
    paper_type: str
    total_score: Optional[float] = None
    duration: int
    course_id: Optional[UUID] = None
    creator_id: Optional[UUID] = None
    status: str

    class Config:
        from_attributes = True


class QuestionCreate(BaseModel):
    content: str
    question_type: str = "single"
    options: Optional[dict] = None
    answer: Optional[str] = None
    analysis: Optional[str] = None
    difficulty: int = Field(1, ge=1, le=5)
    score: float = Field(5, ge=0)


class QuestionResponse(BaseModel):
    id: UUID
    content: str
    question_type: str
    options: Optional[dict] = None
    answer: Optional[str] = None
    analysis: Optional[str] = None
    difficulty: int
    score: float

    class Config:
        from_attributes = True
