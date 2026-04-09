from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.system import router as system_router
from app.api.v1.edu import router as edu_router
from app.api.v1.resource import router as resource_router
from app.api.v1.ai import router as ai_router
from app.api.v1.exam import router as exam_router
from app.api.v1.attendance import router as attendance_router
from app.api.v1.notice import router as notice_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.report import router as report_router
from app.api.v1.settings import router as settings_router
from app.api.v1.message import router as message_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(system_router, prefix="/system", tags=["系统管理"])
api_router.include_router(edu_router, prefix="/edu", tags=["教务管理"])
api_router.include_router(resource_router, prefix="/resource", tags=["教学资源"])
api_router.include_router(ai_router, prefix="/ai", tags=["AI智能助手"])
api_router.include_router(exam_router, prefix="/exam", tags=["考试管理"])
api_router.include_router(attendance_router, prefix="/attendance", tags=["考勤管理"])
api_router.include_router(notice_router, prefix="/notice", tags=["通知公告"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["仪表盘"])
api_router.include_router(report_router, prefix="/report", tags=["报表管理"])
api_router.include_router(settings_router, prefix="/settings", tags=["系统设置"])
api_router.include_router(message_router, prefix="/message", tags=["消息中心"])
