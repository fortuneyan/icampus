"""
手动创建排课模块数据库表（使用 ORM create_all）
直接执行: python migrations/create_scheduling_tables.py
"""
import asyncio
import sys
from pathlib import Path

# 添加 backend 到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

from app.core.database import Base, get_async_session_maker
from app.core.config import settings


async def get_engine() -> AsyncEngine:
    url = settings.DATABASE_URL
    # 同步 URL 转异步 (sqlite:/// -> sqlite+aiosqlite:///)
    if url.startswith("sqlite:///"):
        url = url.replace("sqlite:///", "sqlite+aiosqlite:///")
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://")
    print(f"Database URL: {url}")
    return create_async_engine(url, echo=True)


async def check_table_exists(engine: AsyncEngine, table_name: str) -> bool:
    async with engine.begin() as conn:
        result = await conn.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"))
        return result.fetchone() is not None


async def create_scheduling_tables():
    """创建排课模块的所有表"""
    engine = await get_engine()

    # 导入所有模型，触发 Base.metadata 注册
    from app.models.scheduling_models import (
        SchCycle, SchSemester, SchCalendarMap, SchTemplate, SchPeriod,
        SchPlan, SchResult, SchPatch, SchConstraint, SchEvent,
        SchPlanTeacherReplace,
    )
    from app.models.schedule import Schedule, Classroom

    print("\n=== 排课模块表列表 ===")
    for table_name, table in sorted(Base.metadata.tables.items()):
        if table_name.startswith("sch_") or table_name in ("schedules", "classrooms"):
            print(f"  - {table_name}")

    print("\n=== 检查现有表 ===")
    existing = []
    missing = []
    for table_name in Base.metadata.tables:
        if table_name.startswith("sch_") or table_name in ("schedules", "classrooms"):
            if await check_table_exists(engine, table_name):
                existing.append(table_name)
            else:
                missing.append(table_name)

    print(f"  已存在: {existing}")
    print(f"  缺失（待创建）: {missing}")

    if missing:
        print("\n=== 创建缺失的表 ===")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("  ✅ 表创建完成")
    else:
        print("\n  ✅ 所有表已存在，无需创建")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_scheduling_tables())
