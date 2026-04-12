"""
学生成长档案模型
"""
from datetime import datetime, date
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class GrowthRecord(Base):
    """成长记录"""
    __tablename__ = "growth_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # 记录类型
    record_type = Column(String(50), nullable=False)  # photo/video/honor/activity/comment
    
    # 基本信息
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    
    # 附件
    attachment_url = Column(String(500), nullable=True)  # 图片/视频URL
    attachment_urls = Column(Text, nullable=True)  # 多个附件，JSON格式存储
    
    # 标签/分类
    tags = Column(String(500), nullable=True)  # 逗号分隔
    
    # 时间和学期
    record_date = Column(DateTime, nullable=True)
    academic_year = Column(String(20), nullable=True)
    semester = Column(String(20), nullable=True)
    
    # 可见性
    is_public = Column(Boolean, default=False)  # 是否对家长可见
    is_featured = Column(Boolean, default=False)  # 是否精选
    
    # 状态
    status = Column(String(20), default="draft")  # draft/published
    
    # 审核
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # 元数据
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index("idx_growth_student_type", "student_id", "record_type"),
        Index("idx_growth_date", "record_date"),
    )


class GrowthComment(Base):
    """成长记录评论"""
    __tablename__ = "growth_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    record_id = Column(UUID(as_uuid=True), ForeignKey("growth_records.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    user_name = Column(String(100), nullable=True)
    
    content = Column(Text, nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("growth_comments.id", ondelete="CASCADE"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
