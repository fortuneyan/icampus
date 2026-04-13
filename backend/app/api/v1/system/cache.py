"""
缓存监控 API - T13: 缓存监控
提供缓存统计、键列表查询、清理等功能
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.response import success, page_response


# ==================== Schema 定义 ====================

class CacheKeyType:
    """缓存键类型"""
    STRING = "string"
    HASH = "hash"
    LIST = "list"
    SET = "set"
    ZSET = "zset"


class CacheStats(BaseModel):
    total_keys: int
    hit_rate: float
    memory_usage: float  # MB
    memory_usage_bytes: int
    expired_keys: int
    evicted_keys: int
    connected_clients: int
    total_commands_processed: int
    uptime_seconds: int


class CacheKeyInfo(BaseModel):
    key: str
    type: str
    ttl: int  # 秒，-1表示永久
    size: int  # 字节
    access_count: int
    last_access: str
    created_at: str
    creator: Optional[str] = None


class CacheKeyValue(BaseModel):
    key: str
    type: str
    value: str
    ttl: int
    size: int


# ==================== 内存存储（模拟缓存）====================

_cache_keys: dict[str, dict] = {}
_cache_stats = {
    "hit_count": 12580,
    "miss_count": 2120,
    "total_commands": 500000,
    "uptime": 86400 * 7,  # 7天
}


def _init_sample_cache():
    """初始化示例缓存数据"""
    if not _cache_keys:
        now = datetime.now()
        sample_keys = [
            {
                "key": "user:profile:1001",
                "type": CacheKeyType.HASH,
                "ttl": 3600,
                "size": 2048,
                "access_count": 156,
                "last_access": (now - timedelta(minutes=5)).isoformat(),
                "created_at": (now - timedelta(days=2)).isoformat(),
                "creator": "user_service",
                "value": '{"id": 1001, "name": "张三", "role": "student"}',
            },
            {
                "key": "course:info:2001",
                "type": CacheKeyType.STRING,
                "ttl": 7200,
                "size": 1024,
                "access_count": 89,
                "last_access": (now - timedelta(minutes=15)).isoformat(),
                "created_at": (now - timedelta(days=3)).isoformat(),
                "creator": "course_service",
                "value": '{"id": 2001, "name": "数学", "teacher": "李老师"}',
            },
            {
                "key": "session:abc123",
                "type": CacheKeyType.STRING,
                "ttl": 1800,
                "size": 512,
                "access_count": 234,
                "last_access": (now - timedelta(minutes=2)).isoformat(),
                "created_at": (now - timedelta(hours=4)).isoformat(),
                "creator": "auth_service",
                "value": '{"user_id": 1001, "login_time": "2026-04-12T08:00:00"}',
            },
            {
                "key": "ai:ability:3001",
                "type": CacheKeyType.HASH,
                "ttl": -1,  # 永久
                "size": 4096,
                "access_count": 45,
                "last_access": (now - timedelta(hours=1)).isoformat(),
                "created_at": (now - timedelta(days=10)).isoformat(),
                "creator": "ai_service",
                "value": '{"math": 85, "english": 78, "physics": 92}',
            },
            {
                "key": "exam:questions:4001",
                "type": CacheKeyType.LIST,
                "ttl": 86400,
                "size": 8192,
                "access_count": 12,
                "last_access": (now - timedelta(hours=3)).isoformat(),
                "created_at": (now - timedelta(hours=8)).isoformat(),
                "creator": "exam_service",
                "value": '["q_001", "q_002", "q_003", "q_004", "q_005"]',
            },
            {
                "key": "settings:system",
                "type": CacheKeyType.HASH,
                "ttl": -1,
                "size": 1024,
                "access_count": 567,
                "last_access": (now - timedelta(minutes=1)).isoformat(),
                "created_at": (now - timedelta(days=30)).isoformat(),
                "creator": "system",
                "value": '{"site_name": "智慧校园", "max_upload_size": 10485760}',
            },
            {
                "key": "attendance:today",
                "type": CacheKeyType.SET,
                "ttl": 43200,
                "size": 5120,
                "access_count": 78,
                "last_access": (now - timedelta(minutes=30)).isoformat(),
                "created_at": (now - timedelta(hours=6)).isoformat(),
                "creator": "attendance_service",
                "value": '["1001", "1002", "1003", "1004", "1005"]',
            },
            {
                "key": "ranking:weekly",
                "type": CacheKeyType.ZSET,
                "ttl": 604800,
                "size": 20480,
                "access_count": 23,
                "last_access": (now - timedelta(hours=2)).isoformat(),
                "created_at": (now - timedelta(days=1)).isoformat(),
                "creator": "score_service",
                "value": '{"1001": 95.5, "1002": 92.0, "1003": 88.5}',
            },
        ]
        
        # 生成更多示例数据
        for i in range(9, 101):
            key_type = [CacheKeyType.STRING, CacheKeyType.HASH, CacheKeyType.LIST][i % 3]
            ttl_options = [3600, 7200, 1800, 86400, -1, 43200]
            ttl = ttl_options[i % len(ttl_options)]
            
            _cache_keys[f"sample:key:{i}"] = {
                "key": f"sample:key:{i}",
                "type": key_type,
                "ttl": ttl,
                "size": 512 + (i * 10),
                "access_count": i * 2,
                "last_access": (now - timedelta(minutes=i * 5)).isoformat(),
                "created_at": (now - timedelta(days=i % 10)).isoformat(),
                "creator": f"service_{i % 5}",
                "value": f'"sample value {i}"',
            }
        
        for key_data in sample_keys:
            _cache_keys[key_data["key"]] = key_data


# ==================== 辅助函数 ====================

def _calculate_hit_rate() -> float:
    """计算缓存命中率"""
    total = _cache_stats["hit_count"] + _cache_stats["miss_count"]
    if total == 0:
        return 0.0
    return round(_cache_stats["hit_count"] / total * 100, 2)


def _calculate_memory_usage() -> tuple[float, int]:
    """计算内存使用量"""
    total_bytes = sum(k["size"] for k in _cache_keys.values())
    total_mb = round(total_bytes / (1024 * 1024), 2)
    return total_mb, total_bytes


def _count_expired_keys() -> int:
    """统计过期键数量"""
    now = datetime.now()
    expired = 0
    for key_data in _cache_keys.values():
        if key_data["ttl"] > 0:
            created_at = datetime.fromisoformat(key_data["created_at"])
            expire_time = created_at + timedelta(seconds=key_data["ttl"])
            if expire_time < now:
                expired += 1
    return expired


# ==================== 路由定义 ====================

router = APIRouter(prefix="/cache", tags=["缓存监控"])


@router.get("/stats", response_model=dict)
async def get_cache_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取缓存统计信息
    
    返回缓存命中率、内存使用、键数量等统计信息
    """
    _init_sample_cache()
    
    memory_mb, memory_bytes = _calculate_memory_usage()
    
    stats = {
        "total_keys": len(_cache_keys),
        "hit_rate": _calculate_hit_rate(),
        "memory_usage": memory_mb,
        "memory_usage_bytes": memory_bytes,
        "expired_keys": _count_expired_keys(),
        "evicted_keys": 0,  # 模拟值
        "connected_clients": 12,  # 模拟值
        "total_commands_processed": _cache_stats["total_commands"],
        "uptime_seconds": _cache_stats["uptime"],
        "timestamp": datetime.now().isoformat(),
    }
    
    return success(stats)


@router.get("/keys", response_model=dict)
async def get_cache_keys(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    key_type: Optional[str] = Query(None, description="类型筛选"),
    sort_by: Optional[str] = Query("last_access", description="排序字段"),
    sort_order: Optional[str] = Query("desc", description="排序方向: asc/desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取缓存键列表
    
    返回缓存中的键列表，支持搜索和筛选
    """
    _init_sample_cache()
    
    # 筛选
    filtered_keys = list(_cache_keys.values())
    
    if keyword:
        filtered_keys = [k for k in filtered_keys if keyword in k["key"]]
    
    if key_type:
        filtered_keys = [k for k in filtered_keys if k["type"] == key_type]
    
    # 排序
    reverse = sort_order == "desc"
    if sort_by in ["key", "type", "ttl", "size", "access_count", "last_access", "created_at"]:
        filtered_keys.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse)
    
    # 分页
    total = len(filtered_keys)
    start = (page - 1) * page_size
    end = start + page_size
    items = filtered_keys[start:end]
    
    return page_response(items, total, page, page_size)


@router.get("/keys/{key:path}", response_model=dict)
async def get_cache_key(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取缓存键详情
    
    返回指定缓存键的详细信息和值
    """
    _init_sample_cache()
    
    key_data = _cache_keys.get(key)
    if not key_data:
        return success(message="键不存在")
    
    # 更新访问统计
    key_data["access_count"] += 1
    key_data["last_access"] = datetime.now().isoformat()
    _cache_stats["hit_count"] += 1
    
    return success({
        "key": key_data["key"],
        "type": key_data["type"],
        "ttl": key_data["ttl"],
        "size": key_data["size"],
        "access_count": key_data["access_count"],
        "last_access": key_data["last_access"],
        "created_at": key_data["created_at"],
        "creator": key_data["creator"],
        "value": key_data["value"],
    })


@router.delete("/keys/{key:path}", response_model=dict)
async def delete_cache_key(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    删除缓存键
    
    删除指定的缓存键
    """
    _init_sample_cache()
    
    if key not in _cache_keys:
        return success(message="键不存在")
    
    del _cache_keys[key]
    
    return success({"key": key}, f"键 {key} 已删除")


@router.post("/keys/{key:path}/ttl", response_model=dict)
async def update_cache_ttl(
    key: str,
    ttl: int = Query(..., description="新的TTL值(秒)，-1表示永久"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新缓存键的TTL
    
    修改指定缓存键的过期时间
    """
    _init_sample_cache()
    
    key_data = _cache_keys.get(key)
    if not key_data:
        return success(message="键不存在")
    
    key_data["ttl"] = ttl
    key_data["updated_at"] = datetime.now().isoformat()
    
    return success({
        "key": key,
        "ttl": ttl,
    }, f"键 {key} 的TTL已更新为 {ttl} 秒")


@router.post("/clear-expired", response_model=dict)
async def clear_expired_keys(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    清理过期缓存键
    
    删除所有已过期的缓存键
    """
    _init_sample_cache()
    
    now = datetime.now()
    expired_keys = []
    
    for key, key_data in list(_cache_keys.items()):
        if key_data["ttl"] > 0:
            created_at = datetime.fromisoformat(key_data["created_at"])
            expire_time = created_at + timedelta(seconds=key_data["ttl"])
            if expire_time < now:
                expired_keys.append(key)
                del _cache_keys[key]
    
    return success({
        "cleared_count": len(expired_keys),
        "cleared_keys": expired_keys[:10],  # 最多返回10个
    }, f"已清理 {len(expired_keys)} 个过期缓存键")


@router.post("/clear-all", response_model=dict)
async def clear_all_cache(
    confirm: bool = Query(False, description="确认清空所有缓存"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    清空所有缓存
    
    删除所有缓存键（危险操作，需要确认）
    """
    _init_sample_cache()
    
    if not confirm:
        return success(message="请设置 confirm=true 确认清空所有缓存")
    
    cleared_count = len(_cache_keys)
    _cache_keys.clear()
    
    return success({
        "cleared_count": cleared_count,
    }, f"已清空所有缓存，共 {cleared_count} 个键")


@router.get("/types", response_model=dict)
async def get_cache_types(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取缓存类型分布
    
    返回各类型缓存键的数量和内存占用
    """
    _init_sample_cache()
    
    type_stats = {}
    for key_data in _cache_keys.values():
        key_type = key_data["type"]
        if key_type not in type_stats:
            type_stats[key_type] = {"count": 0, "size": 0}
        type_stats[key_type]["count"] += 1
        type_stats[key_type]["size"] += key_data["size"]
    
    # 转换为列表格式
    result = []
    for key_type, stats in type_stats.items():
        result.append({
            "type": key_type,
            "count": stats["count"],
            "size": stats["size"],
            "size_formatted": f"{stats['size'] / 1024:.2f} KB" if stats["size"] < 1024 * 1024 else f"{stats['size'] / (1024 * 1024):.2f} MB",
        })
    
    # 按数量排序
    result.sort(key=lambda x: x["count"], reverse=True)
    
    return success(result)


@router.get("/memory-trend", response_model=dict)
async def get_memory_trend(
    hours: int = Query(24, ge=1, le=168, description="查询小时数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取内存使用趋势
    
    返回指定时间范围内的内存使用量变化
    """
    _init_sample_cache()
    
    now = datetime.now()
    data_points = []
    
    # 生成模拟数据
    current_memory, _ = _calculate_memory_usage()
    
    for i in range(hours, 0, -1):
        point_time = now - timedelta(hours=i)
        # 模拟波动
        variation = (i % 5 - 2) * 10  # -20 到 +20 的波动
        memory_at_point = max(50, current_memory + variation)
        
        data_points.append({
            "time": point_time.strftime("%H:%M"),
            "memory_mb": round(memory_at_point, 2),
        })
    
    # 添加当前点
    data_points.append({
        "time": now.strftime("%H:%M"),
        "memory_mb": current_memory,
    })
    
    return success({
        "hours": hours,
        "data": data_points,
        "current": current_memory,
        "average": round(sum(d["memory_mb"] for d in data_points) / len(data_points), 2),
        "max": round(max(d["memory_mb"] for d in data_points), 2),
        "min": round(min(d["memory_mb"] for d in data_points), 2),
    })


@router.post("/flushdb", response_model=dict)
async def flush_cache_db(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    刷新缓存数据库
    
    清除所有缓存数据并重置统计信息
    """
    _init_sample_cache()
    
    cleared_count = len(_cache_keys)
    _cache_keys.clear()
    _cache_stats["hit_count"] = 0
    _cache_stats["miss_count"] = 0
    
    return success({
        "cleared_count": cleared_count,
    }, "缓存数据库已刷新")
