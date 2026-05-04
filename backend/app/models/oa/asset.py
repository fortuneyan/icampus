"""
OA资产管理模块模型

包含资产分类表、资产主表、借用记录表
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


class OaAssetCategory(Base, TimestampMixin):
    """
    资产分类表

    资产分类的树形结构
    """
    __tablename__ = "oa_asset_category"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 分类信息
    name = Column(String(100), nullable=False, comment="分类名称")
    code = Column(String(50), nullable=False, unique=True, comment="分类编码")
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("oa_asset_category.id", ondelete="CASCADE"),
        nullable=True,
        comment="父分类ID"
    )

    # 分类属性
    icon = Column(String(100), nullable=True, comment="分类图标")
    description = Column(Text, nullable=True, comment="分类描述")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序顺序")

    # 关联关系
    parent = relationship(
        "OaAssetCategory",
        remote_side=[id],
        backref="children",
        lazy="selectin"
    )
    assets = relationship(
        "OaAsset",
        back_populates="category",
        lazy="selectin"
    )

    __table_args__ = (
        Index("idx_asset_category_parent", "parent_id"),
        Index("idx_asset_category_code", "code"),
        Index("idx_asset_category_sort", "sort_order"),
    )

    def __repr__(self):
        return f"<OaAssetCategory(id={self.id}, name={self.name}, code={self.code})>"


class OaAsset(Base, SoftDeleteMixin, TimestampMixin):
    """
    资产主表

    管理系统中的固定资产、办公设备等
    """
    __tablename__ = "oa_asset"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 基本信息
    name = Column(String(200), nullable=False, comment="资产名称")
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("oa_asset_category.id", ondelete="SET NULL"),
        nullable=True,
        comment="资产分类ID"
    )
    asset_code = Column(String(100), nullable=False, unique=True, comment="资产编号")
    barcode = Column(String(100), nullable=True, comment="条形码")
    qr_code = Column(String(255), nullable=True, comment="二维码")

    # 品牌型号
    brand = Column(String(100), nullable=True, comment="品牌")
    model = Column(String(100), nullable=True, comment="型号")
    spec_md = Column(Text, nullable=True, comment="规格参数(Markdown)")
    description_md = Column(Text, nullable=True, comment="资产描述(Markdown)")

    # 采购信息
    purchase_date = Column(Date, nullable=True, comment="采购日期")
    purchase_price = Column(Numeric(12, 2), nullable=True, comment="采购价格")
    supplier = Column(String(200), nullable=True, comment="供应商")
    warranty_expire = Column(Date, nullable=True, comment="保修截止日期")

    # 当前位置
    current_org_id = Column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        comment="当前所属部门"
    )
    storage_location = Column(String(200), nullable=True, comment="存放位置")

    # 资产状态: IDLE-闲置 BORROWED-已借出 MAINTENANCE-维修中 SCRAPPED-已报废
    status = Column(
        String(20),
        default="IDLE",
        nullable=False,
        comment="状态: IDLE-闲置 BORROWED-已借出 MAINTENANCE-维修中 SCRAPPED-已报废"
    )

    # 图片
    image_urls = Column(JSON, nullable=True, comment="资产图片URL列表")

    # 关联关系
    category = relationship("OaAssetCategory", back_populates="assets")
    current_org = relationship("Department", lazy="selectin")
    borrow_records = relationship(
        "OaBorrowRecord",
        back_populates="asset",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    __table_args__ = (
        Index("idx_asset_code", "asset_code"),
        Index("idx_asset_category", "category_id"),
        Index("idx_asset_status", "status"),
        Index("idx_asset_org", "current_org_id"),
        Index("idx_asset_barcode", "barcode"),
    )

    def __repr__(self):
        return f"<OaAsset(id={self.id}, name={self.name}, code={self.asset_code}, status={self.status})>"


class OaBorrowRecord(Base, SoftDeleteMixin, TimestampMixin):
    """
    借用记录表

    记录资产的借用/归还流程
    """
    __tablename__ = "oa_borrow_record"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # 关联资产
    asset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("oa_asset.id", ondelete="CASCADE"),
        nullable=False,
        comment="资产ID"
    )

    # 关联工作流实例 (可选，用于审批流程)
    workflow_instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("oa_workflow_instance.id", ondelete="SET NULL"),
        nullable=True,
        comment="工作流实例ID"
    )

    # 借用人
    borrower_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="借用人ID"
    )

    # 借用信息
    purpose_md = Column(Text, nullable=True, comment="借用用途(Markdown)")

    # 时间
    borrow_date = Column(Date, nullable=False, comment="借用日期")
    expected_return_date = Column(Date, nullable=False, comment="预计归还日期")
    actual_return_date = Column(Date, nullable=True, comment="实际归还日期")

    # 归还信息
    actual_return_condition = Column(Text, nullable=True, comment="实际归还状态描述")

    # 状态: PENDING-待审批 APPROVED-已批准 BORROWED-使用中 RETURNED-已归还 OVERDUE-已超期 REJECTED-已拒绝
    status = Column(
        String(20),
        default="PENDING",
        nullable=False,
        comment="状态: PENDING-待审批 APPROVED-已批准 BORROWED-使用中 RETURNED-已归还 OVERDUE-已超期 REJECTED-已拒绝"
    )

    # 审批信息
    approver_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="审批人ID"
    )
    approver_comment = Column(Text, nullable=True, comment="审批意见")
    approved_at = Column(DateTime, nullable=True, comment="审批时间")

    # 提醒
    reminder_count = Column(Integer, default=0, nullable=False, comment="催还提醒次数")
    last_reminder_at = Column(DateTime, nullable=True, comment="最后提醒时间")

    # 关联关系
    asset = relationship("OaAsset", back_populates="borrow_records")
    borrower = relationship("User", foreign_keys=[borrower_id], lazy="selectin")
    approver = relationship("User", foreign_keys=[approver_id], lazy="selectin")
    workflow_instance = relationship("OaWorkflowInstance", lazy="selectin")

    __table_args__ = (
        Index("idx_borrow_asset", "asset_id"),
        Index("idx_borrow_borrower", "borrower_id"),
        Index("idx_borrow_status", "status"),
        Index("idx_borrow_expected_return", "expected_return_date"),
        Index("idx_borrow_workflow", "workflow_instance_id"),
        Index("idx_borrow_overdue", "status", postgresql_where=status == "OVERDUE"),
        # 检查约束: 实际归还日期不能早于借用日期
        CheckConstraint(
            "actual_return_date IS NULL OR actual_return_date >= borrow_date",
            name="ck_borrow_return_date"
        ),
    )

    def __repr__(self):
        return f"<OaBorrowRecord(id={self.id}, asset_id={self.asset_id}, status={self.status})>"
