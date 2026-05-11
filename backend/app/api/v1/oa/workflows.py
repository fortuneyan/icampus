"""
工作流管理API
"""

from datetime import datetime
from typing import Optional, List, Any, Dict
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Body
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.oa.workflow import OaWorkflowDefinition, OaWorkflowNode
from app.schemas.response import success, page_response
from app.services.oa.workflow_engine import WorkflowEngine

router = APIRouter()


# ============================================================
# Pydantic Schema
# ============================================================

class StartInstanceRequest(BaseModel):
    """发起审批请求体"""
    workflow_id: str
    business_type: str
    business_id: str
    title: str
    context: Optional[Dict[str, Any]] = None
    cc_list: Optional[List[str]] = None
    summary: Optional[str] = None


# ============================================================
# 工作流定义管理
# ============================================================

@router.get("/", response_model=dict)
async def get_workflow_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    name: Optional[str] = Query(None, description="工作流名称"),
    status: Optional[str] = Query(None, description="状态筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取工作流定义列表（分页）"""
    engine = WorkflowEngine(db)
    definitions = await engine.get_definitions()

    # 过滤
    if name:
        definitions = [d for d in definitions if name in (d.name or "")]
    if status:
        definitions = [d for d in definitions if d.status == status]

    items = [
        {
            "id": str(d.id),
            "name": d.name,
            "code": d.code,
            "description": d.description,
            "category": d.business_type,
            "version": d.version,
            "is_active": d.is_active,
            "status": d.status,
            "instance_count": len([i for i in d.instances if not i.is_deleted]) if hasattr(d, 'instances') else 0,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "updated_at": d.updated_at.isoformat() if d.updated_at else None,
        }
        for d in definitions
    ]
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return page_response(items[start:end], total, page, page_size)


@router.post("/", response_model=dict)
async def create_workflow(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建工作流定义"""
    # 检查编码唯一性
    existing = await db.execute(
        select(OaWorkflowDefinition).where(
            OaWorkflowDefinition.code == data.get("code"),
            OaWorkflowDefinition.is_deleted == False
        )
    )
    if existing.scalar_one_or_none():
        return {"code": 400, "message": f"工作流编码 '{data.get('code')}' 已存在"}

    # 创建工作流定义
    initial_status = "draft"
    if data.get("is_active"):
        initial_status = "published"
    
    definition = OaWorkflowDefinition(
        name=data.get("name"),
        code=data.get("code"),
        description=data.get("description", ""),
        business_type=data.get("business_type"),
        version=data.get("version", 1),
        status=initial_status,
        is_active=data.get("is_active", False),
        form_config=data.get("form_config"),
        allow_withdraw=data.get("allow_withdraw", True),
        allow_transfer=data.get("allow_transfer", True),
        allow_cc=data.get("allow_cc", True),
        published_by=current_user.id if data.get("is_active") else None,
        published_at=datetime.now() if data.get("is_active") else None,
    )
    db.add(definition)
    await db.flush()

    # 创建节点
    nodes_data = data.get("nodes", [])
    for idx, node_data in enumerate(nodes_data):
        approver_rule = node_data.get("approver_rule")
        config = node_data.get("config", {})

        node = OaWorkflowNode(
            definition_id=definition.id,
            name=node_data.get("name"),
            code=node_data.get("code"),
            node_type=node_data.get("node_type"),
            order_index=node_data.get("order_index", idx),
            approver_rule=approver_rule,
            config={
                "timeout_hours": config.get("timeout_hours", 0),
                "timeout_action": config.get("timeout_action", "NOTIFY"),
                "cc_type": config.get("cc_type"),
                "cc_user_ids": config.get("cc_user_ids", []),
                "condition_expression": config.get("condition_expression"),
            },
            timeout_hours=config.get("timeout_hours"),
            timeout_action=config.get("timeout_action"),
            condition_expression=config.get("condition_expression"),
        )
        db.add(node)

    await db.commit()
    await db.refresh(definition)

    return success({"id": str(definition.id)}, "工作流已创建")


@router.get("/{workflow_id}/", response_model=dict)
async def get_workflow_detail(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取工作流详情"""
    stmt = select(OaWorkflowDefinition).where(
        OaWorkflowDefinition.id == workflow_id,
        OaWorkflowDefinition.is_deleted == False
    )
    result = await db.execute(stmt)
    definition = result.scalar_one_or_none()

    if not definition:
        return {"code": 404, "message": "工作流不存在"}

    # 获取节点
    nodes_stmt = select(OaWorkflowNode).where(
        OaWorkflowNode.definition_id == workflow_id,
        OaWorkflowNode.is_deleted == False
    ).order_by(OaWorkflowNode.order_index)
    nodes_result = await db.execute(nodes_stmt)
    nodes = nodes_result.scalars().all()

    return success({
        "id": str(definition.id),
        "name": definition.name,
        "code": definition.code,
        "description": definition.description,
        "category": definition.business_type,
        "business_type": definition.business_type,
        "version": definition.version,
        "is_active": definition.is_active,
        "form_config": definition.form_config,
        "allow_withdraw": definition.allow_withdraw,
        "allow_transfer": definition.allow_transfer,
        "allow_cc": definition.allow_cc,
        "allow_urge": True,
        "allow_all_initiator": True,
        "allowed_roles": [],
        "allowed_departments": [],
        "nodes": [
            {
                "id": str(n.id),
                "name": n.name,
                "code": n.code,
                "node_type": n.node_type,
                "order_index": n.order_index,
                "approver_rule": n.approver_rule,
                "approver_type": n.approver_rule.get("type") if n.approver_rule else "USER",
                "approver_ids": n.approver_rule.get("user_ids", []) if n.approver_rule else [],
                "role_ids": n.approver_rule.get("role_ids", []) if n.approver_rule else [],
                "timeout_hours": n.timeout_hours or 0,
                "timeout_action": n.timeout_action or "NOTIFY",
                "condition_expression": n.condition_expression,
                "cc_type": n.config.get("cc_type") if n.config else None,
                "cc_user_ids": n.config.get("cc_user_ids", []) if n.config else [],
            }
            for n in nodes
        ],
        "created_at": definition.created_at.isoformat() if definition.created_at else None,
        "updated_at": definition.updated_at.isoformat() if definition.updated_at else None,
    })


@router.put("/{workflow_id}/", response_model=dict)
async def update_workflow(
    workflow_id: UUID,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新工作流定义"""
    stmt = select(OaWorkflowDefinition).where(
        OaWorkflowDefinition.id == workflow_id,
        OaWorkflowDefinition.is_deleted == False
    )
    result = await db.execute(stmt)
    definition = result.scalar_one_or_none()

    if not definition:
        return {"code": 404, "message": "工作流不存在"}

    # 更新基本字段
    if "name" in data:
        definition.name = data["name"]
    if "description" in data:
        definition.description = data["description"]
    if "business_type" in data:
        definition.business_type = data["business_type"]
    if "version" in data:
        definition.version = data["version"]
    if "status" in data:
        definition.status = data["status"]
        if data["status"] == "published":
            definition.is_active = True
            definition.published_by = current_user.id
            definition.published_at = datetime.now()
        elif data["status"] == "disabled":
            definition.is_active = False
        else:  # draft
            definition.is_active = False
    if "form_config" in data:
        definition.form_config = data["form_config"]
    if "allow_withdraw" in data:
        definition.allow_withdraw = data["allow_withdraw"]
    if "allow_transfer" in data:
        definition.allow_transfer = data["allow_transfer"]
    if "allow_cc" in data:
        definition.allow_cc = data["allow_cc"]

    # 更新节点
    if "nodes" in data:
        # 删除旧节点
        del_stmt = OaWorkflowNode.__table__.delete().where(
            OaWorkflowNode.definition_id == workflow_id
        )
        await db.execute(del_stmt)

        # 创建新节点
        for idx, node_data in enumerate(data["nodes"]):
            approver_rule = node_data.get("approver_rule")
            config = node_data.get("config", {})

            node = OaWorkflowNode(
                definition_id=definition.id,
                name=node_data.get("name"),
                code=node_data.get("code"),
                node_type=node_data.get("node_type"),
                order_index=node_data.get("order_index", idx),
                approver_rule=approver_rule,
                config={
                    "timeout_hours": config.get("timeout_hours", 0),
                    "timeout_action": config.get("timeout_action", "NOTIFY"),
                    "cc_type": config.get("cc_type"),
                    "cc_user_ids": config.get("cc_user_ids", []),
                    "condition_expression": config.get("condition_expression"),
                },
                timeout_hours=config.get("timeout_hours"),
                timeout_action=config.get("timeout_action"),
                condition_expression=config.get("condition_expression"),
            )
            db.add(node)

    await db.commit()
    await db.refresh(definition)

    return success({"id": str(definition.id)}, "工作流已更新")


@router.delete("/{workflow_id}/", response_model=dict)
async def delete_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除工作流定义"""
    stmt = select(OaWorkflowDefinition).where(
        OaWorkflowDefinition.id == workflow_id,
        OaWorkflowDefinition.is_deleted == False
    )
    result = await db.execute(stmt)
    definition = result.scalar_one_or_none()

    if not definition:
        return {"code": 404, "message": "工作流不存在"}

    definition.is_deleted = True
    await db.commit()

    return success({"id": str(workflow_id)}, "工作流已删除")


@router.post("/{workflow_id}/publish", response_model=dict)
async def publish_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发布工作流"""
    stmt = select(OaWorkflowDefinition).where(
        OaWorkflowDefinition.id == workflow_id,
        OaWorkflowDefinition.is_deleted == False
    )
    result = await db.execute(stmt)
    definition = result.scalar_one_or_none()

    if not definition:
        return {"code": 404, "message": "工作流不存在"}

    definition.status = "published"
    definition.is_active = True
    definition.published_by = current_user.id
    definition.published_at = datetime.now()

    await db.commit()
    await db.refresh(definition)

    return success({"id": str(definition.id)}, "工作流已发布")


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
    body: StartInstanceRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    发起审批流程

    请求体字段:
        workflow_id: str     工作流定义ID (UUID字符串)
        business_type: str   业务类型标识
        business_id: str     业务数据ID (UUID字符串)
        title: str           审批标题（必填）
        context: dict        表单数据
        cc_list: [str]       抄送用户ID列表
        summary: str          审批摘要
    """
    engine = WorkflowEngine(db)
    instance = await engine.start_instance(
        definition_id=UUID(body.workflow_id),
        business_type=body.business_type,
        business_id=UUID(body.business_id),
        initiator_id=current_user.id,
        title=body.title,
        form_data=body.context,
        cc_list=[UUID(uid) for uid in (body.cc_list or [])],
        summary=body.summary,
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
        transfer_to=UUID(target_user_id),   # ✅ 修正参数名
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
        delegate_to=UUID(delegate_to),      # ✅ 修正参数名
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


# ============================================================
# 催办
# ============================================================

class UrgeRequest(BaseModel):
    """催办请求体"""
    message: Optional[str] = "请尽快处理该审批申请"


@router.post("/instances/{instance_id}/urge", response_model=dict)
async def urge_instance(
    instance_id: UUID,
    body: UrgeRequest = Body(default=UrgeRequest()),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    催办审批实例（发起人专用）

    - 只有发起人可以催办
    - 实例状态必须为 PENDING 或 APPROVING
    - 每次催办给当前节点所有待处理审批人发送系统通知
    - 每小时最多催办1次（防刷机制）

    响应体:
        {
            "instance_id": "uuid-xxx",
            "urge_count": 2,
            "last_urge_at": "2026-05-09T10:30:00",
            "notified_users": 1
        }
    """
    engine = WorkflowEngine(db)
    urge_result = await engine.urge_instance(
        instance_id=instance_id,
        operator_id=current_user.id,
        message=body.message,
    )
    return success(urge_result, "催办成功")


# ============================================================
# 统计
# ============================================================

@router.get("/statistics", response_model=dict)
async def get_workflow_statistics(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    business_type: Optional[str] = Query(None, description="业务类型"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取工作流统计数据

    查询参数:
        start_date: 开始日期 (YYYY-MM-DD)，默认近30天
        end_date: 结束日期 (YYYY-MM-DD)，默认今天
        business_type: 按业务类型筛选

    响应体:
        {
            "summary": {
                "total": 156,           # 总申请数
                "approved": 98,         # 已通过数
                "rejected": 23,         # 已拒绝数
                "cancelled": 12,        # 已撤回数
                "in_progress": 23,      # 进行中数
                "approve_rate": 0.629,  # 通过率
                "avg_duration_hours": 18.5  # 平均审批时长
            },
            "by_type": [
                {
                    "business_type": "leave",
                    "total": 45,
                    "approved": 40,
                    "rejected": 3,
                    "approve_rate": 0.930
                }
            ]
        }
    """
    from datetime import datetime as dt

    # 解析日期参数
    parsed_start = None
    parsed_end = None
    if start_date:
        try:
            parsed_start = dt.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            return {"code": 400, "message": "start_date 格式错误，请使用 YYYY-MM-DD"}
    if end_date:
        try:
            parsed_end = dt.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return {"code": 400, "message": "end_date 格式错误，请使用 YYYY-MM-DD"}

    engine = WorkflowEngine(db)
    result = await engine.get_statistics(
        start_date=parsed_start,
        end_date=parsed_end,
        business_type=business_type,
    )
    return success(result)