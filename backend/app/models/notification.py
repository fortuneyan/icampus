from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    notification_type = Column(String(20), nullable=False, default="notice")
    sender_id = Column(UUID(as_uuid=True), nullable=False)
    scope_type = Column(String(20), nullable=False, default="all")
    scope_ids = Column(JSON, nullable=True)
    is_urgent = Column(Boolean, default=False)
    status = Column(String(20), default="draft")
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)