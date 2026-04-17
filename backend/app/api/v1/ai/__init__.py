from fastapi import APIRouter
from app.api.v1.ai import chat, learning_records, teacher_assistant, learning_diagnosis, learning_agent

router = APIRouter()
router.include_router(chat.router, prefix="", tags=["AI智能助手"])
router.include_router(
    learning_records.router, prefix="/learning-records", tags=["学习记录"]
)
router.include_router(
    teacher_assistant.router, prefix="/teacher", tags=["教师助手"]
)
router.include_router(
    learning_diagnosis.router, prefix="/learning", tags=["学习诊断"]
)
router.include_router(
    learning_agent.router, prefix="/learning", tags=["学习助手"]
)
