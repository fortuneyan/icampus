"""
操作日志模型
记录用户操作行为，符合JY/T 0643-2025要求
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    username = Column(String(100), nullable=True)

    module = Column(String(50), nullable=True)
    action = Column(String(50), nullable=True)
    operation = Column(String(100), nullable=True)

    method = Column(String(10), nullable=True)
    path = Column(String(255), nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)

    status_code = Column(Integer, nullable=True)
    response_time = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    request_body = Column(Text, nullable=True)
    response_body = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.now, index=True)

    __table_args__ = (
        Index("idx_operation_logs_user_id", "user_id"),
        Index("idx_operation_logs_module", "module"),
        Index("idx_operation_logs_created_at", "created_at"),
    )
