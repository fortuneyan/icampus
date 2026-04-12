"""
图书管理模型
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Book(Base):
    """图书"""
    __tablename__ = "books"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    isbn = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    author = Column(String(100), nullable=True)
    publisher = Column(String(100), nullable=True)
    publish_date = Column(String(20), nullable=True)
    
    category = Column(String(50), nullable=True)
    location = Column(String(100), nullable=True)  # 书架位置
    cover_url = Column(String(500), nullable=True)
    
    total_copies = Column(Integer, default=1)
    available_copies = Column(Integer, default=1)
    
    price = Column(String(20), nullable=True)
    pages = Column(Integer, nullable=True)
    
    status = Column(String(20), default="active")  # active/lost/dindon
    description = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_book_title", "title"),
        Index("idx_book_author", "author"),
        Index("idx_book_category", "category"),
    )


class BookBorrow(Base):
    """借阅记录"""
    __tablename__ = "book_borrows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    borrow_date = Column(DateTime, default=datetime.now)
    due_date = Column(DateTime, nullable=False)
    return_date = Column(DateTime, nullable=True)
    
    status = Column(String(20), default="borrowed")  # borrowed/returned/overdue
    renew_count = Column(Integer, default=0)
    
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_borrow_student", "student_id"),
        Index("idx_borrow_book", "book_id"),
        Index("idx_borrow_status", "status"),
    )


class BookReservation(Base):
    """图书预约"""
    __tablename__ = "book_reservations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    reserve_date = Column(DateTime, default=datetime.now)
    expire_date = Column(DateTime, nullable=True)
    pickup_date = Column(DateTime, nullable=True)
    
    status = Column(String(20), default="pending")  # pending/available/cancelled/expired
    remarks = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
