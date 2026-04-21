from fastapi import APIRouter
from app.api.v1 import notification

router = APIRouter()
router.include_router(notification.router, prefix="", tags=["家校联系"])