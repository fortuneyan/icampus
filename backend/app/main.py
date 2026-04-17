"""
智慧校园管理平台 - 后端入口

路由结构说明：
  基础管理 API: /api/v1/{module}       (认证/系统/教务/考勤/考试等)
  AI 功能 API:  /api/v1/ai/{module}    (AI对话/学习诊断/教师助手/学习记录等)

通过 main.py 中的两个独立 include_router 调用，
使基础管理路由与 AI 功能路由在注册层面明确分离，便于独立维护和权限控制。
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine, Base, async_session_factory
from app.core.security import get_password_hash
from app.core.redis_client import get_redis_client, close_redis_connection
from app.core.rate_limiter import set_rate_limiter_redis
from app.middleware.rate_limit import RateLimitMiddleware
from app.api.v1 import api_router, ai_api_router

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def _init_seed_data():
    """初始化种子数据（仅在 users 表为空时执行）"""
    async with async_session_factory() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        if count > 0:
            logger.info("数据库已有用户数据，跳过种子初始化")
            return

        from uuid import uuid4
        from app.models.user import User

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
        logger.info("种子用户 admin/admin123 初始化成功")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("Starting Smart Campus Platform...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")

    # 初始化种子数据
    try:
        await _init_seed_data()
    except Exception as e:
        logger.warning(f"种子数据初始化失败（非致命）: {e}")

    # 初始化 Redis 连接
    try:
        redis_client = await get_redis_client()
        await redis_client.connect()
        logger.info("Redis connected successfully")
        # 为限流器注入 Redis 客户端
        set_rate_limiter_redis(redis_client)
        logger.info("Rate limiter connected to Redis")
    except Exception as e:
        logger.warning(f"Redis 连接失败（非致命，将使用内存降级）: {e}")

    yield
    # 关闭时
    logger.info("Shutting down Smart Campus Platform...")
    await close_redis_connection()
    logger.info("Redis connection closed")
    await engine.dispose()


# 创建应用
app = FastAPI(
    title="Smart Campus API",
    version="1.0.0",
    description="智慧校园管理平台API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册限流中间件（CORS 之后，后注册先执行：限流 → CORS）
app.add_middleware(RateLimitMiddleware)

# ==================== 路由注册 ====================

# 基础管理路由: /api/v1/{auth|system|edu|exam|attendance|...}
app.include_router(api_router, prefix="/api/v1")

# AI 功能路由: /api/v1/ai/{chat|learning|teacher|diagnosis|...}
# 独立注册，与基础管理路由在代码层面明确分离
app.include_router(ai_api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Welcome to Smart Campus API",
        "version": "1.0.0",
        "docs": "/docs",
        "routes": {
            "base_management": "/api/v1/{auth|system|edu|exam|attendance|...}",
            "ai_features": "/api/v1/ai/{chat|learning|teacher|diagnosis|...}",
        },
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG
    )
