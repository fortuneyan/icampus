"""检查数据库表"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from sqlalchemy import inspect

async def check():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    async with engine.connect() as conn:
        def get_tables(sync_conn):
            inspector = inspect(sync_conn)
            return inspector.get_table_names()
        
        tables = await conn.run_sync(get_tables)
        print(f'数据库中的表: {tables}')
        
        if 'attendance_records' in tables:
            print('attendance_records 表存在')
        else:
            print('attendance_records 表不存在')
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
