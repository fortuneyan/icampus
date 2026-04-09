from fastapi import APIRouter
from app.api.v1.settings import config

router = APIRouter()
router.include_router(config.router, prefix="", tags=["系统设置"])
