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

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import api_router, ai_api_router

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("Starting Smart Campus Platform...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")
    yield
    # 关闭时
    logger.info("Shutting down Smart Campus Platform...")
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
