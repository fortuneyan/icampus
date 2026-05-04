"""
任务看板API
"""

from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.oa.task import (
    TaskBoardCreate as ProjectCreate,
    TaskBoardUpdate as ProjectUpdate,
    TaskCardCreate as TaskCreate,
    TaskCardUpdate as TaskUpdate,
    TaskMoveRequest as TaskStatusUpdate,
    TaskCardUpdate as TaskProgressUpdate,
    TaskCardCreate as TaskAssign,
    TaskCommentCreate as CommentCreate,
)
from app.schemas.response import success, page_response
from app.services.oa.task_svc import TaskProjectService, TaskService

router = APIRouter()


# ============ 项目管理 ============

@router.get("/projects", response_model=dict)
async def get_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取项目列表"""
    service = TaskProjectService(db)
    result = await service.get_project_list(
        page=page,
        page_size=page_size,
        status=status,
    )
    return page_response(result["items"], result["total"], page, page_size)


@router.get("/projects/{project_id}", response_model=dict)
async def get_project_detail(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取项目详情"""
    service = TaskProjectService(db)
    project = await service.get_project_detail(project_id)
    return success(project)


@router.post("/projects", response_model=dict)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建项目"""
    service = TaskProjectService(db)
    project = await service.create_project(data.model_dump(), current_user.id)
    return success({"id": str(project.id)}, "项目创建成功")


@router.put("/projects/{project_id}", response_model=dict)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """编辑项目"""
    service = TaskProjectService(db)
    project = await service.update_project(project_id, data.model_dump(exclude_unset=True))
    return success({"id": str(project.id)}, "项目更新成功")


@router.delete("/projects/{project_id}", response_model=dict)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除项目"""
    service = TaskProjectService(db)
    await service.delete_project(project_id)
    return success(message="项目删除成功")


@router.post("/projects/{project_id}/archive", response_model=dict)
async def archive_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """归档项目"""
    service = TaskProjectService(db)
    project = await service.archive_project(project_id)
    return success({"id": str(project.id)}, "项目已归档")


# ============ 任务管理 ============

@router.get("", response_model=dict)
async def get_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    project_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assignee_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取任务列表"""
    service = TaskService(db)
    result = await service.get_task_list(
        page=page,
        page_size=page_size,
        project_id=UUID(project_id) if project_id else None,
        status=status,
        priority=priority,
        assignee_id=UUID(assignee_id) if assignee_id else None,
    )
    return page_response(result["items"], result["total"], page, page_size)


@router.get("/{task_id}", response_model=dict)
async def get_task_detail(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取任务详情"""
    service = TaskService(db)
    task = await service.get_task_detail(task_id)
    return success(task)


@router.post("", response_model=dict)
async def create_task(
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建任务"""
    service = TaskService(db)
    task = await service.create_task(data.model_dump(), current_user.id)
    return success({"id": str(task.id)}, "任务创建成功")


@router.put("/{task_id}", response_model=dict)
async def update_task(
    task_id: UUID,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """编辑任务"""
    service = TaskService(db)
    task = await service.update_task(task_id, data.model_dump(exclude_unset=True))
    return success({"id": str(task.id)}, "任务更新成功")


@router.delete("/{task_id}", response_model=dict)
async def delete_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除任务"""
    service = TaskService(db)
    await service.delete_task(task_id, current_user.id)
    return success(message="任务删除成功")


@router.post("/{task_id}/status", response_model=dict)
async def update_task_status(
    task_id: UUID,
    data: TaskStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新任务状态"""
    service = TaskService(db)
    task = await service.update_status(
        task_id=task_id,
        status=data.status,
        operator_id=current_user.id,
    )
    return success({"id": str(task.id)}, "状态更新成功")


@router.post("/{task_id}/progress", response_model=dict)
async def update_task_progress(
    task_id: UUID,
    data: TaskProgressUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新任务进度"""
    service = TaskService(db)
    task = await service.update_progress(task_id, data.progress)
    return success({"id": str(task.id)}, "进度更新成功")


@router.post("/{task_id}/assign", response_model=dict)
async def assign_task(
    task_id: UUID,
    data: TaskAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """分配任务"""
    service = TaskService(db)
    task = await service.assign_task(
        task_id=task_id,
        assignee_id=data.assignee_id,
        operator_id=current_user.id,
    )
    return success({"id": str(task.id)}, "任务分配成功")


@router.get("/{task_id}/comments", response_model=dict)
async def get_task_comments(
    task_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取评论列表"""
    service = TaskService(db)
    result = await service.get_comments(task_id, page, page_size)
    return page_response(result["items"], result["total"], page, page_size)


@router.post("/{task_id}/comments", response_model=dict)
async def add_task_comment(
    task_id: UUID,
    data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加评论"""
    service = TaskService(db)
    comment = await service.add_comment(
        task_id=task_id,
        user_id=current_user.id,
        data=data.model_dump(),
    )
    return success({"id": str(comment.id)}, "评论成功")


@router.delete("/comments/{comment_id}", response_model=dict)
async def delete_task_comment(
    comment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除评论"""
    service = TaskService(db)
    await service.delete_comment(comment_id, current_user.id)
    return success(message="评论删除成功")


# ============ 我的任务 ============

@router.get("/my/tasks", response_model=dict)
async def get_my_tasks(
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我的任务"""
    service = TaskService(db)
    tasks = await service.get_my_tasks(current_user.id, status)
    return success(tasks)


@router.get("/my/tasks/board", response_model=dict)
async def get_my_task_board(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我的看板视图"""
    service = TaskService(db)
    board = await service.get_my_board(current_user.id)
    return success(board)