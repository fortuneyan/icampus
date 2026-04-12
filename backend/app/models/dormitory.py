"""
宿舍管理模型
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Dormitory(Base):
    """宿舍楼栋"""
    __tablename__ = "dormitories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False)
    building_no = Column(String(50), nullable=False, index=True)
    floor_count = Column(Integer, default=1)
    building_type = Column(String(20), default="female")  # male/female
    status = Column(String(20), default="active")
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class DormitoryRoom(Base):
    """宿舍房间"""
    __tablename__ = "dormitory_rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    dormitory_id = Column(UUID(as_uuid=True), ForeignKey("dormitories.id", ondelete="CASCADE"), nullable=False)
    room_no = Column(String(50), nullable=False)
    floor = Column(Integer, nullable=False)
    bed_count = Column(Integer, default=4)
    occupied_beds = Column(Integer, default=0)
    room_type = Column(String(20), default="standard")  # standard/deluxe
    status = Column(String(20), default="available")  # available/occupied/maintenance
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_room_dorm", "dormitory_id"),
    )


class DormitoryAssignment(Base):
    """住宿分配"""
    __tablename__ = "dormitory_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    room_id = Column(UUID(as_uuid=True), ForeignKey("dormitory_rooms.id", ondelete="CASCADE"), nullable=False)
    bed_no = Column(Integer, nullable=False)
    academic_year = Column(String(20), nullable=False)
    semester = Column(String(20), nullable=False)
    check_in_date = Column(DateTime, nullable=True)
    check_out_date = Column(DateTime, nullable=True)
    status = Column(String(20), default="active")  # active/checkout
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class DormitoryAttendance(Base):
    """归寝记录"""
    __tablename__ = "dormitory_attendances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    room_id = Column(UUID(as_uuid=True), nullable=False)
    check_date = Column(DateTime, nullable=False)
    check_in_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)
    status = Column(String(20), default="normal")  # normal/late/absent
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index("idx_attendance_student_date", "student_id", "check_date"),
    )
