"""
OA教室预约模块模型

包含教室/场地表、预约记录表
"""
from datetime import datetime, date, time as dt_time
from decimal import Decimal
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import (
    Column, String, Text, DateTime, Date, Time, ForeignKey, Boolean,
    Integer, Numeric, JSON, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.soft_delete import SoftDeleteMixin
from app.models.timestamp import TimestampMixin


class OaRoom(Base, SoftDeleteMixin, TimestampMixin):
    """
    教室/场地表

    管理系统中的教室、会议室、实验室、活动室等场地
    """
    __tablename__ = "oa_room"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 基本信息
    name = Column(String(100), nullable=False, comment="场地名称")
    room_type = Column(
        String(20),
        nullable=False,
        comment="场地类型: CLASSROOM-教室 MEETING_ROOM-会议室 LAB-实验室 ACTIVITY_ROOM-活动室 OTHER-其他"
    )
    building = Column(String(50), nullable=True, comment="所在楼宇")
    floor = Column(Integer, nullable=True, comment="所在楼层")
    capacity = Column(Integer, nullable=True, comment="容纳人数")
    area_sqm = Column(Numeric(10, 2), nullable=True, comment="面积(平方米)")

    # 位置描述
    location = Column(String(200), nullable=True, comment="详细位置描述")

    # 设备信息
    equipment = Column(JSON, nullable=True, comment="设备清单(JSON)")
    equipment_md = Column(Text, nullable=True, comment="设备说明(Markdown)")

    # 预约规则
    booking_rules = Column(JSON, nullable=True, comment="预约规则配置")
    # 示例规则:
    # {
    #   "min_advance_hours": 1,           # 最小提前预约时间(小时)
    #   "max_advance_days": 30,           # 最大提前预约天数
    #   "max_duration_hours": 4,          # 单次最大预约时长(小时)
    #   "allowed_weekdays": [1,2,3,4,5],  # 允许预约的星期(0-6)
    #   "time_slots": [                   # 可用时间段
    #       {"start": "08:00", "end": "12:00"},
    #       {"start": "14:00", "end": "18:00"}
    #   ],
    #   "auto_approve": false             # 是否自动审批
    # }

    # 组织归属
    org_id = Column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        comment="归属组织ID"
    )

    # 状态
    status = Column(
        String(20),
        default="ACTIVE",
        nullable=False,
        comment="状态: ACTIVE-可用 MAINTENANCE-维护中 DISABLED-已停用"
    )

    # 关联关系
    bookings = relationship(
        "OaRoomBooking",
        back_populates="room",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    __table_args__ = (
        Index("idx_room_type", "room_type"),
        Index("idx_room_building", "building"),
        Index("idx_room_status", "status"),
        Index("idx_room_org", "org_id"),
    )

    def __repr__(self):
        return f"<OaRoom(id={self.id}, name={self.name}, type={self.room_type})>"


class OaRoomBooking(Base, SoftDeleteMixin, TimestampMixin):
    """
    预约记录表

    记录场地预约信息
    """
    __tablename__ = "oa_room_booking"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 关联场地
    room_id = Column(
        UUID(as_uuid=True),
        ForeignKey("oa_room.id", ondelete="CASCADE"),
        nullable=False,
        comment="场地ID"
    )

    # 关联工作流实例 (可选，用于审批流程)
    workflow_instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("oa_workflow_instance.id", ondelete="SET NULL"),
        nullable=True,
        comment="工作流实例ID"
    )

    # 申请人
    applicant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="申请人ID"
    )

    # 预约信息
    title = Column(String(200), nullable=False, comment="预约标题")
    agenda_md = Column(Text, nullable=True, comment="会议议程(Markdown)")
    attendee_count = Column(Integer, default=1, nullable=False, comment="参加人数")
    attendees = Column(JSON, nullable=True, comment="参与者ID列表")

    # 预约时间 (核心时间字段)
    booking_date = Column(Date, nullable=False, comment="预约日期")
    start_time = Column(Time, nullable=False, comment="开始时间")
    end_time = Column(Time, nullable=False, comment="结束时间")

    # 合并的时间戳字段 (用于查询和排他约束)
    start_datetime = Column(DateTime, nullable=True, comment="开始时间戳")
    end_datetime = Column(DateTime, nullable=True, comment="结束时间戳")

    # 状态
    status = Column(
        String(20),
        default="PENDING",
        nullable=False,
        comment="状态: PENDING-待审批 APPROVED-已通过 REJECTED-已拒绝 CANCELLED-已取消"
    )

    # 审批信息
    reject_reason = Column(Text, nullable=True, comment="拒绝原因")

    # 提醒
    reminder_sent = Column(Boolean, default=False, nullable=False, comment="是否已发送提醒")

    # 取消信息
    cancelled_at = Column(DateTime, nullable=True, comment="取消时间")
    cancel_reason = Column(Text, nullable=True, comment="取消原因")

    # 关联关系
    room = relationship("OaRoom", back_populates="bookings")
    applicant = relationship("User", foreign_keys=[applicant_id], lazy="selectin")
    workflow_instance = relationship("OaWorkflowInstance", lazy="selectin")

    __table_args__ = (
        Index("idx_booking_room_date", "room_id", "booking_date"),
        Index("idx_booking_applicant", "applicant_id"),
        Index("idx_booking_status", "status"),
        Index("idx_booking_date", "booking_date"),
        Index("idx_booking_workflow", "workflow_instance_id"),
        # 排他约束: 同一场地同一日期内时间段不能重叠
        # 注意: 此约束在迁移脚本中创建，使用 btree 类型
        # CREATE EXTENSION IF NOT EXISTS btree_gist;
        # ALTER TABLE oa_room_booking ADD CONSTRAINT no_time_overlap
        #   EXCLUDE USING gist (
        #     room_id WITH =,
        #     tstzrange(start_datetime, end_datetime) WITH &&
        #   ) WHERE (status NOT IN ('CANCELLED', 'REJECTED'));
    )

    def __repr__(self):
        return f"<OaRoomBooking(id={self.id}, room_id={self.room_id}, date={self.booking_date})>"
