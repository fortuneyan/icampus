"""
消息订阅模型
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class MessageSubscription(Base):
    __tablename__ = "message_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    channel = Column(String(50), nullable=False)
    message_type = Column(String(50), nullable=True)

    is_enabled = Column(String(10), default="true")

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_subscription_user_channel", "user_id", "channel", unique=True),
    )
