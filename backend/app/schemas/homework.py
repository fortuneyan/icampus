from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class HomeworkCreate(BaseModel):
    title: str
    content: Optional[str] = None
    course_id: Optional[str] = None
    grade_id: Optional[str] = None
    class_ids: Optional[list] = None
    homework_type: str = "online"
    total_score: float = 100
    submit_start: Optional[datetime] = None
    submit_end: Optional[datetime] = None
    attachments: Optional[list] = None
    notify_enabled: bool = True


class HomeworkUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    homework_type: Optional[str] = None
    total_score: Optional[float] = None
    submit_start: Optional[datetime] = None
    submit_end: Optional[datetime] = None
    attachments: Optional[list] = None
    status: Optional[str] = None


class HomeworkSubmissionCreate(BaseModel):
    content: Optional[str] = None
    attachment_urls: Optional[list] = None


class HomeworkSubmissionUpdate(BaseModel):
    score: Optional[float] = None
    feedback: Optional[str] = None


class WrongQuestionCreate(BaseModel):
    question_content: str
    question_type: Optional[str] = None
    correct_answer: Optional[str] = None
    student_answer: Optional[str] = None
    score: Optional[float] = None
    source_type: str = "exam"
    source_id: Optional[str] = None


class HomeworkFeedbackCreate(BaseModel):
    feedback_type: str
    content: str


class HomeworkFeedbackReply(BaseModel):
    content: str