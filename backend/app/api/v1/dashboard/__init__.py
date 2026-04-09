from fastapi import APIRouter
from app.api.v1.dashboard import overview

router = APIRouter()
router.include_router(overview.router, prefix="", tags=["仪表盘"])
