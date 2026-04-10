"""
推荐记录模型
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Float, Index
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    resource_type = Column(String(50), nullable=False)
    resource_id = Column(UUID(as_uuid=True), nullable=False)
    resource_name = Column(String(255), nullable=True)

    recommendation_type = Column(String(50), nullable=True)
    score = Column(Float, default=0.0)
    reason = Column(String(255), nullable=True)

    is_clicked = Column(String(10), default="false")
    is_favorited = Column(String(10), default="false")

    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (Index("idx_recommendation_user", "user_id", "created_at"),)
