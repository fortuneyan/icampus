"""
一卡通管理模型
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class CampusCard(Base):
    """校园卡"""
    __tablename__ = "campus_cards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    card_no = Column(String(50), unique=True, nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    card_type = Column(String(20), default="student")  # student/teacher/temp
    status = Column(String(20), default="active")  # active/lost/disabled
    
    balance = Column(Integer, default=0)  # 余额（分）
    password = Column(String(100), nullable=True)
    
    issue_date = Column(DateTime, default=datetime.now)
    expire_date = Column(DateTime, nullable=True)
    lost_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_card_student", "student_id"),
    )


class CardTransaction(Base):
    """卡交易记录"""
    __tablename__ = "card_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    card_id = Column(UUID(as_uuid=True), ForeignKey("campus_cards.id", ondelete="CASCADE"), nullable=False)
    
    transaction_type = Column(String(20), nullable=False)  # consume/recharge/refund
    amount = Column(Integer, nullable=False)  # 金额（分）
    balance_before = Column(Integer, nullable=True)
    balance_after = Column(Integer, nullable=True)
    
    merchant_id = Column(String(50), nullable=True)
    merchant_name = Column(String(100), nullable=True)
    
    location = Column(String(200), nullable=True)
    device_no = Column(String(50), nullable=True)
    
    status = Column(String(20), default="success")  # success/failed/reversed
    remarks = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index("idx_transaction_card", "card_id"),
        Index("idx_transaction_time", "created_at"),
    )


class AccessRecord(Base):
    """门禁通行记录"""
    __tablename__ = "access_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    card_id = Column(UUID(as_uuid=True), ForeignKey("campus_cards.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), nullable=True)
    
    door_id = Column(String(50), nullable=False)
    door_name = Column(String(100), nullable=True)
    location = Column(String(200), nullable=True)
    
    access_type = Column(String(20), nullable=False)  # enter/exit
    access_result = Column(String(20), default="allow")  # allow/deny
    
    device_no = Column(String(50), nullable=True)
    capture_url = Column(String(500), nullable=True)
    
    temperature = Column(String(20), nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index("idx_access_card", "card_id"),
        Index("idx_access_student", "student_id"),
        Index("idx_access_time", "created_at"),
    )


class Merchant(Base):
    """商户"""
    __tablename__ = "card_merchants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    merchant_no = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    merchant_type = Column(String(50), nullable=True)  # canteen/shop/library
    
    location = Column(String(200), nullable=True)
    contact = Column(String(50), nullable=True)
    
    status = Column(String(20), default="active")
    remarks = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
