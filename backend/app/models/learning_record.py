"""
学习记录模型
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Integer, Float, Index
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class LearningRecord(Base):
    __tablename__ = "learning_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    resource_type = Column(String(50), nullable=True)
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    resource_name = Column(String(255), nullable=True)

    action_type = Column(String(50), nullable=False)
    duration = Column(Integer, default=0)

    progress = Column(Float, default=0.0)
    score = Column(Float, nullable=True)

    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (Index("idx_learning_user_action", "user_id", "action_type"),)
