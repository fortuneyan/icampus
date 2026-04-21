from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Boolean, JSON, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Homework(Base):
    __tablename__ = "homeworks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=True)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    grade_id = Column(UUID(as_uuid=True), ForeignKey("grades.id"), nullable=True)
    class_ids = Column(JSON, nullable=True)
    
    homework_type = Column(String(20), default="online")
    total_score = Column(Numeric(5, 1), default=100)
    
    submit_start = Column(DateTime, nullable=True)
    submit_end = Column(DateTime, nullable=True)
    
    attachments = Column(JSON, nullable=True)
    status = Column(String(20), default="draft")
    
    notify_enabled = Column(Boolean, default=True)
    notification_id = Column(UUID(as_uuid=True), ForeignKey("notifications.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class HomeworkSubmission(Base):
    __tablename__ = "homework_submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    homework_id = Column(UUID(as_uuid=True), ForeignKey("homeworks.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    
    content = Column(Text, nullable=True)
    attachment_urls = Column(JSON, nullable=True)
    score = Column(Numeric(5, 1), nullable=True)
    feedback = Column(Text, nullable=True)
    
    status = Column(String(20), default="submitted")
    submitted_at = Column(DateTime, nullable=True)
    graded_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class WrongQuestion(Base):
    __tablename__ = "wrong_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=True)
    
    question_content = Column(Text, nullable=False)
    question_type = Column(String(20), nullable=True)
    correct_answer = Column(Text, nullable=True)
    student_answer = Column(Text, nullable=True)
    score = Column(Numeric(5, 1), nullable=True)
    
    source_type = Column(String(20), default="exam")
    source_id = Column(String(100), nullable=True)
    
    is_reviewed = Column(Boolean, default=False)
    is_mastered = Column(Boolean, default=False)
    review_count = Column(Integer, default=0)
    last_reviewed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)


class HomeworkFeedback(Base):
    __tablename__ = "homework_feedbacks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    homework_id = Column(UUID(as_uuid=True), ForeignKey("homeworks.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    feedback_type = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class HomeworkNotification(Base):
    __tablename__ = "homework_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    homework_id = Column(UUID(as_uuid=True), ForeignKey("homeworks.id"), nullable=False)
    notification_id = Column(UUID(as_uuid=True), ForeignKey("notifications.id"), nullable=False)
    
    include_wrong_questions = Column(Boolean, default=False)
    wrong_question_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.now)
