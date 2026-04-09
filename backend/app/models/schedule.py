from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    room_id = Column(UUID(as_uuid=True), ForeignKey("classrooms.id"), nullable=True)
    weekday = Column(Integer, nullable=False)
    period_start = Column(Integer, nullable=False)
    period_end = Column(Integer, nullable=False)
    semester = Column(String(20), nullable=True)
    week_range = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Classroom(Base):
    __tablename__ = "classrooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    building = Column(String(50), nullable=True)
    room_no = Column(String(20), nullable=False)
    capacity = Column(Integer, nullable=True)
    room_type = Column(String(20), nullable=True)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.now)
