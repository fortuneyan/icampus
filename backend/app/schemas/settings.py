"""
设置相关 Schemas
"""

from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class SettingUpdate(BaseModel):
    setting_key: str
    setting_value: Any
    value_type: str = "string"


class SettingResponse(BaseModel):
    setting_key: str
    setting_value: Any
    value_type: str
    description: Optional[str] = None


class SystemInfo(BaseModel):
    app_version: str
    python_version: str
    database_type: str
    os_type: str
    server_time: str


class LogQuery(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    level: Optional[str] = None
    keyword: Optional[str] = None
    page: int = 1
    page_size: int = 20


class LogEntry(BaseModel):
    id: str
    level: str
    message: str
    created_at: str
