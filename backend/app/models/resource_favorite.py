"""
资源收藏模型
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ResourceFavorite(Base):
    __tablename__ = "resource_favorites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    resource_id = Column(UUID(as_uuid=True), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_name = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index("idx_favorite_user_resource", "user_id", "resource_id", unique=True),
    )
