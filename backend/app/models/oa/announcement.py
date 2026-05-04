"""
OA公告模块模型

包含公告主表、已读记录表、评论表
"""
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, Boolean,
    Integer, JSON, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.soft_delete import SoftDeleteMixin
from app.models.timestamp import TimestampMixin


class OaAnnouncement(Base, SoftDeleteMixin, TimestampMixin):
    """
    公告主表

    存储系统公告，支持全文搜索、软删除、优先级排序
    """
    __tablename__ = "oa_announcement"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 基本信息
    title = Column(String(200), nullable=False, comment="公告标题")
    content_md = Column(Text, nullable=False, default="", comment="公告正文(Markdown)")
    content_html = Column(Text, nullable=True, comment="公告正文(HTML缓存)")

    # 作者信息
    author_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="作者ID"
    )

    # 分类信息
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("announcement_categories.id", ondelete="SET NULL"),
        nullable=True,
        comment="分类ID"
    )

    # 可见范围
    org_scope = Column(JSON, nullable=True, comment="可见范围(组织结构)")
    role_scope = Column(JSON, nullable=True, comment="可见范围(角色)")

    # 公告属性
    priority = Column(
        Integer,
        default=0,
        nullable=False,
        comment="优先级: 0-普通 1-重要 2-紧急"
    )
    status = Column(
        String(20),
        default="DRAFT",
        nullable=False,
        comment="状态: DRAFT-草稿 PUBLISHED-已发布 ARCHIVED-已归档"
    )
    publish_time = Column(DateTime, nullable=True, comment="发布时间")

    # 显示控制
    pin_top = Column(Boolean, default=False, nullable=False, comment="是否置顶")
    allow_comment = Column(Boolean, default=True, nullable=False, comment="是否允许评论")

    # 附件
    attachment_urls = Column(JSON, nullable=True, comment="附件URL列表")

    # 统计
    read_count = Column(Integer, default=0, nullable=False, comment="阅读次数")
    comment_count = Column(Integer, default=0, nullable=False, comment="评论数")

    # 全文搜索向量 (PostgreSQL TSVECTOR)
    search_vector = Column(
        TSVECTOR,
        nullable=True,
        comment="全文搜索向量"
    )

    # 关系
    author = relationship("User", foreign_keys=[author_id], lazy="selectin")
    category = relationship("AnnouncementCategory", foreign_keys=[category_id], lazy="selectin")
    read_records = relationship(
        "OaAnnouncementRead",
        back_populates="announcement",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    comments = relationship(
        "OaAnnouncementComment",
        back_populates="announcement",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    __table_args__ = (
        # 索引
        Index("idx_announcement_author", "author_id"),
        Index("idx_announcement_category", "category_id"),
        Index("idx_announcement_status", "status"),
        Index("idx_announcement_priority", "priority"),
        Index("idx_announcement_publish_time", "publish_time"),
        Index("idx_announcement_pintop", "pin_top"),
        # 全文搜索索引
        Index(
            "idx_announcement_search",
            search_vector,
            postgresql_using="gin"
        ),
    )

    def __repr__(self):
        return f"<OaAnnouncement(id={self.id}, title={self.title}, status={self.status})>"


class OaAnnouncementRead(Base, TimestampMixin):
    """
    公告已读记录表

    记录用户对公告的阅读情况
    """
    __tablename__ = "oa_announcement_read"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 公告ID
    announcement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("oa_announcement.id", ondelete="CASCADE"),
        nullable=False,
        comment="公告ID"
    )

    # 用户ID
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID"
    )

    # 阅读时间
    read_at = Column(DateTime, default=datetime.now, nullable=False, comment="阅读时间")

    # 关系
    announcement = relationship("OaAnnouncement", back_populates="read_records")
    user = relationship("User", lazy="selectin")

    __table_args__ = (
        # 唯一约束: 每个用户对每条公告只能有一条已读记录
        UniqueConstraint("announcement_id", "user_id", name="uq_announcement_read"),
        Index("idx_announcement_read_user", "user_id"),
        Index("idx_announcement_read_announcement", "announcement_id"),
    )

    def __repr__(self):
        return f"<OaAnnouncementRead(id={self.id}, announcement_id={self.announcement_id}, user_id={self.user_id})>"


class OaAnnouncementComment(Base, SoftDeleteMixin, TimestampMixin):
    """
    公告评论表

    支持嵌套评论结构
    """
    __tablename__ = "oa_announcement_comment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 公告ID
    announcement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("oa_announcement.id", ondelete="CASCADE"),
        nullable=False,
        comment="公告ID"
    )

    # 评论者
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="评论者ID"
    )

    # 父评论ID (用于嵌套回复)
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("oa_announcement_comment.id", ondelete="CASCADE"),
        nullable=True,
        comment="父评论ID"
    )

    # 评论内容
    content_md = Column(Text, nullable=False, comment="评论内容(Markdown)")
    content_html = Column(Text, nullable=True, comment="评论内容(HTML)")

    # 回复目标
    reply_to_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="回复目标用户ID"
    )

    # 关系
    announcement = relationship("OaAnnouncement", back_populates="comments")
    user = relationship("User", foreign_keys=[user_id], lazy="selectin")
    reply_to_user = relationship("User", foreign_keys=[reply_to_user_id], lazy="selectin")
    parent = relationship("OaAnnouncementComment", remote_side=[id], lazy="selectin")
    replies = relationship(
        "OaAnnouncementComment",
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    __table_args__ = (
        Index("idx_comment_announcement", "announcement_id"),
        Index("idx_comment_user", "user_id"),
        Index("idx_comment_parent", "parent_id"),
    )

    def __repr__(self):
        return f"<OaAnnouncementComment(id={self.id}, announcement_id={self.announcement_id}, user_id={self.user_id})>"
