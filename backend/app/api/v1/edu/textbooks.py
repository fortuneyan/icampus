"""
教材管理 API 接口

提供教材 CRUD、库存管理、教材选用等功能
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.textbook import Textbook, TextbookAdoption, TextbookStatus, TextbookLevel
from app.schemas.response import success, error, page_response

router = APIRouter()


# ==================== 教材 CRUD ====================

@router.get("/textbooks", summary="获取教材列表")
async def list_textbooks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    subject: Optional[str] = Query(None, description="学科筛选"),
    grade_level: Optional[str] = Query(None, description="年级筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取教材列表

    - **page**: 页码
    - **page_size**: 每页数量
    - **keyword**: 关键词搜索（教材名称、ISBN、作者）
    - **subject**: 学科筛选
    - **grade_level**: 年级筛选
    - **status**: 状态筛选
    """
    query = select(Textbook).where(Textbook.is_deleted == False)

    if keyword:
        query = query.where(
            (Textbook.title.contains(keyword)) |
            (Textbook.isbn.contains(keyword)) |
            (Textbook.author.contains(keyword))
        )
    if subject:
        query = query.where(Textbook.subject == subject)
    if grade_level:
        query = query.where(Textbook.grade_level == grade_level)
    if status:
        query = query.where(Textbook.status == status)

    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页
    query = query.order_by(Textbook.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    textbooks = result.scalars().all()

    return page_response(
        [t.to_dict() for t in textbooks],
        total,
        page,
        page_size,
    )


@router.get("/textbooks/{textbook_id}", summary="获取教材详情")
async def get_textbook(
    textbook_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教材详情"""
    result = await db.execute(
        select(Textbook).where(
            Textbook.id == textbook_id,
            Textbook.is_deleted == False,
        )
    )
    textbook = result.scalar_one_or_none()
    if not textbook:
        raise HTTPException(status_code=404, detail="教材不存在")
    return success(textbook.to_dict())


@router.post("/textbooks", summary="创建教材")
async def create_textbook(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建教材

    必填字段：
    - **isbn**: ISBN编号
    - **title**: 教材名称
    """
    if not data.get("isbn"):
        raise HTTPException(status_code=400, detail="ISBN编号不能为空")
    if not data.get("title"):
        raise HTTPException(status_code=400, detail="教材名称不能为空")

    # 检查ISBN是否已存在
    existing = await db.execute(
        select(Textbook).where(Textbook.isbn == data["isbn"])
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该ISBN已存在")

    textbook = Textbook(**data)
    db.add(textbook)
    await db.commit()
    await db.refresh(textbook)
    return success(textbook.to_dict(), "创建成功")


@router.put("/textbooks/{textbook_id}", summary="更新教材")
async def update_textbook(
    textbook_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新教材

    可更新字段：title, subtitle, author, publisher, subject, grade_level,
    semester, edition, price, cost_price, stock_quantity, min_stock,
    reorder_point, description, cover_image, page_count, status
    """
    result = await db.execute(
        select(Textbook).where(
            Textbook.id == textbook_id,
            Textbook.is_deleted == False,
        )
    )
    textbook = result.scalar_one_or_none()
    if not textbook:
        raise HTTPException(status_code=404, detail="教材不存在")

    for key, value in data.items():
        if hasattr(textbook, key):
            setattr(textbook, key, value)

    await db.commit()
    await db.refresh(textbook)
    return success(textbook.to_dict(), "更新成功")


@router.delete("/textbooks/{textbook_id}", summary="删除教材")
async def delete_textbook(
    textbook_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除教材（软删除）"""
    result = await db.execute(
        select(Textbook).where(Textbook.id == textbook_id)
    )
    textbook = result.scalar_one_or_none()
    if not textbook:
        raise HTTPException(status_code=404, detail="教材不存在")

    textbook.soft_delete()
    await db.commit()
    return success(None, "删除成功")


# ==================== 库存管理 ====================

@router.post("/textbooks/{textbook_id}/stock", summary="更新库存")
async def update_stock(
    textbook_id: int,
    quantity: int = Query(..., description="数量"),
    operation: str = Query("add", description="操作类型: add/subtract/set"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新库存

    - **quantity**: 数量
    - **operation**: 操作类型（add=增加, subtract=减少, set=设置）
    """
    result = await db.execute(
        select(Textbook).where(
            Textbook.id == textbook_id,
            Textbook.is_deleted == False,
        )
    )
    textbook = result.scalar_one_or_none()
    if not textbook:
        raise HTTPException(status_code=404, detail="教材不存在")

    if operation == "add":
        textbook.stock_quantity += quantity
    elif operation == "subtract":
        if textbook.stock_quantity < quantity:
            raise HTTPException(status_code=400, detail="库存不足")
        textbook.stock_quantity -= quantity
    elif operation == "set":
        textbook.stock_quantity = quantity
    else:
        raise HTTPException(status_code=400, detail="无效的操作类型")

    await db.commit()
    await db.refresh(textbook)
    return success(textbook.to_dict(), "库存更新成功")


# ==================== 教材选用 ====================

@router.get("/adoptions", summary="获取教材选用列表")
async def list_adoptions(
    grade_level: Optional[str] = Query(None),
    semester: Optional[str] = Query(None),
    school_year: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教材选用列表"""
    query = select(TextbookAdoption)

    if grade_level:
        query = query.where(TextbookAdoption.grade_level == grade_level)
    if semester:
        query = query.where(TextbookAdoption.semester == semester)
    if school_year:
        query = query.where(TextbookAdoption.school_year == school_year)

    result = await db.execute(query)
    adoptions = result.scalars().all()
    return success([a.to_dict() for a in adoptions])


@router.post("/adoptions", summary="创建教材选用记录")
async def create_adoption(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建教材选用记录

    必填字段：
    - **textbook_id**: 教材ID
    - **grade_level**: 年级
    - **semester**: 学期
    - **school_year**: 学年
    """
    # 验证教材是否存在
    tb_result = await db.execute(
        select(Textbook).where(
            Textbook.id == data.get("textbook_id"),
            Textbook.is_deleted == False,
        )
    )
    if not tb_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="教材不存在")

    adoption = TextbookAdoption(**data)
    db.add(adoption)
    await db.commit()
    await db.refresh(adoption)
    return success(adoption.to_dict(), "选用记录创建成功")


@router.put("/adoptions/{adoption_id}/approve", summary="审批教材选用")
async def approve_adoption(
    adoption_id: int,
    approved_by: str = Query(..., description="审批人"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """审批教材选用"""
    result = await db.execute(
        select(TextbookAdoption).where(TextbookAdoption.id == adoption_id)
    )
    adoption = result.scalar_one_or_none()
    if not adoption:
        raise HTTPException(status_code=404, detail="选用记录不存在")

    adoption.approved_by = approved_by
    adoption.approved_at = datetime.now().date()
    await db.commit()
    await db.refresh(adoption)
    return success(adoption.to_dict(), "审批成功")


# ==================== 统计分析 ====================

@router.get("/statistics/subjects", summary="各学科教材统计")
async def get_subject_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取各学科教材统计"""
    result = await db.execute(
        select(Textbook).where(Textbook.is_deleted == False)
    )
    textbooks = result.scalars().all()

    stats = {}
    for t in textbooks:
        subject = t.subject or "未分类"
        if subject not in stats:
            stats[subject] = {"count": 0, "total_stock": 0, "total_value": 0}
        stats[subject]["count"] += 1
        stats[subject]["total_stock"] += t.stock_quantity
        stats[subject]["total_value"] += t.stock_quantity * t.cost_price

    return success(stats)


@router.get("/statistics/low-stock", summary="低库存教材")
async def get_low_stock_textbooks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取低库存教材"""
    result = await db.execute(
        select(Textbook).where(
            Textbook.is_deleted == False,
            Textbook.stock_quantity <= Textbook.min_stock,
        )
    )
    textbooks = result.scalars().all()
    return success([t.to_dict() for t in textbooks])
