"""
地区模型
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Region(Base):
    __tablename__ = "regions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    level = Column(Integer, nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("regions.id"), nullable=True)
    parent_code = Column(String(20), nullable=True)
    sort_order = Column(Integer, default=0)

    is_active = Column(String(10), default="true")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_region_level", "level"),
        Index("idx_region_parent", "parent_id"),
        Index("idx_region_parent_code", "parent_code"),
    )
