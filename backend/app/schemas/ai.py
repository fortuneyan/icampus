"""
AI 相关 Schemas
"""

from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: Optional[UUID] = None
    message: str = Field(..., max_length=4000)
    model_type: str = "deepseek"


class ChatResponse(BaseModel):
    session_id: UUID
    message: str
    created_at: str


class SessionCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    model_type: str = "deepseek"


class SessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: Optional[str] = None
    model_type: str
    status: str
    created_at: str


class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    created_at: str


class AIConfigUpdate(BaseModel):
    model_type: str
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    temperature: int = Field(80, ge=0, le=100)
    max_tokens: int = Field(2000, ge=100, le=4000)
    status: str = "active"
