"""
工作流定时任务调度器

使用 APScheduler 注册和管理工作流相关的定时任务
"""
import logging
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.database import async_session_factory
from app.services.oa.workflow_timeout_service import WorkflowTimeoutService

# 全局调度器实例
_scheduler: Optional[AsyncIOScheduler] = None
_logger = logging.getLogger(__name__)


async def _run_workflow_timeout_check():
    """
    工作流超时检查定时任务

    每10分钟执行一次，检测并处理超时的审批任务
    """
    _logger.info("[WorkflowTimeout] Starting workflow timeout check...")
    try:
        async with async_session_factory() as db:
            service = WorkflowTimeoutService(db)
            stats = await service.process_overdue_tasks()
            _logger.info(
                "[WorkflowTimeout] Completed: notified=%d, auto_approved=%d, skipped=%d",
                stats["notified"],
                stats["auto_approved"],
                stats["skipped"],
            )
    except Exception as e:
        _logger.error(
            "[WorkflowTimeout] Error during workflow timeout check: %s",
            str(e),
            exc_info=True,
        )


def get_scheduler() -> AsyncIOScheduler:
    """
    获取全局调度器实例

    Returns:
        AsyncIOScheduler: 全局调度器实例
    """
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


def setup_workflow_scheduler():
    """
    注册工作流相关定时任务

    调用时机：在应用启动时调用（如 main.py 中）
    """
    scheduler = get_scheduler()

    # 工作流超时检查任务（每10分钟执行一次）
    scheduler.add_job(
        _run_workflow_timeout_check,
        trigger=IntervalTrigger(minutes=10),
        id="workflow_timeout_check",
        name="工作流超时检查",
        replace_existing=True,
        max_instances=1,  # 防止并发执行
    )

    _logger.info("[Scheduler] Workflow timeout check job registered (interval: 10 minutes)")


def start_scheduler():
    """启动调度器（仅在未运行时启动）"""
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        _logger.info("[Scheduler] Started")


def stop_scheduler():
    """停止调度器"""
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=False)
        _logger.info("[Scheduler] Stopped")
