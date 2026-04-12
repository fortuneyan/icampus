"""
Smart Paper Generation System - Data Models

Uses different table names to avoid conflicts with existing exam.py models.
"""
from sqlalchemy import Column, String, Text, Integer, Numeric, JSON, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.core.database import Base


class SmartPaper(Base):
    """Smart paper model for generation system"""
    __tablename__ = "smart_papers"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic info
    title = Column(String(200), nullable=False, comment="Paper title")
    subject = Column(String(50), comment="Subject")
    grade_level = Column(String(20), comment="Grade level")
    paper_type = Column(String(20), default="normal", comment="normal/diagnostic/exam")
    
    # Generation params
    constraints = Column(JSON, comment="Generation constraints")
    generation_mode = Column(String(20), comment="manual/ai/greedy/diagnostic")
    
    # Question references
    question_ids = Column(JSON, comment="Question ID list")
    question_count = Column(Integer, default=0, comment="Question count")
    total_score = Column(Numeric(5, 1), default=100.0, comment="Total score")
    estimated_time = Column(Integer, comment="Estimated time in minutes")
    
    # Statistics
    difficulty_distribution = Column(JSON, comment="Actual difficulty distribution")
    knowledge_coverage = Column(JSON, comment="Knowledge coverage")
    cognitive_distribution = Column(JSON, comment="Cognitive level distribution")
    
    # A/B paper
    paired_paper_id = Column(UUID, comment="Paired paper ID")
    is_paired = Column(Boolean, default=False, comment="Is paired")
    is_paper_a = Column(Boolean, default=True, comment="Is paper A")
    
    # Status
    status = Column(String(20), default="draft", comment="draft/published/archived")
    
    # Source info
    source_student_id = Column(UUID, comment="Source student ID")
    source_diagnosis = Column(JSON, comment="Diagnosis report reference")
    
    # Audit
    creator_id = Column(UUID, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    published_at = Column(DateTime, comment="Published at")
    
    # Soft delete
    is_deleted = Column(Boolean, default=False, comment="Soft delete")


class SmartPaperQuestion(Base):
    """Smart paper - question association"""
    __tablename__ = "smart_paper_questions"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUID, ForeignKey("smart_papers.id"), nullable=False, index=True)
    question_id = Column(UUID, ForeignKey("questions.id"), nullable=False, index=True)
    
    # Position
    order = Column(Integer, nullable=False, comment="Question order")
    section = Column(String(50), comment="Section")
    
    # Score
    score = Column(Numeric(5, 1), default=5.0, comment="Score")
    
    # Attributes
    is_required = Column(Boolean, default=True, comment="Required")
    is_optional = Column(Boolean, default=False, comment="Optional")
    
    # A/B paper
    appears_in = Column(String(10), default="AB", comment="A/B/AB")
    
    created_at = Column(DateTime, default=datetime.now)


class SmartPaperVersion(Base):
    """Smart paper version record"""
    __tablename__ = "smart_paper_versions"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUID, ForeignKey("smart_papers.id"), nullable=False, index=True)
    
    # Version info
    version = Column(Integer, nullable=False, comment="Version number")
    change_summary = Column(Text, comment="Change summary")
    
    # Snapshot
    snapshot = Column(JSON, comment="Paper snapshot")
    question_snapshot = Column(JSON, comment="Question snapshot")
    
    # Creator
    created_by = Column(UUID, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now)


# Aliases for compatibility with models/__init__.py
Paper = SmartPaper
PaperQuestion = SmartPaperQuestion
PaperVersion = SmartPaperVersion
