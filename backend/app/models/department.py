from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=True)
    sort_order = Column(Integer, default=0)
    leader_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    status = Column(String(20), default="active")
    description = Column(Text, nullable=True)
    path = Column(String(500), nullable=True)
    level = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    parent = relationship("Department", remote_side=[id], backref="children")
    users = relationship(
        "User", back_populates="department", foreign_keys="User.department_id"
    )
