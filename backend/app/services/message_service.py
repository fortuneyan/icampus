"""
消息服务
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dashboard import Message


class MessageService:
    """消息服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_message(
        self,
        user_id: UUID,
        title: str,
        content: Optional[str] = None,
        msg_type: str = "system",
        priority: int = 0,
    ) -> Message:
        """创建消息"""
        message = Message(
            user_id=user_id,
            title=title,
            content=content,
            msg_type=msg_type,
            priority=priority,
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_user_messages(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        is_read: Optional[bool] = None,
    ) -> dict:
        """获取用户消息"""
        filters = [Message.user_id == user_id]
        if is_read is not None:
            filters.append(Message.is_read == is_read)

        query = select(Message).where(*filters).order_by(Message.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        messages = list(result.scalars().all())

        count_result = await self.db.execute(
            select(func.count()).select_from(Message).where(*filters)
        )
        total = count_result.scalar()

        return {"items": messages, "total": total, "page": page, "page_size": page_size}

    async def get_unread_count(self, user_id: UUID) -> dict:
        """获取未读数量"""
        total_result = await self.db.execute(
            select(func.count())
            .select_from(Message)
            .where(Message.user_id == user_id, Message.is_read == False)
        )
        total = total_result.scalar() or 0

        return {"total": total, "system": total, "notice": 0, "task": 0}

    async def mark_as_read(self, message_id: UUID, user_id: UUID) -> bool:
        """标记已读"""
        result = await self.db.execute(
            select(Message).where(Message.id == message_id, Message.user_id == user_id)
        )
        message = result.scalar_one_or_none()

        if message:
            message.is_read = True
            message.read_at = datetime.now()
            await self.db.commit()
            return True
        return False

    async def mark_all_as_read(self, user_id: UUID) -> bool:
        """全部标记已读"""
        result = await self.db.execute(
            select(Message).where(Message.user_id == user_id, Message.is_read == False)
        )
        messages = list(result.scalars().all())

        for msg in messages:
            msg.is_read = True
            msg.read_at = datetime.now()

        await self.db.commit()
        return True

    async def delete_message(self, message_id: UUID, user_id: UUID) -> bool:
        """删除消息"""
        result = await self.db.execute(
            select(Message).where(Message.id == message_id, Message.user_id == user_id)
        )
        message = result.scalar_one_or_none()

        if message:
            await self.db.delete(message)
            await self.db.commit()
            return True
        return False
