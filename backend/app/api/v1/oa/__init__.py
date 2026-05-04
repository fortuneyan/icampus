"""
OA模块主路由
"""

from fastapi import APIRouter

from app.api.v1.oa import (
    announcements,
    announcement_categories,
    rooms,
    room_bookings,
    assets,
    asset_categories,
    asset_operations,
    worklogs,
    worklog_categories,
    tasks,
    task_boards,
    workflows,
)

router = APIRouter()

# 注册子路由
router.include_router(workflows.router, prefix="/workflows", tags=["OA-工作流"])
router.include_router(announcements.router, prefix="/announcements", tags=["OA-公告通知"])
router.include_router(announcement_categories.router, prefix="/announcement-categories", tags=["OA-公告分类"])
router.include_router(rooms.router, prefix="/rooms", tags=["OA-教室管理"])
router.include_router(room_bookings.router, prefix="/room-bookings", tags=["OA-教室预约"])
router.include_router(assets.router, prefix="/assets", tags=["OA-资产管理"])
router.include_router(asset_categories.router, prefix="/asset-categories", tags=["OA-资产分类"])
router.include_router(asset_operations.router, prefix="/asset-operations", tags=["OA-资产操作"])
router.include_router(worklogs.router, prefix="/worklogs", tags=["OA-工作日志"])
router.include_router(worklog_categories.router, prefix="/worklog-categories", tags=["OA-日志分类"])
router.include_router(tasks.router, prefix="/tasks", tags=["OA-任务管理"])
router.include_router(task_boards.router, prefix="/task-boards", tags=["OA-任务看板"])
