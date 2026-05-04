"""
API 通用工具函数
"""

from typing import Any, Optional, List
from fastapi.responses import JSONResponse
from fastapi import Response


def success(
    data: Any = None,
    message: str = "操作成功",
    code: int = 200
) -> dict:
    """
    通用成功响应

    Args:
        data: 返回数据
        message: 成功消息
        code: 状态码

    Returns:
        dict: 响应字典
    """
    return {
        "code": code,
        "message": message,
        "data": data
    }


def error(
    message: str = "操作失败",
    code: int = 400,
    data: Any = None
) -> dict:
    """
    通用错误响应

    Args:
        message: 错误消息
        code: 状态码
        data: 附加数据

    Returns:
        dict: 响应字典
    """
    return {
        "code": code,
        "message": message,
        "data": data
    }


def page_response(
    items: List[Any],
    total: int,
    page: int = 1,
    page_size: int = 20,
    message: str = "查询成功"
) -> dict:
    """
    分页响应

    Args:
        items: 数据列表
        total: 总数
        page: 当前页
        page_size: 每页数量
        message: 消息

    Returns:
        dict: 响应字典
    """
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return {
        "code": 200,
        "message": message,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    }
