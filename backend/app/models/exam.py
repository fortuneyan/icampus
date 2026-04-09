from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Numeric,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ExamPaper(Base):
    __tablename__ = "exam_papers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(200), nullable=False)
    paper_type = Column(String(20), default="practice")
    total_score = Column(Numeric(5, 1), default=100)
    duration = Column(Integer, default=90)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=True)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status = Column(String(20), default="draft")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    content = Column(Text, nullable=False)
    question_type = Column(String(20), default="single")
    options = Column(JSON, nullable=True)
    answer = Column(Text, nullable=True)
    analysis = Column(Text, nullable=True)
    difficulty = Column(Integer, default=1)
    score = Column(Numeric(5, 1), default=5)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class PaperQuestion(Base):
    __tablename__ = "paper_questions"

    paper_id = Column(
        UUID(as_uuid=True), ForeignKey("exam_papers.id"), primary_key=True
    )
    question_id = Column(
        UUID(as_uuid=True), ForeignKey("questions.id"), primary_key=True
    )
    order_num = Column(Integer, default=0)
    score = Column(Numeric(5, 1), default=5)
