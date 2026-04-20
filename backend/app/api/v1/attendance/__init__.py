from fastapi import APIRouter
from app.api.v1.attendance import check, leaves

router = APIRouter()
router.include_router(check.router, prefix="", tags=["考勤管理"])
router.include_router(leaves.router, prefix="/leaves", tags=["请假管理"])
