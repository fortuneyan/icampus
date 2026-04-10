"""
加密密钥模型
符合JY/T 0661-2025 L4级别保护要求
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class EncryptionKey(Base):
    __tablename__ = "encryption_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    key_name = Column(String(100), nullable=False, unique=True)
    key_value = Column(Text, nullable=False)
    algorithm = Column(String(50), default="AES-256")

    is_active = Column(String(10), default="true")
    expires_at = Column(DateTime, nullable=True)

    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (Index("idx_key_name", "key_name"),)
