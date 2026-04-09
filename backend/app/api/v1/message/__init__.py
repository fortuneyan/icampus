from fastapi import APIRouter
from app.api.v1.message import messages

router = APIRouter()
router.include_router(messages.router, prefix="", tags=["消息中心"])
