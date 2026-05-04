"""
OA工作日志模块模型

包含工作日志表
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


class OaWorkLog(Base, SoftDeleteMixin, TimestampMixin):
    """
    工作日志表

    记录日常工作日志，支持日报、周报、月报
    """
    __tablename__ = "oa_work_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 作者信息
    author_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="作者ID"
    )

    # 日志类型: DAILY-日报 WEEKLY-周报 MONTHLY-月报
    log_type = Column(
        String(20),
        nullable=False,
        comment="日志类型: DAILY-日报 WEEKLY-周报 MONTHLY-月报"
    )

    # 时间周期
    period_start = Column(Date, nullable=False, comment="周期开始日期")
    period_end = Column(Date, nullable=False, comment="周期结束日期")
    week_number = Column(Integer, nullable=True, comment="周数(ISO周)")
    year = Column(Integer, nullable=True, comment="年份")
    month = Column(Integer, nullable=True, comment="月份")

    # 日志内容 (Markdown格式)
    summary_md = Column(Text, nullable=True, comment="本周期工作总结(Markdown)")
    plan_md = Column(Text, nullable=True, comment="下周期工作计划(Markdown)")
    attachment_urls = Column(JSON, nullable=True, comment="附件URL列表")

    # 统计数据
    total_hours = Column(Numeric(5, 2), nullable=True, comment="总工时")
    task_count = Column(Integer, default=0, nullable=False, comment="完成任务数")
    bug_count = Column(Integer, default=0, nullable=False, comment="处理Bug数")

    # 审核信息
    reviewer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="审核人ID"
    )
    review_md = Column(Text, nullable=True, comment="审核意见(Markdown)")
    review_status = Column(
        String(20),
        default="PENDING",
        nullable=False,
        comment="审核状态: PENDING-待审核 REVIEWED-已审核 REVISION_REQUIRED-需修改"
    )
    review_at = Column(DateTime, nullable=True, comment="审核时间")

    # 提交状态
    submitted_at = Column(DateTime, nullable=True, comment="提交时间")
    is_draft = Column(Boolean, default=True, nullable=False, comment="是否草稿")

    # 提醒状态
    reminder_sent = Column(Boolean, default=False, nullable=False, comment="是否已发送提醒")

    # 关联关系
    author = relationship("User", foreign_keys=[author_id], lazy="selectin")
    reviewer = relationship("User", foreign_keys=[reviewer_id], lazy="selectin")

    __table_args__ = (
        # 唯一约束: 同一作者、同一类型、同一周期只能有一条日志
        UniqueConstraint(
            "author_id", "log_type", "period_start",
            name="uq_worklog_author_type_period"
        ),
        Index("idx_worklog_author", "author_id"),
        Index("idx_worklog_type", "log_type"),
        Index("idx_worklog_period", "period_start", "period_end"),
        Index("idx_worklog_reviewer", "reviewer_id"),
        Index("idx_worklog_review_status", "review_status"),
        Index("idx_worklog_submitted", "is_draft", postgresql_where=is_draft == False),
        # 检查约束: 结束日期不能早于开始日期
        CheckConstraint(
            "period_end >= period_start",
            name="ck_worklog_period"
        ),
    )

    def __repr__(self):
        return f"<OaWorkLog(id={self.id}, author_id={self.author_id}, type={self.log_type}, period={self.period_start})>"

    def calculate_week_number(self) -> int:
        """计算ISO周数"""
        from datetime import date
        if self.period_start:
            # ISO周数: 周一作为一周开始
            return self.period_start.isocalendar()[1]
        return 0

    def before_insert(self, mapper, connection):
        """插入前钩子"""
        if self.period_start:
            self.year = self.period_start.year
            self.month = self.period_start.month
            self.week_number = self.calculate_week_number()
