"""
通知服务
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notice import Notice, NoticeRead
from app.core.exceptions import NotFoundException
from app.services.base_service import BaseService


class NoticeService(BaseService[Notice]):
    """通知服务"""

    def __init__(self, db: AsyncSession):
        super().__init__(Notice, db)

    async def create_notice(self, data: dict, publisher_id: UUID) -> Notice:
        data["publisher_id"] = publisher_id
        if data.get("status") == "published":
            data["published_at"] = datetime.now()
        return await self.create(data)

    async def publish_notice(self, notice_id: UUID) -> Notice:
        notice = await self.get(notice_id)
        if not notice:
            raise NotFoundException("通知不存在")
        notice.status = "published"
        notice.published_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(notice)
        return notice

    async def get_user_notices(
        self, user_id: UUID, page: int = 1, page_size: int = 20
    ) -> dict:
        filters = [Notice.status == "published"]

        query = (
            select(Notice)
            .where(and_(*filters))
            .order_by(Notice.priority.desc(), Notice.created_at.desc())
        )
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        notices = list(result.scalars().all())

        count_result = await self.db.execute(
            select(func.count()).select_from(Notice).where(and_(*filters))
        )
        total = count_result.scalar()

        return {"items": notices, "total": total, "page": page, "page_size": page_size}

    async def get_unread_count(self, user_id: UUID) -> int:
        subquery = select(NoticeRead.user_id).where(NoticeRead.user_id == user_id)
        result = await self.db.execute(
            select(func.count())
            .select_from(Notice)
            .where(
                Notice.status == "published",
                Notice.id.not_in(
                    select(NoticeRead.notice_id).where(NoticeRead.user_id == user_id)
                ),
            )
        )
        return result.scalar() or 0

    async def mark_as_read(self, notice_id: UUID, user_id: UUID) -> bool:
        result = await self.db.execute(
            select(NoticeRead).where(
                NoticeRead.notice_id == notice_id, NoticeRead.user_id == user_id
            )
        )
        existing = result.scalar_one_or_none()

        if not existing:
            notice_read = NoticeRead(
                notice_id=notice_id, user_id=user_id, read_at=datetime.now()
            )
            self.db.add(notice_read)
            await self.db.commit()
            return True
        return False
