from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    level = Column(Integer, default=1)
    data_scope = Column(String(50), default="all")
    dept_ids = Column(JSON, nullable=True)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 用户-角色关联
    user_role_assocs = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    resource = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id"), nullable=True)
    sort_order = Column(Integer, default=0)
    icon = Column(String(50), nullable=True)
    visible = Column(Boolean, default=True)
    component = Column(String(255), nullable=True)
    route_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class Menu(Base):
    __tablename__ = "menus"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("menus.id"), nullable=True)
    name = Column(String(100), nullable=False)
    title = Column(String(100), nullable=False)
    icon = Column(String(50), nullable=True)
    path = Column(String(255), nullable=True)
    component = Column(String(255), nullable=True)
    sort_order = Column(Integer, default=0)
    visible = Column(Boolean, default=True)
    enabled = Column(Boolean, default=True)
    keep_alive = Column(Boolean, default=True)
    permission_code = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    parent = relationship("Menu", remote_side=[id], backref="children")


class UserRole(Base):
    """用户-角色中间表（多对多）"""
    __tablename__ = "user_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    user = relationship("User", back_populates="user_role_assocs")
    role = relationship("Role", back_populates="user_role_assocs")


# 已废弃的占位符（保留以防旧代码引用）
role_permissions = None
user_roles = None
