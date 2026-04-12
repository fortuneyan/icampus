import asyncio
from app.core.database import engine
from sqlalchemy import text

async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text(
            "SELECT column_name, character_maximum_length, data_type "
            "FROM information_schema.columns "
            "WHERE table_name = 'students' AND character_maximum_length IS NOT NULL "
            "ORDER BY ordinal_position"
        ))
        for row in result:
            print(row)

asyncio.run(check())
