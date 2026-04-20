from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.models.notification_read import NotificationRead
from app.models.user import User
from app.models.student import Student
from app.models.class_model import Class
from app.services.base_service import BaseService


class NotificationService(BaseService[Notification]):
    def __init__(self, db: AsyncSession):
        super().__init__(Notification, db)

    async def create_notification(self, data: dict, sender_id: UUID) -> Notification:
        data["sender_id"] = sender_id
        data["status"] = "draft"
        return await self.create(data)

    async def send_notification(self, notification_id: UUID) -> Optional[Notification]:
        notification = await self.get(notification_id)
        if notification:
            notification.status = "published"
            notification.published_at = datetime.now()
            await self.db.commit()
            await self.db.refresh(notification)
            
            await self._create_read_records(notification)
        return notification

    async def _create_read_records(self, notification: Notification):
        user_ids = []
        
        if notification.scope_type == "all":
            result = await self.db.execute(select(User.id))
            user_ids = [r[0] for r in result.all()]
            
            result = await self.db.execute(select(Student.id))
            student_ids = [r[0] for r in result.all()]
            user_ids.extend(student_ids)
            
        elif notification.scope_type == "grade":
            if notification.scope_ids:
                for grade_id in notification.scope_ids:
                    result = await self.db.execute(
                        select(Student.id).where(Student.grade_id == UUID(grade_id))
                    )
                    user_ids.extend([r[0] for r in result.all()])
                    
        elif notification.scope_type == "class":
            if notification.scope_ids:
                for class_id in notification.scope_ids:
                    result = await self.db.execute(
                        select(Student.id).where(Student.class_id == UUID(class_id))
                    )
                    user_ids.extend([r[0] for r in result.all()])
                    
        elif notification.scope_type == "individual":
            if notification.scope_ids:
                user_ids = [UUID(uid) for uid in notification.scope_ids]

        for user_id in set(user_ids):
            read_record = NotificationRead(
                notification_id=notification.id,
                user_id=user_id
            )
            self.db.add(read_record)
        
        await self.db.commit()

    async def get_user_notifications(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        include_read: bool = True
    ) -> dict:
        query = (
            select(Notification)
            .where(Notification.status == "published")
            .order_by(Notification.created_at.desc())
        )
        
        result = await self.db.execute(query)
        notifications = result.scalars().all()
        
        total = len(notifications)
        offset = (page - 1) * page_size
        items = notifications[offset:offset + page_size]
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def mark_as_read(self, notification_id: UUID, user_id: UUID) -> bool:
        result = await self.db.execute(
            select(NotificationRead).where(
                and_(
                    NotificationRead.notification_id == notification_id,
                    NotificationRead.user_id == user_id
                )
            )
        )
        read_record = result.scalar_one_or_none()
        
        if read_record:
            read_record.read_at = datetime.now()
            await self.db.commit()
            return True
        return False

    async def get_read_status(self, notification_id: UUID) -> List[dict]:
        result = await self.db.execute(
            select(NotificationRead).where(
                NotificationRead.notification_id == notification_id
            )
        )
        reads = result.scalars().all()
        
        return [
            {
                "user_id": str(r.user_id),
                "read_at": r.read_at.isoformat() if r.read_at else None
            }
            for r in reads
        ]