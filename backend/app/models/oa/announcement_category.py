"""
公告分类模型
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.core.database import Base


class AnnouncementCategory(Base):
    """公告分类"""
    __tablename__ = "announcement_categories"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(50), nullable=False, comment="分类名称")
    code = Column(String(30), nullable=False, unique=True, comment="分类编码")
    color = Column(String(20), default="#1890ff", comment="分类颜色")
    icon = Column(String(100), nullable=True, comment="分类图标")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    description = Column(Text, nullable=True, comment="分类描述")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def __repr__(self):
        return f"<AnnouncementCategory(id={self.id}, name={self.name}, code={self.code})>"
