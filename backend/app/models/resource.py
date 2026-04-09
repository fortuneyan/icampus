from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ResourceCategory(Base):
    __tablename__ = "resource_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False)
    parent_id = Column(
        UUID(as_uuid=True), ForeignKey("resource_categories.id"), nullable=True
    )
    sort_order = Column(Integer, default=0)
    icon = Column(String(50), nullable=True)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.now)


class Resource(Base):
    __tablename__ = "resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    resource_type = Column(String(50), nullable=True)
    file_url = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    duration = Column(Integer, nullable=True)
    category_id = Column(
        UUID(as_uuid=True), ForeignKey("resource_categories.id"), nullable=True
    )
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=True)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    collect_count = Column(Integer, default=0)
    status = Column(String(20), default="published")
    tags = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
