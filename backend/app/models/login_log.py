"""
登录日志模型
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class LoginLog(Base):
    __tablename__ = "login_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    username = Column(String(100), nullable=True, index=True)

    login_type = Column(String(20), default="password")
    ip_address = Column(String(50), nullable=True)
    ip_location = Column(String(255), nullable=True)
    device = Column(String(100), nullable=True)
    browser = Column(String(100), nullable=True)

    status = Column(String(20), nullable=True)
    fail_reason = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.now, index=True)

    __table_args__ = (
        Index("idx_login_logs_user_id", "user_id"),
        Index("idx_login_logs_created_at", "created_at"),
    )
