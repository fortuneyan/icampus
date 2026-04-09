from fastapi import APIRouter
from app.api.v1.exam import exams

router = APIRouter()
router.include_router(exams.router, prefix="", tags=["考试管理"])
