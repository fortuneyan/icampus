from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class AISession(Base):
    __tablename__ = "ai_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=True)
    model_type = Column(String(50), default="deepseek")
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    messages = relationship("AIMessage", back_populates="session")


class AIMessage(Base):
    __tablename__ = "ai_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("ai_sessions.id"), nullable=False
    )
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    session = relationship("AISession", back_populates="messages")


class AIConfig(Base):
    __tablename__ = "ai_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    model_type = Column(String(50), nullable=False)
    api_key = Column(String(500), nullable=True)
    api_url = Column(String(500), nullable=True)
    temperature = Column(Integer, default=80)
    max_tokens = Column(Integer, default=2000)
    status = Column(String(20), default="active")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
