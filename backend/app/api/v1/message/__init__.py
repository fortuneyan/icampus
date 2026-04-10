from fastapi import APIRouter
from app.api.v1.message import messages, subscriptions

router = APIRouter()
router.include_router(messages.router, prefix="", tags=["消息中心"])
router.include_router(subscriptions.router, prefix="/subscriptions", tags=["消息订阅"])
