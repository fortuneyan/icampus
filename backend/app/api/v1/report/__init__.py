from fastapi import APIRouter
from app.api.v1.report import student_report

router = APIRouter()
router.include_router(student_report.router, prefix="", tags=["报表管理"])
