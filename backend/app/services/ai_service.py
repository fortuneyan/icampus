"""
AI 服务
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_model import AISession, AIMessage, AIConfig
from app.core.exceptions import NotFoundException
from app.services.base_service import BaseService


class AIService:
    """AI服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self, user_id: UUID, title: Optional[str] = None, model_type: str = "deepseek"
    ) -> AISession:
        session = AISession(
            user_id=user_id, title=title or "新对话", model_type=model_type
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_user_sessions(self, user_id: UUID) -> List[AISession]:
        result = await self.db.execute(
            select(AISession)
            .where(AISession.user_id == user_id)
            .order_by(AISession.updated_at.desc())
        )
        return list(result.scalars().all())

    async def get_session_messages(self, session_id: UUID) -> List[AIMessage]:
        result = await self.db.execute(
            select(AIMessage)
            .where(AIMessage.session_id == session_id)
            .order_by(AIMessage.created_at)
        )
        return list(result.scalars().all())

    async def add_message(self, session_id: UUID, role: str, content: str) -> AIMessage:
        message = AIMessage(session_id=session_id, role=role, content=content)
        self.db.add(message)

        session = await self.db.get(AISession, session_id)
        if session:
            session.updated_at = datetime.now()

        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def delete_session(self, session_id: UUID) -> bool:
        session = await self.db.get(AISession, session_id)
        if session:
            await self.db.delete(session)
            await self.db.commit()
            return True
        return False

    async def get_config(self, model_type: str = "deepseek") -> Optional[AIConfig]:
        result = await self.db.execute(
            select(AIConfig).where(
                AIConfig.model_type == model_type, AIConfig.status == "active"
            )
        )
        return result.scalar_one_or_none()

    async def update_config(self, model_type: str, data: dict) -> AIConfig:
        config = await self.get_config(model_type)
        if config:
            for key, value in data.items():
                setattr(config, key, value)
        else:
            config = AIConfig(model_type=model_type, **data)
            self.db.add(config)

        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def chat(
        self,
        user_id: UUID,
        message: str,
        session_id: Optional[UUID] = None,
        model_type: str = "deepseek",
    ) -> dict:
        if not session_id:
            session = await self.create_session(user_id, model_type=model_type)
            session_id = session.id

        await self.add_message(session_id, "user", message)

        config = await self.get_config(model_type)
        response_content = f"AI回复: {message} (模拟响应 - 配置: {model_type})"

        await self.add_message(session_id, "assistant", response_content)

        return {
            "session_id": str(session_id),
            "message": response_content,
            "created_at": datetime.now().isoformat(),
        }
