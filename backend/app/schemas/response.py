"""
统一响应格式
"""

from datetime import datetime
from typing import Any, List
from pydantic import BaseModel, Field


class ResponseModel(BaseModel):
    """基础响应"""

    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="消息")
    data: Any = Field(default=None, description="数据")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class PageResult(BaseModel):
    """分页结果"""

    items: List[Any] = Field(default=[], description="数据列表")
    total: int = Field(default=0, description="总条数")
    page: int = Field(default=1, description="当前页")
    page_size: int = Field(default=20, description="每页条数")
    total_pages: int = Field(default=0, description="总页数")


def success(data: Any = None, message: str = "success") -> dict:
    """成功响应"""
    return {
        "code": 200,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat(),
    }


def error(code: int = 400, message: str = "error", errors: list = None) -> dict:
    """错误响应"""
    return {
        "code": code,
        "message": message,
        "errors": errors or [],
        "timestamp": datetime.now().isoformat(),
    }


def page_response(items: list, total: int, page: int, page_size: int) -> dict:
    """分页响应"""
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        },
        "timestamp": datetime.now().isoformat(),
    }
