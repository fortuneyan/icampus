"""
OA任务看板模块模型

包含项目表、任务表、任务评论表、任务附件表
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import (
    Column, String, Text, DateTime, Date, ForeignKey, Boolean,
    Integer, Numeric, JSON, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.soft_delete import SoftDeleteMixin
from app.models.timestamp import TimestampMixin


class OaTaskProject(Base, SoftDeleteMixin, TimestampMixin):
    """
    项目表

    任务看板所属的项目
    """
    __tablename__ = "oa_task_project"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 基本信息
    name = Column(String(200), nullable=False, comment="项目名称")
    description_md = Column(Text, nullable=True, comment="项目描述(Markdown)")

    # 负责人
    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="项目负责人ID"
    )

    # 组织归属
    org_id = Column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=True,
        comment="所属部门ID"
    )

    # 项目时间
    start_date = Column(Date, nullable=True, comment="开始日期")
    end_date = Column(Date, nullable=True, comment="结束日期")

    # 状态: ACTIVE-进行中 ARCHIVED-已归档
    status = Column(
        String(20),
        default="ACTIVE",
        nullable=False,
        comment="状态: ACTIVE-进行中 ARCHIVED-已归档"
    )

    # 配置
    config = Column(JSON, nullable=True, comment="项目配置")
    # 示例:
    # {
    #   "columns": ["TODO", "IN_PROGRESS", "REVIEW", "DONE"],
    #   "default_priority": "MEDIUM",
    #   "allow_subtasks": true,
    #   "require_due_date": false
    # }

    # 关联关系
    owner = relationship("User", lazy="selectin")
    org = relationship("Department", lazy="selectin")
    tasks = relationship(
        "OaTask",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    __table_args__ = (
        Index("idx_project_owner", "owner_id"),
        Index("idx_project_org", "org_id"),
        Index("idx_project_status", "status"),
    )

    def __repr__(self):
        return f"<OaTaskProject(id={self.id}, name={self.name}, status={self.status})>"


class OaTask(Base, SoftDeleteMixin, TimestampMixin):
    """
    任务表

    支持层级结构（父子任务）
    """
    __tablename__ = "oa_task"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 项目归属
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("oa_task_project.id", ondelete="CASCADE"),
        nullable=True,
        comment="项目ID"
    )

    # 父任务 (支持层级结构)
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("oa_task.id", ondelete="CASCADE"),
        nullable=True,
        comment="父任务ID"
    )

    # 任务基本信息
    title = Column(String(200), nullable=False, comment="任务标题")
    description_md = Column(Text, nullable=True, comment="任务描述(Markdown)")

    # 创建者和负责人
    creator_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="创建者ID"
    )
    assignee_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="负责人ID"
    )
    assignee_type = Column(
        String(20),
        nullable=True,
        comment="负责人类型: USER-用户 ROLE-角色 DEPARTMENT-部门"
    )
    assignee_value = Column(String(100), nullable=True, comment="负责人值(角色ID或部门ID)")

    # 优先级: LOW-低 MEDIUM-中 HIGH-高 URGENT-紧急
    priority = Column(
        String(20),
        default="MEDIUM",
        nullable=False,
        comment="优先级: LOW-低 MEDIUM-中 HIGH-高 URGENT-紧急"
    )

    # 状态: TODO-待处理 IN_PROGRESS-进行中 REVIEW-待审核 DONE-已完成 CANCELLED-已取消
    status = Column(
        String(20),
        default="TODO",
        nullable=False,
        comment="状态: TODO-待处理 IN_PROGRESS-进行中 REVIEW-待审核 DONE-已完成 CANCELLED-已取消"
    )

    # 进度
    progress = Column(Integer, default=0, nullable=False, comment="进度(0-100)")

    # 时间
    start_date = Column(Date, nullable=True, comment="开始日期")
    due_date = Column(Date, nullable=True, comment="截止日期")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")

    # 工时
    estimated_hours = Column(Numeric(6, 2), nullable=True, comment="预计工时")
    actual_hours = Column(Numeric(6, 2), nullable=True, comment="实际工时")

    # 标签和排序
    tags = Column(JSON, nullable=True, comment="标签列表")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序顺序")

    # 关联关系
    project = relationship("OaTaskProject", back_populates="tasks")
    parent = relationship("OaTask", remote_side=[id], backref="children", lazy="selectin")
    creator = relationship("User", foreign_keys=[creator_id], lazy="selectin")
    assignee = relationship("User", foreign_keys=[assignee_id], lazy="selectin")
    comments = relationship(
        "OaTaskComment",
        back_populates="task",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    attachments = relationship(
        "OaTaskAttachment",
        back_populates="task",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    __table_args__ = (
        Index("idx_task_project", "project_id"),
        Index("idx_task_parent", "parent_id"),
        Index("idx_task_assignee", "assignee_id"),
        Index("idx_task_creator", "creator_id"),
        Index("idx_task_status", "status"),
        Index("idx_task_priority", "priority"),
        Index("idx_task_due_date", "due_date"),
        Index("idx_task_assignee_status", "assignee_id", "status"),
    )

    def __repr__(self):
        return f"<OaTask(id={self.id}, title={self.title}, status={self.status})>"


class OaTaskComment(Base, SoftDeleteMixin, TimestampMixin):
    """
    任务评论表

    支持 @提及 功能
    """
    __tablename__ = "oa_task_comment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 关联任务
    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("oa_task.id", ondelete="CASCADE"),
        nullable=False,
        comment="任务ID"
    )

    # 评论者
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="评论者ID"
    )

    # 父评论 (支持嵌套回复)
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("oa_task_comment.id", ondelete="CASCADE"),
        nullable=True,
        comment="父评论ID"
    )

    # 内容
    content_md = Column(Text, nullable=False, comment="评论内容(Markdown)")
    content_html = Column(Text, nullable=True, comment="评论内容(HTML)")

    # @提及的用户
    mentions = Column(JSON, nullable=True, comment="提及的用户ID列表")

    # 是否已编辑
    is_edited = Column(Boolean, default=False, nullable=False, comment="是否已编辑")
    edited_at = Column(DateTime, nullable=True, comment="编辑时间")

    # 关联关系
    task = relationship("OaTask", back_populates="comments")
    user = relationship("User", lazy="selectin")
    parent = relationship("OaTaskComment", remote_side=[id], backref="replies", lazy="selectin")

    __table_args__ = (
        Index("idx_comment_task", "task_id"),
        Index("idx_comment_user", "user_id"),
        Index("idx_comment_parent", "parent_id"),
    )

    def __repr__(self):
        return f"<OaTaskComment(id={self.id}, task_id={self.task_id}, user_id={self.user_id})>"


class OaTaskAttachment(Base, SoftDeleteMixin, TimestampMixin):
    """
    任务附件表
    """
    __tablename__ = "oa_task_attachment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 关联任务
    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("oa_task.id", ondelete="CASCADE"),
        nullable=False,
        comment="任务ID"
    )

    # 上传者
    uploader_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="上传者ID"
    )

    # 文件信息
    file_name = Column(String(255), nullable=False, comment="文件名")
    file_url = Column(String(500), nullable=False, comment="文件URL")
    file_size = Column(Integer, nullable=True, comment="文件大小(字节)")
    file_type = Column(String(50), nullable=True, comment="文件类型/MIME")

    # 预览信息
    thumbnail_url = Column(String(500), nullable=True, comment="缩略图URL")

    # 关联关系
    task = relationship("OaTask", back_populates="attachments")
    uploader = relationship("User", lazy="selectin")

    __table_args__ = (
        Index("idx_attachment_task", "task_id"),
        Index("idx_attachment_uploader", "uploader_id"),
    )

    def __repr__(self):
        return f"<OaTaskAttachment(id={self.id}, task_id={self.task_id}, file_name={self.file_name})>"
