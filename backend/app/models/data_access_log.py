"""
数据访问日志模型
记录敏感数据访问，符合JY/T 0661-2025要求
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class DataAccessLog(Base):
    __tablename__ = "data_access_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    username = Column(String(100), nullable=True)

    resource_type = Column(String(50), nullable=True)
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    resource_name = Column(String(255), nullable=True)

    data_level = Column(String(10), nullable=True)

    operation = Column(String(50), nullable=True)

    status = Column(String(20), nullable=True)

    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now, index=True)

    __table_args__ = (
        Index("idx_data_access_user_id", "user_id"),
        Index("idx_data_access_data_level", "data_level"),
    )
