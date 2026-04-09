"""
AI智能助手接口
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.ai import ChatRequest, SessionCreate, AIConfigUpdate
from app.schemas.response import success
from app.services.ai_service import AIService

router = APIRouter()


@router.post("/chat", response_model=dict)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AIService(db)
    result = await service.chat(
        current_user.id, request.message, request.session_id, request.model_type
    )
    return success(result)


@router.get("/sessions", response_model=dict)
async def get_sessions(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    service = AIService(db)
    sessions = await service.get_user_sessions(current_user.id)
    items = [
        {
            "id": str(s.id),
            "title": s.title,
            "model_type": s.model_type,
            "updated_at": s.updated_at.isoformat(),
        }
        for s in sessions
    ]
    return success(items)


@router.post("/sessions", response_model=dict)
async def create_session(
    data: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AIService(db)
    session = await service.create_session(current_user.id, data.title, data.model_type)
    return success({"id": str(session.id)}, "创建成功")


@router.delete("/sessions/{id}", response_model=dict)
async def delete_session(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AIService(db)
    await service.delete_session(id)
    return success(message="删除成功")


@router.get("/sessions/{id}/messages", response_model=dict)
async def get_messages(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AIService(db)
    messages = await service.get_session_messages(id)
    items = [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]
    return success(items)


@router.get("/config", response_model=dict)
async def get_config(
    model_type: str = Query("deepseek"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AIService(db)
    config = await service.get_config(model_type)
    if config:
        return success(
            {
                "model_type": config.model_type,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                "status": config.status,
            }
        )
    return success(
        {
            "model_type": model_type,
            "temperature": 80,
            "max_tokens": 2000,
            "status": "active",
        }
    )


@router.put("/config", response_model=dict)
async def update_config(
    data: AIConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AIService(db)
    config = await service.update_config(data.model_type, data.model_dump())
    return success({"id": str(config.id)}, "配置更新成功")
