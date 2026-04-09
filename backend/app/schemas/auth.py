from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: str
    exp: int
    type: str


class UserInfo(BaseModel):
    id: str
    username: str
    email: Optional[EmailStr] = None
    real_name: Optional[str] = None
    avatar: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class RefreshTokenRequest(BaseModel):
    refresh_token: str
