from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class NotificationRead(Base):
    __tablename__ = "notification_reads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    notification_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    read_at = Column(DateTime, default=datetime.now)