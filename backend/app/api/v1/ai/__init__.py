from fastapi import APIRouter
from app.api.v1.ai import chat

router = APIRouter()
router.include_router(chat.router, prefix="", tags=["AI智能助手"])
