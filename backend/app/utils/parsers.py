"""
通用类型转换工具
用于处理前端传入的各种数据类型
"""
from uuid import UUID
from datetime import datetime, date
from typing import Optional, Any, List, Union


def parse_uuid(value: Any) -> Optional[UUID]:
    """解析UUID，支持字符串、数组、UUID"""
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    if isinstance(value, list) and len(value) > 0:
        value = value[0]
    if isinstance(value, str) and value:
        try:
            return UUID(value)
        except ValueError:
            return None
    return None


def parse_uuid_list(value: Any) -> List[UUID]:
    """解析UUID列表"""
    if not value:
        return []
    if isinstance(value, list):
        return [parse_uuid(v) for v in value if parse_uuid(v)]
    return [parse_uuid(value)] if parse_uuid(value) else []


def parse_int(value: Any) -> Optional[int]:
    """解析整数，支持字符串、数字"""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value:
        try:
            return int(value)
        except ValueError:
            return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def parse_float(value: Any) -> Optional[float]:
    """解析浮点数"""
    if value is None:
        return None
    if isinstance(value, float):
        return value
    if isinstance(value, str) and value:
        try:
            return float(value)
        except ValueError:
            return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def parse_str(value: Any) -> Optional[str]:
    """解析字符串，支持数组取第一个元素"""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, list) and len(value) > 0:
        return str(value[0]) if value[0] else None
    return str(value) if value else None


def parse_str_list(value: Any) -> List[str]:
    """解析字符串列表"""
    if not value:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if v]
    return [str(value)] if value else []


def parse_datetime(value: Any) -> Optional[datetime]:
    """解析日期时间，处理时区，转换为不带时区的datetime"""
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            return value.replace(tzinfo=None)
        return value
    if isinstance(value, str) and value:
        try:
            # 处理 ISO 格式 (带时区)
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return dt.replace(tzinfo=None)
        except ValueError:
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return None
    return None


def parse_date(value: Any) -> Optional[date]:
    """解析日期"""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            return None
    return None


def parse_bool(value: Any) -> Optional[bool]:
    """解析布尔值"""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    return bool(value)
