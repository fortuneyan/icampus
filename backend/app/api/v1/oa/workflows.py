"""
工作流管理API
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.response import success, page_response
from app.services.oa.workflow_engine import WorkflowEngine

router = APIRouter()


@router.get("/", response_model=dict)
async def get_workflow_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取工作流定义列表（分页）"""
    engine = WorkflowEngine(db)
    definitions = await engine.get_definitions()
    items = [
        {
            "id": str(d.id),
            "name": d.name,
            "code": d.code,
            "description": d.description,
            "is_active": d.is_active,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in definitions
    ]
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return page_response(items[start:end], total, page, page_size)


@router.get("/definitions", response_model=dict)
async def get_workflow_definitions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取工作流定义列表"""
    engine = WorkflowEngine(db)
    definitions = await engine.get_definitions()
    items = [
        {
            "id": str(d.id),
            "name": d.name,
            "code": d.code,
            "description": d.description,
            "is_active": d.is_active,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in definitions
    ]
    return success(items)


@router.get("/instances", response_model=dict)
async def get_my_instances(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取我的申请列表"""
    engine = WorkflowEngine(db)
    result = await engine.get_my_instances(current_user.id, page, page_size, status)
    return page_response(result["items"], result["total"], page, page_size)


@router.post("/instances", response_model=dict)
async def start_instance(
    workflow_id: str,
    business_type: str,
    business_id: str,
    context: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发起审批流程"""
    engine = WorkflowEngine(db)
    instance = await engine.start_instance(
        business_type=business_type,
        business_id=UUID(business_id),
        context=context,
    )
    return success({"id": str(instance.id)}, "审批流程已发起")


@router.get("/instances/{instance_id}", response_model=dict)
async def get_instance_detail(
    instance_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取申请详情"""
    engine = WorkflowEngine(db)
    detail = await engine.get_instance_detail(instance_id)
    return success(detail)


@router.post("/instances/{instance_id}/cancel", response_model=dict)
async def cancel_instance(
    instance_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """撤回申请"""
    engine = WorkflowEngine(db)
    instance = await engine.cancel_instance(instance_id, current_user.id)
    return success({"id": str(instance.id)}, "申请已撤回")


@router.get("/tasks", response_model=dict)
async def get_my_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取待我审批的任务"""
    engine = WorkflowEngine(db)
    result = await engine.get_my_pending_tasks(current_user.id, page, page_size)
    return page_response(result["items"], result["total"], page, page_size)


@router.get("/tasks/{task_id}", response_model=dict)
async def get_task_detail(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取审批任务详情"""
    engine = WorkflowEngine(db)
    detail = await engine.get_task_detail(task_id)
    return success(detail)


@router.post("/tasks/{task_id}/approve", response_model=dict)
async def approve_task(
    task_id: UUID,
    comment: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """审批通过"""
    engine = WorkflowEngine(db)
    task = await engine.handle_task(
        task_id=task_id,
        action="APPROVE",
        comment=comment,
        operator_id=current_user.id,
    )
    return success({"id": str(task.id)}, "审批已通过")


@router.post("/tasks/{task_id}/reject", response_model=dict)
async def reject_task(
    task_id: UUID,
    comment: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """审批拒绝"""
    engine = WorkflowEngine(db)
    task = await engine.handle_task(
        task_id=task_id,
        action="REJECT",
        comment=comment,
        operator_id=current_user.id,
    )
    return success({"id": str(task.id)}, "审批已拒绝")


@router.post("/tasks/{task_id}/transfer", response_model=dict)
async def transfer_task(
    task_id: UUID,
    target_user_id: str,
    comment: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """转交任务"""
    engine = WorkflowEngine(db)
    task = await engine.handle_task(
        task_id=task_id,
        action="TRANSFER",
        comment=comment,
        operator_id=current_user.id,
        target_user_id=UUID(target_user_id),
    )
    return success({"id": str(task.id)}, "任务已转交")


@router.post("/tasks/{task_id}/delegate", response_model=dict)
async def delegate_task(
    task_id: UUID,
    delegate_to: str,
    comment: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """转派任务"""
    engine = WorkflowEngine(db)
    task = await engine.handle_task(
        task_id=task_id,
        action="DELEGATE",
        comment=comment,
        operator_id=current_user.id,
        target_user_id=UUID(delegate_to),
    )
    return success({"id": str(task.id)}, "任务已转派")


@router.get("/cc", response_model=dict)
async def get_my_cc(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取抄送给我的"""
    engine = WorkflowEngine(db)
    result = await engine.get_my_cc(current_user.id, page, page_size)
    return page_response(result["items"], result["total"], page, page_size)