from fastapi import APIRouter
from app.api.v1.notice import notices

router = APIRouter()
router.include_router(notices.router, prefix="", tags=["通知公告"])
