"""
数据字典模型
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class DictionaryType(Base):
    """字典类型"""
    __tablename__ = "dictionary_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False, comment="字典名称")
    code = Column(String(50), unique=True, nullable=False, index=True, comment="字典编码")
    description = Column(Text, nullable=True, comment="描述")
    status = Column(String(20), default="active", comment="状态")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    items = relationship("DictionaryItem", back_populates="dict_type", cascade="all, delete-orphan")


class DictionaryItem(Base):
    """字典项"""
    __tablename__ = "dictionary_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    type_id = Column(UUID(as_uuid=True), ForeignKey("dictionary_types.id", ondelete="CASCADE"), nullable=False, comment="字典类型ID")
    label = Column(String(100), nullable=False, comment="字典标签")
    value = Column(String(255), nullable=False, comment="字典值")
    sort_order = Column(Integer, default=0, comment="排序")
    status = Column(String(20), default="active", comment="状态")
    remark = Column(Text, nullable=True, comment="备注")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    dict_type = relationship("DictionaryType", back_populates="items")
