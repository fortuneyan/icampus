from datetime import datetime, time
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, Time, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

# 从 attendance_rule 导入完整版 AttendanceRule，避免表重复定义
from app.models.attendance_rule import AttendanceRule  # noqa: F401


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    rule_id = Column(
        UUID(as_uuid=True), ForeignKey("attendance_rules.id"), nullable=True
    )
    check_in_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)
    check_in_photo = Column(String(500), nullable=True)
    check_in_location = Column(String(200), nullable=True)
    status = Column(String(20), default="normal")
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
