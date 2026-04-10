"""Debug script to check database connection"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.database import engine, is_sqlite
from sqlalchemy import text

print(f"Database URL: {settings.DATABASE_URL}")
print(f"Is SQLite: {is_sqlite}")
print(f"DB file exists: {os.path.exists('smart_campus.db')}")


async def check():
    from app.core.database import async_session_factory

    async with async_session_factory() as session:
        result = await session.execute(text("SELECT name FROM grades"))
        print(f"Grades: {[r[0] for r in result.fetchall()]}")


asyncio.run(check())
