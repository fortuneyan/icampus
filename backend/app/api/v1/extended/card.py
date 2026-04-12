"""
一卡通管理接口
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
from app.models.card import CampusCard, CardTransaction, AccessRecord
from app.schemas.response import success, page_response

router = APIRouter()


# ==================== 校园卡管理 ====================

class CardCreate(BaseModel):
    card_no: str
    student_id: Optional[UUID] = None
    card_type: str = "student"
    initial_balance: int = 0


@router.get("/cards", response_model=dict)
async def get_cards(
    keyword: Optional[str] = Query(None),
    card_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取校园卡列表"""
    query = select(CampusCard).order_by(desc(CampusCard.created_at))
    
    if keyword:
        query = query.where(CampusCard.card_no.ilike(f"%{keyword}%"))
    if card_type:
        query = query.where(CampusCard.card_type == card_type)
    if status:
        query = query.where(CampusCard.status == status)
    
    total_result = await db.execute(query)
    total = len(total_result.scalars().all())
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return page_response([
        {
            "id": str(c.id),
            "card_no": c.card_no,
            "student_id": str(c.student_id) if c.student_id else None,
            "card_type": c.card_type,
            "balance": c.balance / 100.0,  # 转换为元
            "status": c.status,
            "issue_date": c.issue_date.isoformat() if c.issue_date else None,
        }
        for c in items
    ], total, page, page_size)


@router.post("/cards", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_card(
    data: CardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建校园卡"""
    card = CampusCard(
        balance=data.initial_balance * 100,  # 转换为分
        **data.model_dump(exclude={"initial_balance"})
    )
    db.add(card)
    await db.commit()
    await db.refresh(card)
    return success({"id": str(card.id)}, "创建成功")


# ==================== 交易记录 ====================

class TransactionCreate(BaseModel):
    card_id: UUID
    transaction_type: str  # consume/recharge
    amount: float  # 元


@router.get("/transactions", response_model=dict)
async def get_transactions(
    card_id: Optional[UUID] = Query(None),
    transaction_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取交易记录"""
    query = select(CardTransaction).order_by(desc(CardTransaction.created_at))
    
    if card_id:
        query = query.where(CardTransaction.card_id == card_id)
    if transaction_type:
        query = query.where(CardTransaction.transaction_type == transaction_type)
    
    total_result = await db.execute(query)
    total = len(total_result.scalars().all())
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return page_response([
        {
            "id": str(t.id),
            "card_id": str(t.card_id),
            "transaction_type": t.transaction_type,
            "amount": t.amount / 100.0,
            "balance_after": t.balance_after / 100.0 if t.balance_after else 0,
            "merchant_name": t.merchant_name,
            "location": t.location,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in items
    ], total, page, page_size)


@router.post("/transactions/recharge", response_model=dict, status_code=status.HTTP_201_CREATED)
async def recharge_card(
    data: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """校园卡充值"""
    card_result = await db.execute(select(CampusCard).where(CampusCard.id == data.card_id))
    card = card_result.scalar_one_or_none()
    
    if not card:
        return success(message="校园卡不存在")
    
    amount_cents = int(data.amount * 100)
    card.balance += amount_cents
    
    transaction = CardTransaction(
        card_id=data.card_id,
        transaction_type="recharge",
        amount=amount_cents,
        balance_before=card.balance - amount_cents,
        balance_after=card.balance,
        merchant_name="校园卡充值",
        remarks=f"用户{current_user.username}充值"
    )
    db.add(transaction)
    await db.commit()
    
    return success({"balance": card.balance / 100.0}, "充值成功")


# ==================== 门禁记录 ====================

@router.get("/access-records", response_model=dict)
async def get_access_records(
    card_id: Optional[UUID] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取门禁记录"""
    query = select(AccessRecord).order_by(desc(AccessRecord.created_at))
    
    if card_id:
        query = query.where(AccessRecord.card_id == card_id)
    
    total_result = await db.execute(query)
    total = len(total_result.scalars().all())
    
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return page_response([
        {
            "id": str(a.id),
            "card_id": str(a.card_id),
            "door_name": a.door_name,
            "location": a.location,
            "access_type": a.access_type,
            "access_result": a.access_result,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in items
    ], total, page, page_size)
