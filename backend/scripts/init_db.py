"""
数据库初始化脚本
"""

import asyncio
from uuid import uuid4
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base
from app.core.security import get_password_hash
from app.core.logger import app_logger
from app.models.user import User
from app.models.role import Role, Permission


"""
数据库初始化脚本
"""

import asyncio
from uuid import uuid4
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base
from app.core.security import get_password_hash
from app.core.logger import app_logger
from app.models.user import User
from app.models.role import Role, Permission


def create_database_sync():
    """同步创建数据库和扩展"""
    if settings.DATABASE_URL.startswith("sqlite"):
        app_logger.info("SQLite 数据库，无需创建")
        return

    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

    conn = psycopg2.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        dbname="postgres",
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    cursor.execute(
        f"SELECT 1 FROM pg_database WHERE datname = '{settings.POSTGRES_DB}'"
    )
    if not cursor.fetchone():
        cursor.execute(f"CREATE DATABASE {settings.POSTGRES_DB}")
        app_logger.info(f"数据库 {settings.POSTGRES_DB} 创建成功")

    cursor.close()
    conn.close()

    conn2 = psycopg2.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        dbname=settings.POSTGRES_DB,
    )
    conn2.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor2 = conn2.cursor()
    cursor2.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    cursor2.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    cursor2.close()
    conn2.close()


async def create_database():
    """创建数据库和扩展"""
    if settings.DATABASE_URL.startswith("sqlite"):
        app_logger.info("SQLite 数据库，无需创建")
        return
    create_database_sync()


async def create_tables():
    """创建所有表"""
    if settings.DATABASE_URL.startswith("sqlite"):
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        engine = create_async_engine(settings.DATABASE_URL, echo=settings.DATABASE_ECHO)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
    app_logger.info("数据库表创建成功")


async def init_default_data():
    """初始化默认数据"""
    if settings.DATABASE_URL.startswith("sqlite"):
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async_session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_factory() as session:
        try:
            result = await session.execute(text("SELECT COUNT(*) FROM users"))
        except Exception:
            app_logger.info("数据库表不存在，需要先创建表")
            await engine.dispose()
            return

        if result.scalar() > 0:
            app_logger.info("数据库已有数据，跳过初始化")
            await engine.dispose()
            return

        admin_role = Role(
            id=uuid4(),
            code="admin",
            name="系统管理员",
            description="系统最高权限管理员",
            level=99,
            status="active",
        )

        teacher_role = Role(
            id=uuid4(),
            code="teacher",
            name="教师",
            description="教师角色",
            level=10,
            status="active",
        )

        student_role = Role(
            id=uuid4(),
            code="student",
            name="学生",
            description="学生角色",
            level=1,
            status="active",
        )

        session.add_all([admin_role, teacher_role, student_role])

        admin_user = User(
            id=uuid4(),
            username="admin",
            email="admin@smartcampus.edu",
            password_hash=get_password_hash("admin123"),
            real_name="系统管理员",
            status="active",
        )

        session.add(admin_user)

        await session.commit()
        app_logger.info("默认数据初始化成功")

    await engine.dispose()


async def init_db():
    """初始化数据库"""
    app_logger.info("开始初始化数据库...")

    try:
        await create_database()
        await create_tables()
        await init_default_data()
        app_logger.info("数据库初始化完成!")
    except Exception as e:
        app_logger.error(f"数据库初始化失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(init_db())
