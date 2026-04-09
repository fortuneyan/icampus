from fastapi import APIRouter
from app.api.v1.attendance import check

router = APIRouter()
router.include_router(check.router, prefix="", tags=["考勤管理"])
