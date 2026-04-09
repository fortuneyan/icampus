from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Notice(Base):
    __tablename__ = "notices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    notice_type = Column(String(20), default="system")
    priority = Column(Integer, default=0)
    publisher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    target_type = Column(String(20), default="all")
    target_ids = Column(JSON, nullable=True)
    attachment_url = Column(String(500), nullable=True)
    published_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="draft")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class NoticeRead(Base):
    __tablename__ = "notice_reads"

    notice_id = Column(UUID(as_uuid=True), ForeignKey("notices.id"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    read_at = Column(DateTime, default=datetime.now)
