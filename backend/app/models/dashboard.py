from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ReportConfig(Base):
    __tablename__ = "report_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False)
    report_type = Column(String(50), nullable=False)
    config = Column(JSON, nullable=True)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    msg_type = Column(String(20), default="system")
    priority = Column(Integer, default=0)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_value = Column(Text, nullable=True)
    value_type = Column(String(20), default="string")
    description = Column(String(200), nullable=True)
    is_system = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
