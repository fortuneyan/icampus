"""
用户相关 Schemas
"""

from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


class UserCreate(BaseModel):
    """创建用户请求"""

    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    password: str = Field(..., min_length=6)
    real_name: Optional[str] = Field(None, max_length=100)
    department_id: Optional[UUID] = None
    position: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None, max_length=10)
    birth_date: Optional[date] = None
    address: Optional[str] = Field(None, max_length=255)
    status: str = "active"
    role_ids: Optional[List[UUID]] = None


class UserUpdate(BaseModel):
    """更新用户请求"""

    email: Optional[str] = None
    phone: Optional[str] = None
    real_name: Optional[str] = None
    department_id: Optional[UUID] = None
    position: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    address: Optional[str] = None
    status: Optional[str] = None
    role_ids: Optional[List[UUID]] = None


class UserPasswordReset(BaseModel):
    """重置密码请求"""

    password: str = Field(..., min_length=6)


class UserPasswordChange(BaseModel):
    """修改密码请求"""

    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)


class RoleSimple(BaseModel):
    """角色简要信息"""
    id: UUID
    code: str
    name: str


class UserResponse(BaseModel):
    """用户响应"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    real_name: Optional[str] = None
    avatar: Optional[str] = None
    department_id: Optional[UUID] = None
    position: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    address: Optional[str] = None
    status: str
    created_at: Optional[str] = None
    roles: List[RoleSimple] = []


class UserWithRoles(UserResponse):
    """带角色的用户响应（保持向后兼容）"""
    pass


class UserQuery(BaseModel):
    """用户查询参数"""

    username: Optional[str] = None
    real_name: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    department_id: Optional[UUID] = None


class UserOptions(BaseModel):
    """用户下拉选项"""

    id: UUID
    label: str
    value: UUID
