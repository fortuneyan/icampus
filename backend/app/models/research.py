"""
教研课题模型
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ResearchProject(Base):
    __tablename__ = "research_projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    leader_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    project_no = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    project_type = Column(String(50), nullable=True)

    background = Column(Text, nullable=True)
    objectives = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    methods = Column(Text, nullable=True)
    expected_results = Column(Text, nullable=True)

    funding = Column(String(50), nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    status = Column(String(20), default="pending")
    reviewer_id = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_comment = Column(Text, nullable=True)

    members = Column(Text, nullable=True)
    attachments = Column(Text, nullable=True)

    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (Index("idx_research_status", "status"),)
