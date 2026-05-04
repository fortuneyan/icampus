"""
任务看板API
路径: /oa/task-boards/*
"""

from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.oa.task import TaskBoardCreate as ProjectCreate, TaskBoardUpdate as ProjectUpdate
from app.schemas.response import success, page_response
from app.services.oa.task_svc import TaskProjectService

router = APIRouter()


@router.get("", response_model=dict)
async def get_boards(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取看板列表"""
    service = TaskProjectService(db)
    result = await service.get_project_list(
        page=page,
        page_size=page_size,
        status=status,
    )
    return page_response(result["items"], result["total"], page, page_size)


@router.get("/{board_id}", response_model=dict)
async def get_board_detail(
    board_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取看板详情"""
    service = TaskProjectService(db)
    project = await service.get_project_detail(board_id)
    return success(project)


@router.post("", response_model=dict)
async def create_board(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建看板"""
    service = TaskProjectService(db)
    project = await service.create_project(data.model_dump(), current_user.id)
    return success({"id": str(project.id)}, "看板创建成功")


@router.put("/{board_id}", response_model=dict)
async def update_board(
    board_id: UUID,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """编辑看板"""
    service = TaskProjectService(db)
    project = await service.update_project(board_id, data.model_dump(exclude_unset=True))
    return success({"id": str(project.id)}, "看板更新成功")


@router.delete("/{board_id}", response_model=dict)
async def delete_board(
    board_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除看板"""
    service = TaskProjectService(db)
    await service.delete_project(board_id)
    return success(message="看板删除成功")


@router.post("/{board_id}/archive", response_model=dict)
async def archive_board(
    board_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """归档看板"""
    service = TaskProjectService(db)
    project = await service.archive_project(board_id)
    return success({"id": str(project.id)}, "看板已归档")


# 看板列
@router.get("/{board_id}/columns", response_model=dict)
async def get_columns(
    board_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取看板列"""
    service = TaskProjectService(db)
    columns = await service.get_columns(board_id)
    return success(columns)


# 看板成员
@router.get("/{board_id}/members", response_model=dict)
async def get_board_members(
    board_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取看板成员"""
    service = TaskProjectService(db)
    members = await service.get_members(board_id)
    return success(members)


@router.post("/{board_id}/members", response_model=dict)
async def add_board_member(
    board_id: UUID,
    user_id: UUID,
    role: str = "member",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加看板成员"""
    service = TaskProjectService(db)
    member = await service.add_member(board_id, user_id, role)
    return success({"id": str(member["id"])}, "成员添加成功")


@router.delete("/{board_id}/members/{member_id}", response_model=dict)
async def remove_board_member(
    board_id: UUID,
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """移除看板成员"""
    service = TaskProjectService(db)
    await service.remove_member(board_id, member_id)
    return success(message="成员已移除")
