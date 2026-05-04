from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class GenderType(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    phone = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=False)
    real_name = Column(String(100), nullable=True)
    avatar = Column(String(500), nullable=True)

    department_id = Column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True
    )
    position = Column(String(100), nullable=True)
    gender = Column(String(10), nullable=True)
    birth_date = Column(DateTime, nullable=True)
    address = Column(String(255), nullable=True)
    nation = Column(String(50), nullable=True)
    id_card = Column(String(18), nullable=True)

    status = Column(String(20), default="active")
    last_login = Column(DateTime, nullable=True)
    login_ip = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    deleted_at = Column(DateTime, nullable=True)

    department = relationship(
        "Department", back_populates="users", foreign_keys=[department_id]
    )

    # 用户-角色关联
    user_role_assocs = relationship(
        "UserRole", back_populates="user", cascade="all, delete-orphan"
    )
