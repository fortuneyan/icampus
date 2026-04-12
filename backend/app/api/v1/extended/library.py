"""
图书管理接口
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.library import Book, BookBorrow, BookReservation
from app.schemas.response import success, page_response

router = APIRouter()


# ==================== 图书管理 ====================

class BookCreate(BaseModel):
    isbn: str
    title: str
    author: Optional[str] = None
    publisher: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    total_copies: int = 1
    price: Optional[str] = None
    pages: Optional[int] = None
    description: Optional[str] = None


@router.get("/books", response_model=dict)
async def get_books(
    keyword: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取图书列表"""
    query = select(Book).order_by(desc(Book.created_at))
    
    if keyword:
        query = query.where(Book.title.ilike(f"%{keyword}%") | Book.author.ilike(f"%{keyword}%"))
    if category:
        query = query.where(Book.category == category)
    if status:
        query = query.where(Book.status == status)
    
    total_result = await db.execute(query)
    total = len(total_result.scalars().all())
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return page_response([
        {
            "id": str(b.id),
            "isbn": b.isbn,
            "title": b.title,
            "author": b.author,
            "publisher": b.publisher,
            "category": b.category,
            "location": b.location,
            "total_copies": b.total_copies,
            "available_copies": b.available_copies,
            "status": b.status,
        }
        for b in items
    ], total, page, page_size)


@router.post("/books", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_book(
    data: BookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加图书"""
    book = Book(available_copies=data.total_copies, **data.model_dump())
    db.add(book)
    await db.commit()
    await db.refresh(book)
    return success({"id": str(book.id)}, "添加成功")


# ==================== 借阅管理 ====================

class BorrowCreate(BaseModel):
    book_id: UUID
    student_id: UUID
    due_date: str  # ISO日期字符串


@router.get("/borrows", response_model=dict)
async def get_borrows(
    student_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取借阅记录"""
    query = select(BookBorrow).order_by(desc(BookBorrow.created_at))
    
    if student_id:
        query = query.where(BookBorrow.student_id == student_id)
    if status:
        query = query.where(BookBorrow.status == status)
    
    total_result = await db.execute(query)
    total = len(total_result.scalars().all())
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return page_response([
        {
            "id": str(b.id),
            "book_id": str(b.book_id),
            "student_id": str(b.student_id),
            "borrow_date": b.borrow_date.isoformat() if b.borrow_date else None,
            "due_date": b.due_date.isoformat() if b.due_date else None,
            "return_date": b.return_date.isoformat() if b.return_date else None,
            "status": b.status,
        }
        for b in items
    ], total, page, page_size)


@router.post("/borrows", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_borrow(
    data: BorrowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建借阅"""
    from datetime import datetime
    borrow = BookBorrow(
        due_date=datetime.fromisoformat(data.due_date),
        **data.model_dump(exclude={"due_date"})
    )
    db.add(borrow)
    
    # 更新图书可借数量
    book_result = await db.execute(select(Book).where(Book.id == data.book_id))
    book = book_result.scalar_one_or_none()
    if book and book.available_copies > 0:
        book.available_copies -= 1
    
    await db.commit()
    await db.refresh(borrow)
    return success({"id": str(borrow.id)}, "借阅成功")


@router.post("/borrows/{borrow_id}/return", response_model=dict)
async def return_book(
    borrow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """归还图书"""
    result = await db.execute(select(BookBorrow).where(BookBorrow.id == borrow_id))
    borrow = result.scalar_one_or_none()
    
    if not borrow:
        return success(message="借阅记录不存在")
    
    borrow.status = "returned"
    borrow.return_date = datetime.utcnow()
    
    # 更新图书可借数量
    book_result = await db.execute(select(Book).where(Book.id == borrow.book_id))
    book = book_result.scalar_one_or_none()
    if book:
        book.available_copies += 1
    
    await db.commit()
    return success(message="归还成功")
