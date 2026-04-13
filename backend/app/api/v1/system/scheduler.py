"""
定时任务管理 API - T13: 定时任务管理
提供定时任务的增删改查、启用/禁用、立即执行等功能
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.response import success, page_response


# ==================== Schema 定义 ====================

class SchedulerTaskType:
    """任务类型"""
    BACKUP = "backup"           # 数据备份
    SYNC = "sync"               # 数据同步
    CACHE = "cache"             # 缓存清理
    REPORT = "report"           # 报表生成
    NOTIFICATION = "notification"  # 通知推送
    CLEANUP = "cleanup"         # 数据清理
    CUSTOM = "custom"           # 自定义


class SchedulerTaskStatus:
    """任务状态"""
    ENABLED = "enabled"         # 已启用
    DISABLED = "disabled"       # 已禁用
    RUNNING = "running"         # 运行中
    ERROR = "error"             # 错误


class SchedulerTaskCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="任务名称")
    task_type: str = Field(..., description="任务类型")
    cron: str = Field(..., min_length=1, max_length=100, description="Cron表达式")
    description: Optional[str] = Field(None, max_length=500, description="任务描述")
    params: Optional[dict] = Field(None, description="任务参数")


class SchedulerTaskUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    task_type: Optional[str] = None
    cron: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    params: Optional[dict] = None
    enabled: Optional[bool] = None


class SchedulerTaskResponse(BaseModel):
    id: str
    name: str
    task_type: str
    cron: str
    description: Optional[str]
    enabled: bool
    status: str
    last_run: Optional[str]
    last_result: Optional[str]
    next_run: Optional[str]
    run_count: int
    created_at: str
    updated_at: str


class TaskLogResponse(BaseModel):
    id: str
    task_id: str
    task_name: str
    start_time: str
    end_time: Optional[str]
    duration: Optional[str]
    status: str
    message: Optional[str]


# ==================== 内存存储（实际项目应使用数据库）====================

_tasks: dict[str, dict] = {}
_task_logs: list[dict] = []


def _init_sample_tasks():
    """初始化示例任务"""
    if not _tasks:
        now = datetime.now()
        sample_tasks = [
            {
                "id": str(uuid.uuid4()),
                "name": "每日数据备份",
                "task_type": SchedulerTaskType.BACKUP,
                "cron": "0 0 2 * * *",
                "description": "每天凌晨2点执行数据备份",
                "enabled": True,
                "status": SchedulerTaskStatus.ENABLED,
                "last_run": (now - timedelta(hours=14)).isoformat(),
                "last_result": "success",
                "next_run": (now + timedelta(hours=10)).isoformat(),
                "run_count": 45,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "params": {"backup_type": "full"},
            },
            {
                "id": str(uuid.uuid4()),
                "name": "缓存清理",
                "task_type": SchedulerTaskType.CACHE,
                "cron": "0 0 0 * * *",
                "description": "每天凌晨清理过期缓存",
                "enabled": True,
                "status": SchedulerTaskStatus.ENABLED,
                "last_run": (now - timedelta(hours=16)).isoformat(),
                "last_result": "success",
                "next_run": (now + timedelta(hours=8)).isoformat(),
                "run_count": 120,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "params": {"expire_days": 7},
            },
            {
                "id": str(uuid.uuid4()),
                "name": "学习数据同步",
                "task_type": SchedulerTaskType.SYNC,
                "cron": "0 */30 * * * *",
                "description": "每30分钟同步学习记录",
                "enabled": True,
                "status": SchedulerTaskStatus.ENABLED,
                "last_run": (now - timedelta(minutes=12)).isoformat(),
                "last_result": "success",
                "next_run": (now + timedelta(minutes=18)).isoformat(),
                "run_count": 288,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "params": {"sync_type": "incremental"},
            },
            {
                "id": str(uuid.uuid4()),
                "name": "周报生成",
                "task_type": SchedulerTaskType.REPORT,
                "cron": "0 0 8 * * 1",
                "description": "每周一上午8点生成周报",
                "enabled": False,
                "status": SchedulerTaskStatus.DISABLED,
                "last_run": None,
                "last_result": None,
                "next_run": None,
                "run_count": 0,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "params": {"report_type": "weekly"},
            },
        ]
        for task in sample_tasks:
            _tasks[task["id"]] = task
        
        # 初始化示例日志
        global _task_logs
        _task_logs = [
            {
                "id": str(uuid.uuid4()),
                "task_id": sample_tasks[0]["id"],
                "task_name": sample_tasks[0]["name"],
                "start_time": (now - timedelta(hours=14)).isoformat(),
                "end_time": (now - timedelta(hours=13, minutes=45)).isoformat(),
                "duration": "15分30秒",
                "status": "success",
                "message": "备份完成，共备份 128 个文件，大小 256MB",
            },
            {
                "id": str(uuid.uuid4()),
                "task_id": sample_tasks[1]["id"],
                "task_name": sample_tasks[1]["name"],
                "start_time": (now - timedelta(hours=16)).isoformat(),
                "end_time": (now - timedelta(hours=15, minutes=59)).isoformat(),
                "duration": "1分15秒",
                "status": "success",
                "message": "清理过期缓存 2345 条",
            },
            {
                "id": str(uuid.uuid4()),
                "task_id": sample_tasks[2]["id"],
                "task_name": sample_tasks[2]["name"],
                "start_time": (now - timedelta(minutes=42)).isoformat(),
                "end_time": (now - timedelta(minutes=42, seconds=5)).isoformat(),
                "duration": "5秒",
                "status": "success",
                "message": "同步完成，新增 23 条记录",
            },
        ]


# ==================== 辅助函数 ====================

def _calculate_next_run(cron: str, base_time: Optional[datetime] = None) -> Optional[str]:
    """
    根据Cron表达式计算下次执行时间
    简化版：仅支持简单的间隔格式
    """
    now = base_time or datetime.now()
    parts = cron.split()
    
    if len(parts) == 6:  # 秒 分 时 日 月 周
        second, minute, hour, day, month, week = parts
        
        # 简单处理：每小时、每天、每周
        if second == "0" and minute == "0" and hour == "*":
            # 每小时
            next_time = now.replace(minute=0, second=0) + timedelta(hours=1)
        elif second == "0" and minute == "0" and hour.startswith("*/"):
            # 每N小时
            try:
                n = int(hour.replace("*/", ""))
                next_time = now + timedelta(hours=n)
                next_time = next_time.replace(minute=0, second=0)
            except:
                next_time = now + timedelta(hours=1)
        elif second == "0" and minute.startswith("*/"):
            # 每N分钟
            try:
                n = int(minute.replace("*/", ""))
                next_time = now + timedelta(minutes=n)
                next_time = next_time.replace(second=0)
            except:
                next_time = now + timedelta(minutes=30)
        else:
            # 默认1小时后
            next_time = now + timedelta(hours=1)
    else:
        next_time = now + timedelta(hours=1)
    
    return next_time.isoformat()


def _format_duration(seconds: int) -> str:
    """格式化持续时间"""
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}分{secs}秒"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}小时{minutes}分"


# ==================== 路由定义 ====================

router = APIRouter(prefix="/scheduler", tags=["定时任务管理"])


@router.get("/tasks", response_model=dict)
async def get_scheduler_tasks(
    keyword: Optional[str] = Query(None),
    task_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取定时任务列表
    """
    _init_sample_tasks()
    
    # 筛选
    filtered_tasks = list(_tasks.values())
    
    if keyword:
        filtered_tasks = [t for t in filtered_tasks if keyword.lower() in t["name"].lower()]
    
    if task_type:
        filtered_tasks = [t for t in filtered_tasks if t["task_type"] == task_type]
    
    if status:
        if status == "enabled":
            filtered_tasks = [t for t in filtered_tasks if t["enabled"]]
        elif status == "disabled":
            filtered_tasks = [t for t in filtered_tasks if not t["enabled"]]
    
    # 排序：按创建时间倒序
    filtered_tasks.sort(key=lambda x: x["created_at"], reverse=True)
    
    # 分页
    total = len(filtered_tasks)
    start = (page - 1) * page_size
    end = start + page_size
    items = filtered_tasks[start:end]
    
    return page_response(items, total, page, page_size)


@router.get("/tasks/{task_id}", response_model=dict)
async def get_scheduler_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取定时任务详情
    """
    _init_sample_tasks()
    
    task = _tasks.get(task_id)
    if not task:
        return success(message="任务不存在")
    
    return success(task)


@router.post("/tasks", response_model=dict)
async def create_scheduler_task(
    data: SchedulerTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建定时任务
    """
    _init_sample_tasks()
    
    now = datetime.now()
    task_id = str(uuid.uuid4())
    
    task = {
        "id": task_id,
        "name": data.name,
        "task_type": data.task_type,
        "cron": data.cron,
        "description": data.description,
        "enabled": True,
        "status": SchedulerTaskStatus.ENABLED,
        "last_run": None,
        "last_result": None,
        "next_run": _calculate_next_run(data.cron),
        "run_count": 0,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "params": data.params or {},
    }
    
    _tasks[task_id] = task
    
    return success(task, "任务创建成功")


@router.put("/tasks/{task_id}", response_model=dict)
async def update_scheduler_task(
    task_id: str,
    data: SchedulerTaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新定时任务
    """
    _init_sample_tasks()
    
    task = _tasks.get(task_id)
    if not task:
        return success(message="任务不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # 如果修改了cron，重新计算下次执行时间
    if "cron" in update_data:
        update_data["next_run"] = _calculate_next_run(update_data["cron"])
    
    # 更新状态
    if "enabled" in update_data:
        update_data["status"] = SchedulerTaskStatus.ENABLED if update_data["enabled"] else SchedulerTaskStatus.DISABLED
    
    update_data["updated_at"] = datetime.now().isoformat()
    
    task.update(update_data)
    
    return success(task, "任务更新成功")


@router.delete("/tasks/{task_id}", response_model=dict)
async def delete_scheduler_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    删除定时任务
    """
    _init_sample_tasks()
    
    if task_id not in _tasks:
        return success(message="任务不存在")
    
    del _tasks[task_id]
    
    return success(message="任务删除成功")


@router.post("/tasks/{task_id}/toggle", response_model=dict)
async def toggle_scheduler_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    启用/禁用定时任务
    """
    _init_sample_tasks()
    
    task = _tasks.get(task_id)
    if not task:
        return success(message="任务不存在")
    
    task["enabled"] = not task["enabled"]
    task["status"] = SchedulerTaskStatus.ENABLED if task["enabled"] else SchedulerTaskStatus.DISABLED
    task["updated_at"] = datetime.now().isoformat()
    
    action = "启用" if task["enabled"] else "禁用"
    return success(task, f"任务已{action}")


@router.post("/tasks/{task_id}/run", response_model=dict)
async def run_scheduler_task_now(
    task_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    立即执行定时任务
    """
    _init_sample_tasks()
    
    task = _tasks.get(task_id)
    if not task:
        return success(message="任务不存在")
    
    now = datetime.now()
    
    # 模拟执行任务
    def execute_task():
        import time
        time.sleep(2)  # 模拟执行时间
        # 实际项目中这里会调用具体的任务函数
    
    background_tasks.add_task(execute_task)
    
    # 记录执行日志
    log_id = str(uuid.uuid4())
    log = {
        "id": log_id,
        "task_id": task_id,
        "task_name": task["name"],
        "start_time": now.isoformat(),
        "end_time": None,
        "duration": None,
        "status": "running",
        "message": "任务执行中...",
    }
    _task_logs.insert(0, log)
    
    # 更新任务状态
    task["status"] = SchedulerTaskStatus.RUNNING
    task["last_run"] = now.isoformat()
    task["run_count"] += 1
    
    # 模拟任务完成（实际应该在后台任务中更新）
    import asyncio
    async def complete_task():
        await asyncio.sleep(2)
        end_time = datetime.now()
        duration = (end_time - now).seconds
        
        log["end_time"] = end_time.isoformat()
        log["duration"] = _format_duration(duration)
        log["status"] = "success"
        log["message"] = f"任务执行成功，耗时 {log['duration']}"
        
        task["status"] = SchedulerTaskStatus.ENABLED if task["enabled"] else SchedulerTaskStatus.DISABLED
        task["last_result"] = "success"
        task["next_run"] = _calculate_next_run(task["cron"])
    
    asyncio.create_task(complete_task())
    
    return success({
        "task_id": task_id,
        "log_id": log_id,
        "start_time": now.isoformat(),
    }, "任务已开始执行")


@router.get("/logs", response_model=dict)
async def get_scheduler_logs(
    task_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取任务执行日志
    """
    _init_sample_tasks()
    
    filtered_logs = _task_logs.copy()
    
    if task_id:
        filtered_logs = [l for l in filtered_logs if l["task_id"] == task_id]
    
    if status:
        filtered_logs = [l for l in filtered_logs if l["status"] == status]
    
    # 分页
    total = len(filtered_logs)
    start = (page - 1) * page_size
    end = start + page_size
    items = filtered_logs[start:end]
    
    return page_response(items, total, page, page_size)


@router.get("/types", response_model=dict)
async def get_scheduler_task_types(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取支持的任务类型列表
    """
    types = [
        {"value": SchedulerTaskType.BACKUP, "label": "数据备份", "color": "primary"},
        {"value": SchedulerTaskType.SYNC, "label": "数据同步", "color": "success"},
        {"value": SchedulerTaskType.CACHE, "label": "缓存清理", "color": "warning"},
        {"value": SchedulerTaskType.REPORT, "label": "报表生成", "color": "info"},
        {"value": SchedulerTaskType.NOTIFICATION, "label": "通知推送", "color": ""},
        {"value": SchedulerTaskType.CLEANUP, "label": "数据清理", "color": "danger"},
        {"value": SchedulerTaskType.CUSTOM, "label": "自定义", "color": ""},
    ]
    return success(types)
