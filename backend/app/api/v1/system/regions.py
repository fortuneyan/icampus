"""
地区接口
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.region import Region
from app.schemas.response import success

router = APIRouter()


@router.get("", response_model=dict)
async def get_regions(
    level: Optional[int] = Query(None),
    parent_code: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取地区列表"""
    query = select(Region).where(Region.is_active == "true").order_by(Region.sort_order)

    if level is not None:
        query = query.where(Region.level == level)
    if parent_code:
        query = query.where(Region.parent_code == parent_code)

    result = await db.execute(query)
    regions = result.scalars().all()

    items = [
        {
            "id": str(r.id),
            "code": r.code,
            "name": r.name,
            "level": r.level,
            "parent_code": r.parent_code,
        }
        for r in regions
    ]

    return success(items)


@router.get("/provinces", response_model=dict)
async def get_provinces(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取省份列表"""
    result = await db.execute(
        select(Region)
        .where(Region.level == 1, Region.is_active == "true")
        .order_by(Region.sort_order)
    )
    provinces = result.scalars().all()

    return success([{"code": p.code, "name": p.name} for p in provinces])


@router.get("/cities/{province_code}", response_model=dict)
async def get_cities(
    province_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取城市列表"""
    result = await db.execute(
        select(Region)
        .where(
            Region.level == 2,
            Region.parent_code == province_code,
            Region.is_active == "true",
        )
        .order_by(Region.sort_order)
    )
    cities = result.scalars().all()

    return success([{"code": c.code, "name": c.name} for c in cities])


@router.get("/districts/{city_code}", response_model=dict)
async def get_districts(
    city_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取区县列表"""
    result = await db.execute(
        select(Region)
        .where(
            Region.level == 3,
            Region.parent_code == city_code,
            Region.is_active == "true",
        )
        .order_by(Region.sort_order)
    )
    districts = result.scalars().all()

    return success([{"code": d.code, "name": d.name} for d in districts])
