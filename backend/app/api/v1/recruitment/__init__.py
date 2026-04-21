from fastapi import APIRouter
from app.api.v1.recruitment import recruitment

router = APIRouter()
router.include_router(recruitment.router, prefix="", tags=["招生管理"])