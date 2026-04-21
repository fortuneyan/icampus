from fastapi import APIRouter
from app.api.v1.recruitment import recruitment, enrollment

router = APIRouter()
router.include_router(recruitment.router, prefix="", tags=["招生管理"])
router.include_router(enrollment.router, prefix="", tags=["学籍管理"])