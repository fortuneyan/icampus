"""
服务监控 API - T13: 服务监控面板
提供系统资源、数据库连接池、缓存状态的实时监控数据
"""

import psutil
import platform
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.response import success


# ==================== Schema 定义 ====================

class CPUInfo(BaseModel):
    percent: float  # CPU 使用率 %
    count: int      # CPU 核心数
    frequency: Optional[float] = None  # 当前频率 MHz


class MemoryInfo(BaseModel):
    total_gb: float
    used_gb: float
    available_gb: float
    percent: float


class DiskInfo(BaseModel):
    total_gb: float
    used_gb: float
    free_gb: float
    percent: float


class SystemInfo(BaseModel):
    cpu: CPUInfo
    memory: MemoryInfo
    disk: DiskInfo
    platform: str
    platform_version: str
    uptime_seconds: int
    timestamp: str


class DatabasePoolInfo(BaseModel):
    pool_size: int
    checked_out: int
    overflow: int
    checked_in: int
    status: str


class DatabaseInfo(BaseModel):
    pool: DatabasePoolInfo
    database: str
    status: str


class HealthStatus(BaseModel):
    overall: str  # healthy / degraded / unhealthy
    checks: dict
    timestamp: str


# ==================== 辅助函数 ====================

def _calculate_uptime() -> int:
    """获取系统运行时长（秒）"""
    try:
        boot_time = psutil.boot_time()
        uptime = datetime.now().timestamp() - boot_time
        return int(uptime)
    except Exception:
        return 0


def _get_cpu_info() -> CPUInfo:
    """获取 CPU 信息"""
    try:
        freq = psutil.cpu_freq()
        frequency = freq.current if freq else None
    except Exception:
        frequency = None
    
    return CPUInfo(
        percent=psutil.cpu_percent(interval=0.1),
        count=psutil.cpu_count(),
        frequency=frequency
    )


def _get_memory_info() -> MemoryInfo:
    """获取内存信息"""
    mem = psutil.virtual_memory()
    return MemoryInfo(
        total_gb=round(mem.total / (1024**3), 2),
        used_gb=round(mem.used / (1024**3), 2),
        available_gb=round(mem.available / (1024**3), 2),
        percent=mem.percent
    )


def _get_disk_info() -> DiskInfo:
    """获取磁盘信息"""
    try:
        disk = psutil.disk_usage('/')
        return DiskInfo(
            total_gb=round(disk.total / (1024**3), 2),
            used_gb=round(disk.used / (1024**3), 2),
            free_gb=round(disk.free / (1024**3), 2),
            percent=disk.percent
        )
    except Exception:
        # Windows 兼容：尝试获取 C: 盘
        disk = psutil.disk_usage('C:\\')
        return DiskInfo(
            total_gb=round(disk.total / (1024**3), 2),
            used_gb=round(disk.used / (1024**3), 2),
            free_gb=round(disk.free / (1024**3), 2),
            percent=disk.percent
        )


def _check_database_pool(db: AsyncSession) -> DatabasePoolInfo:
    """检查数据库连接池状态"""
    try:
        # SQLAlchemy 连接池信息
        pool = db.get_bind().pool
        pool_size = pool.size()
        checked_out = pool.checkedin()
        overflow = pool.overflow()
        checked_in = pool_size - checked_out + overflow
        
        # 判断状态
        usage_ratio = checked_out / pool_size if pool_size > 0 else 0
        if usage_ratio < 0.7:
            status = "healthy"
        elif usage_ratio < 0.9:
            status = "degraded"
        else:
            status = "unhealthy"
            
        return DatabasePoolInfo(
            pool_size=pool_size,
            checked_out=checked_out,
            overflow=overflow,
            checked_in=checked_in,
            status=status
        )
    except Exception as e:
        return DatabasePoolInfo(
            pool_size=0,
            checked_out=0,
            overflow=0,
            checked_in=0,
            status="unknown"
        )


def _assess_overall_health(system_info: SystemInfo, db_pool: DatabasePoolInfo) -> str:
    """评估整体健康状态"""
    issues = []
    
    # 检查 CPU
    if system_info.cpu.percent > 90:
        issues.append("high_cpu")
    
    # 检查内存
    if system_info.memory.percent > 90:
        issues.append("high_memory")
    
    # 检查磁盘
    if system_info.disk.percent > 90:
        issues.append("high_disk")
    
    # 检查数据库
    if db_pool.status != "healthy":
        issues.append("db_pool_stress")
    
    # 判断整体状态
    if len(issues) == 0:
        return "healthy"
    elif len(issues) == 1:
        return "degraded"
    else:
        return "unhealthy"


# ==================== 路由定义 ====================

router = APIRouter(prefix="", tags=["服务监控"])


@router.get("/system")
async def get_system_info():
    """
    获取系统资源信息
    - CPU 使用率和核心数
    - 内存总量、使用量、可用量
    - 磁盘总量、使用量、可用量
    - 平台信息和运行时长
    """
    return success({
        "cpu": _get_cpu_info().model_dump(),
        "memory": _get_memory_info().model_dump(),
        "disk": _get_disk_info().model_dump(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "uptime_seconds": _calculate_uptime(),
        "timestamp": datetime.now().isoformat()
    })


@router.get("/database")
async def get_database_info(db: AsyncSession = Depends(get_db)):
    """
    获取数据库连接池信息
    - 连接池大小
    - 已使用/可用连接数
    - 溢出连接数
    - 健康状态
    """
    # 获取数据库名称
    try:
        result = await db.execute(text("SELECT current_database()"))
        db_name = result.scalar() or "unknown"
    except Exception:
        db_name = "unknown"
    
    pool_info = _check_database_pool(db)
    
    return success({
        "pool": pool_info.model_dump(),
        "database": db_name,
        "status": pool_info.status
    })


@router.get("/health")
async def get_health_status(db: AsyncSession = Depends(get_db)):
    """
    获取整体健康状态
    - overall: healthy / degraded / unhealthy
    - checks: 各检查项详细状态
    """
    # 获取系统信息
    cpu_info = _get_cpu_info()
    memory_info = _get_memory_info()
    disk_info = _get_disk_info()
    
    # 获取数据库连接池状态
    db_pool = _check_database_pool(db)
    
    # 构建检查详情
    checks = {
        "cpu": {
            "status": "ok" if cpu_info.percent < 90 else "warning",
            "value": f"{cpu_info.percent}%"
        },
        "memory": {
            "status": "ok" if memory_info.percent < 90 else "warning",
            "value": f"{memory_info.percent}%"
        },
        "disk": {
            "status": "ok" if disk_info.percent < 90 else "warning",
            "value": f"{disk_info.percent}%"
        },
        "database": {
            "status": db_pool.status,
            "pool_size": db_pool.pool_size,
            "checked_out": db_pool.checked_out
        }
    }
    
    # 评估整体状态
    system_info = SystemInfo(
        cpu=cpu_info,
        memory=memory_info,
        disk=disk_info,
        platform=platform.system(),
        platform_version=platform.version(),
        uptime_seconds=_calculate_uptime(),
        timestamp=datetime.now().isoformat()
    )
    overall = _assess_overall_health(system_info, db_pool)
    
    return success({
        "overall": overall,
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    })


@router.get("/process")
async def get_process_info():
    """
    获取当前进程信息
    - 进程 ID
    - 内存使用
    - CPU 使用率
    - 线程数
    """
    import os
    import threading
    
    process = psutil.Process(os.getpid())
    
    try:
        cpu_percent = process.cpu_percent(interval=0.1)
    except Exception:
        cpu_percent = 0.0
    
    return success({
        "pid": process.pid,
        "memory_mb": round(process.memory_info().rss / (1024 * 1024), 2),
        "cpu_percent": cpu_percent,
        "num_threads": process.num_threads(),
        "create_time": datetime.fromtimestamp(process.create_time()).isoformat(),
        "status": process.status()
    })
