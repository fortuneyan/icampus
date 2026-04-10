from fastapi import APIRouter
from app.api.v1.ai import chat, learning_records

router = APIRouter()
router.include_router(chat.router, prefix="", tags=["AI智能助手"])
router.include_router(
    learning_records.router, prefix="/learning-records", tags=["学习记录"]
)
