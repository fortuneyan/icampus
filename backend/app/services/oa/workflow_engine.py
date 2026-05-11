"""
OA工作流引擎核心

负责审批流程的启动、节点流转、审批操作等核心逻辑
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, update, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.oa import (
    OaWorkflowDefinition,
    OaWorkflowNode,
    OaWorkflowInstance,
    OaWorkflowTask,
    OaWorkflowVariable,
    OaWorkflowCC,
)
from app.models import User, Notification
from app.core.exceptions import BusinessException, ErrorCode, NotFoundException, ForbiddenException
from app.services.oa.approver_resolver import ApproverResolver
from app.services.oa.business_callbacks import BusinessCallbackRegistry
from app.services.oa.condition_evaluator import ConditionEvaluator


class WorkflowEngine:
    """工作流引擎"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.approver_resolver = ApproverResolver(db)
        self.condition_evaluator = ConditionEvaluator()

    # ========================================================================
    # 流程启动
    # ========================================================================

    async def start_instance(
        self,
        definition_id: UUID,
        business_type: str,
        business_id: UUID,
        initiator_id: UUID,
        title: str,
        form_data: Optional[Dict[str, Any]] = None,
        cc_list: Optional[List[UUID]] = None,
        summary: Optional[str] = None,
    ) -> OaWorkflowInstance:
        """
        启动一个新的审批流程实例

        Args:
            definition_id: 工作流定义ID
            business_type: 业务类型
            business_id: 业务数据ID
            initiator_id: 发起人ID
            title: 审批标题
            form_data: 表单数据
            cc_list: 抄送用户列表
            summary: 审批摘要

        Returns:
            创建的审批实例
        """
        # 检查业务数据是否已有进行中的审批
        existing = await self._check_existing_instance(business_type, business_id)
        if existing:
            raise BusinessException(
                ErrorCode.DUPLICATE_RESOURCE,
                f"业务数据 {business_id} 已有进行中的审批流程"
            )

        # 获取工作流定义
        definition = await self._get_definition(definition_id)
        if definition.status != "published":
            raise BusinessException(ErrorCode.INVALID_OPERATION, "工作流未发布或已禁用")

        # 获取发起人信息
        initiator = await self._get_user(initiator_id)
        if not initiator:
            raise NotFoundException("发起人不存在")

        # 创建审批实例
        instance = OaWorkflowInstance(
            definition_id=definition_id,
            business_type=business_type,
            business_id=business_id,
            initiator_id=initiator_id,
            title=title,
            summary=summary,
            form_data=form_data,
            status="PENDING",
            submitted_at=datetime.now(),
        )
        self.db.add(instance)
        await self.db.flush()

        # 保存流程变量
        if form_data:
            for key, value in form_data.items():
                variable = OaWorkflowVariable(
                    instance_id=instance.id,
                    name=key,
                    value=str(value) if value is not None else None,
                    value_type=self._get_value_type(value),
                    source="FORM",
                )
                self.db.add(variable)

        # 获取起始节点并启动流程
        start_node = await self._get_start_node(definition_id)
        if not start_node:
            raise BusinessException(ErrorCode.WORKFLOW_NODE_NOT_FOUND, "未找到起始节点")

        # 保存已完成的节点
        instance.completed_node_ids = []

        # 移动到下一个审批节点
        await self._move_to_next_node(instance, start_node)

        # 创建抄送记录
        if cc_list:
            await self._create_cc_records(instance, cc_list)

        await self.db.commit()
        await self.db.refresh(instance)

        # 发送通知给第一个审批人
        await self._notify_assignees(instance)

        return instance

    async def _check_existing_instance(
        self, 
        business_type: str, 
        business_id: UUID
    ) -> Optional[OaWorkflowInstance]:
        """检查是否已有进行中的审批实例"""
        stmt = select(OaWorkflowInstance).where(
            and_(
                OaWorkflowInstance.business_type == business_type,
                OaWorkflowInstance.business_id == business_id,
                OaWorkflowInstance.status.in_(["PENDING", "APPROVING"]),
                OaWorkflowInstance.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_definition(self, definition_id: UUID) -> OaWorkflowDefinition:
        """获取工作流定义"""
        stmt = select(OaWorkflowDefinition).where(
            and_(
                OaWorkflowDefinition.id == definition_id,
                OaWorkflowDefinition.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        definition = result.scalar_one_or_none()
        if not definition:
            raise NotFoundException("工作流定义不存在", ErrorCode.WORKFLOW_NOT_FOUND)
        return definition

    async def _get_start_node(self, definition_id: UUID) -> Optional[OaWorkflowNode]:
        """获取起始节点"""
        stmt = select(OaWorkflowNode).where(
            and_(
                OaWorkflowNode.definition_id == definition_id,
                OaWorkflowNode.node_type == "START",
                OaWorkflowNode.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_user(self, user_id: UUID) -> Optional[User]:
        """获取用户"""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def _get_value_type(self, value: Any) -> str:
        """推断变量值类型"""
        if isinstance(value, bool):
            return "BOOLEAN"
        elif isinstance(value, (int, float)):
            return "NUMBER"
        elif isinstance(value, datetime):
            return "DATE"
        elif isinstance(value, (dict, list)):
            return "JSON"
        return "STRING"

    # ========================================================================
    # 节点流转
    # ========================================================================

    async def _move_to_next_node(
        self,
        instance: OaWorkflowInstance,
        current_node: OaWorkflowNode
    ) -> Optional[OaWorkflowNode]:
        """
        将流程移动到下一个节点

        Args:
            instance: 审批实例
            current_node: 当前节点

        Returns:
            下一个节点，如果没有则返回None
        """
        # 获取下一个节点
        next_node = await self._get_next_node(
            instance.definition_id, 
            current_node.order_index,
            instance.form_data or {}
        )

        if not next_node:
            # 没有下一个节点，流程结束
            await self._complete_instance(instance)
            return None

        # 更新实例状态
        instance.current_node_id = next_node.id
        instance.completed_node_ids = instance.completed_node_ids or []
        instance.completed_node_ids.append(str(current_node.id))
        instance.status = "APPROVING"
        instance.started_at = instance.started_at or datetime.now()

        # 处理不同类型的节点
        if next_node.node_type == "END":
            await self._complete_instance(instance)
            return next_node

        elif next_node.node_type == "APPROVAL":
            # 创建审批任务
            await self._create_approval_task(instance, next_node)

        elif next_node.node_type == "CC":
            # 创建抄送任务
            await self._create_cc_task(instance, next_node)

        elif next_node.node_type == "AUTO":
            # 自动执行节点动作
            await self._execute_auto_node(instance, next_node)
            # 递归移动到下一个节点
            return await self._move_to_next_node(instance, next_node)

        elif next_node.node_type == "CONDITION":
            # 条件节点，根据条件决定路由
            condition_result = await self._evaluate_condition(
                next_node, 
                instance.form_data or {}
            )
            if condition_result:
                return await self._move_to_next_node(instance, next_node)

        return next_node

    async def _get_next_node(
        self,
        definition_id: UUID,
        current_order: int,
        form_data: Dict[str, Any]
    ) -> Optional[OaWorkflowNode]:
        """获取下一个节点"""
        stmt = select(OaWorkflowNode).where(
            and_(
                OaWorkflowNode.definition_id == definition_id,
                OaWorkflowNode.order_index > current_order,
                OaWorkflowNode.is_deleted == False
            )
        ).order_by(OaWorkflowNode.order_index)
        
        result = await self.db.execute(stmt)
        nodes = result.scalars().all()
        
        # 简单实现：返回第一个节点
        # 复杂实现：需要处理CONDITION节点的条件判断
        for node in nodes:
            if node.node_type == "CONDITION":
                # 评估条件
                if await self._evaluate_condition(node, form_data):
                    # 获取条件为true的分支节点
                    return await self._get_condition_branch_node(node, True)
            else:
                return node
        
        return None

    async def _get_condition_branch_node(
        self,
        condition_node: OaWorkflowNode,
        branch: bool
    ) -> Optional[OaWorkflowNode]:
        """获取条件节点的分支节点"""
        config = condition_node.config or {}
        target_order = condition_node.order_index + (1 if branch else 2)
        
        stmt = select(OaWorkflowNode).where(
            and_(
                OaWorkflowNode.definition_id == condition_node.definition_id,
                OaWorkflowNode.order_index == target_order,
                OaWorkflowNode.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _evaluate_condition(
        self,
        node: OaWorkflowNode,
        form_data: Dict[str, Any]
    ) -> bool:
        """
        评估条件节点表达式（委托给 ConditionEvaluator）

        支持：
        - 简单三段式: "field op value"
        - JSON结构: {"op": "AND/OR", "conditions": [...]}
        - 字段路径: "form.amount" 或嵌套 "data.config.threshold"
        """
        return self.condition_evaluator.evaluate(
            expression=node.condition_expression,
            context=form_data,
        )

    async def _create_approval_task(
        self,
        instance: OaWorkflowInstance,
        node: OaWorkflowNode
    ) -> Optional[OaWorkflowTask]:
        """创建审批任务"""
        # 解析审批人
        context = {
            "initiator_id": instance.initiator_id,
            "business_data": instance.form_data,
        }
        
        approver_ids = await self.approver_resolver.resolve_node_approvers(
            {
                "approver_rule": node.approver_rule
            },
            context
        )

        if not approver_ids:
            # 没有审批人，可能需要配置错误处理
            raise BusinessException(
                ErrorCode.WORKFLOW_NO_APPROVER,
                f"节点 {node.name} 未配置审批人"
            )

        # 计算截止时间
        deadline = None
        if node.timeout_hours:
            deadline = datetime.now() + timedelta(hours=node.timeout_hours)

        # 为每个审批人创建任务
        tasks = []
        for idx, approver_id in enumerate(approver_ids):
            task = OaWorkflowTask(
                instance_id=instance.id,
                node_id=node.id,
                task_type="APPROVAL",
                status="PENDING",
                assignee_id=approver_id,
                assignee_type="USER",
                assigned_at=datetime.now(),
                deadline=deadline,
                order_index=idx,
                is_required=node.is_required,
            )
            self.db.add(task)
            tasks.append(task)

        return tasks[0] if tasks else None

    async def _create_cc_task(
        self,
        instance: OaWorkflowInstance,
        node: OaWorkflowNode
    ) -> Optional[OaWorkflowCC]:
        """创建抄送任务"""
        # 解析抄送人
        context = {
            "initiator_id": instance.initiator_id,
            "business_data": instance.form_data,
        }
        
        cc_user_ids = await self.approver_resolver.resolve_node_approvers(
            {
                "approver_rule": node.approver_rule
            },
            context
        )

        if cc_user_ids:
            await self._create_cc_records(instance, cc_user_ids)

        return None

    async def _execute_auto_node(
        self,
        instance: OaWorkflowInstance,
        node: OaWorkflowNode
    ) -> None:
        """执行自动节点"""
        config = node.config or {}
        action = config.get("action")
        
        # 执行自动动作
        if action == "set_variable":
            # 设置变量
            var_name = config.get("var_name")
            var_value = config.get("var_value")
            if var_name:
                variable = OaWorkflowVariable(
                    instance_id=instance.id,
                    name=var_name,
                    value=str(var_value),
                    value_type="STRING",
                    source="AUTO",
                    node_id=node.id,
                )
                self.db.add(variable)

    async def _complete_instance(self, instance: OaWorkflowInstance) -> None:
        """完成审批流程"""
        instance.status = "APPROVED"
        instance.completed_at = datetime.now()
        
        # 调用业务回调
        await self._on_instance_completed(instance, "APPROVED")

    # ========================================================================
    # 审批操作
    # ========================================================================

    async def handle_task(
        self,
        task_id: UUID,
        action: str,
        operator_id: UUID,
        comment: Optional[str] = None,
        transfer_to: Optional[UUID] = None,
        delegate_to: Optional[UUID] = None,
    ) -> OaWorkflowTask:
        """
        处理审批任务

        Args:
            task_id: 任务ID
            action: 操作类型 (APPROVE/REJECT/TRANSFER/DELEGATE)
            operator_id: 操作人ID
            comment: 审批意见
            transfer_to: 转交给谁
            delegate_to: 代理给谁

        Returns:
            更新后的任务
        """
        # 获取任务
        task = await self._get_task(task_id)
        if not task:
            raise NotFoundException("任务不存在", ErrorCode.WORKFLOW_TASK_NOT_FOUND)

        # 验证操作权限
        if task.assignee_id != operator_id:
            raise ForbiddenException("您不是此任务的审批人")

        # 检查任务状态
        if task.status != "PENDING":
            raise BusinessException(
                ErrorCode.INVALID_OPERATION,
                f"任务状态已变更，无法{self._get_action_name(action)}"
            )

        # 执行操作
        if action == "APPROVE":
            await self._approve_task(task, comment)
        elif action == "REJECT":
            await self._reject_task(task, comment)
        elif action == "TRANSFER":
            if not transfer_to:
                raise BusinessException(ErrorCode.VALIDATION_ERROR, "转交目标用户不能为空")
            await self._transfer_task(task, transfer_to, operator_id, comment)
        elif action == "DELEGATE":
            if not delegate_to:
                raise BusinessException(ErrorCode.VALIDATION_ERROR, "代理目标用户不能为空")
            await self._delegate_task(task, delegate_to, operator_id, comment)
        else:
            raise BusinessException(ErrorCode.VALIDATION_ERROR, f"不支持的操作类型: {action}")

        await self.db.commit()
        await self.db.refresh(task)
        
        return task

    async def _approve_task(
        self,
        task: OaWorkflowTask,
        comment: Optional[str]
    ) -> None:
        """审批通过"""
        task.status = "APPROVED"
        task.action = "APPROVE"
        task.comment = comment
        task.completed_at = datetime.now()
        task.started_at = task.started_at or datetime.now()

        # 获取实例和当前节点
        instance = await self._get_instance(task.instance_id)
        node = await self._get_node(task.node_id)

        # 移动到下一个节点
        await self._move_to_next_node(instance, node)

        # 记录审批意见
        self._record_approval_summary(instance, task, "APPROVED", comment)

    async def _reject_task(
        self,
        task: OaWorkflowTask,
        comment: Optional[str]
    ) -> None:
        """审批拒绝"""
        task.status = "REJECTED"
        task.action = "REJECT"
        task.comment = comment
        task.completed_at = datetime.now()
        task.started_at = task.started_at or datetime.now()

        # 更新实例状态
        instance = await self._get_instance(task.instance_id)
        instance.status = "REJECTED"
        instance.completed_at = datetime.now()

        # 记录审批意见
        self._record_approval_summary(instance, task, "REJECTED", comment)

        # 调用业务回调
        await self._on_instance_completed(instance, "REJECTED")

    async def _transfer_task(
        self,
        task: OaWorkflowTask,
        transfer_to: UUID,
        transfer_by: UUID,
        comment: Optional[str]
    ) -> None:
        """转交任务"""
        # 验证目标用户
        target_user = await self._get_user(transfer_to)
        if not target_user:
            raise NotFoundException("转交目标用户不存在")

        # 创建新任务
        new_task = OaWorkflowTask(
            instance_id=task.instance_id,
            node_id=task.node_id,
            task_type="APPROVAL",
            status="PENDING",
            assignee_id=transfer_to,
            assignee_type="USER",
            original_assignee_id=transfer_by,
            assigned_at=datetime.now(),
            deadline=task.deadline,
            order_index=task.order_index,
            is_required=task.is_required,
        )
        
        # 更新原任务
        task.status = "TRANSFERRED"
        task.action = "TRANSFER"
        task.transfer_from = transfer_by
        task.transfer_to = transfer_to
        task.transfer_reason = comment
        task.completed_at = datetime.now()

        self.db.add(new_task)

    async def _delegate_task(
        self,
        task: OaWorkflowTask,
        delegate_to: UUID,
        delegate_by: UUID,
        comment: Optional[str]
    ) -> None:
        """代理任务"""
        # 验证目标用户
        target_user = await self._get_user(delegate_to)
        if not target_user:
            raise NotFoundException("代理目标用户不存在")

        # 更新任务
        task.assignee_id = delegate_to
        task.delegate_from = delegate_by
        task.delegate_to = delegate_to
        task.action = "DELEGATE"
        task.comment = comment

    def _record_approval_summary(
        self,
        instance: OaWorkflowInstance,
        task: OaWorkflowTask,
        action: str,
        comment: Optional[str]
    ) -> None:
        """记录审批意见汇总"""
        summary = instance.approval_summary or []
        summary.append({
            "task_id": str(task.id),
            "node_id": str(task.node_id),
            "assignee_id": str(task.assignee_id),
            "action": action,
            "comment": comment,
            "completed_at": datetime.now().isoformat(),
        })
        instance.approval_summary = summary

    def _get_action_name(self, action: str) -> str:
        """获取操作名称（同步方法，用于 f-string 和异常消息）"""
        action_names = {
            "APPROVE": "审批",
            "REJECT": "拒绝",
            "TRANSFER": "转交",
            "DELEGATE": "代理",
        }
        return action_names.get(action, action)

    # ========================================================================
    # 流程撤回
    # ========================================================================

    async def cancel_instance(
        self,
        instance_id: UUID,
        operator_id: UUID,
        reason: Optional[str] = None
    ) -> OaWorkflowInstance:
        """
        撤回审批流程（仅发起人可操作）

        Args:
            instance_id: 实例ID
            operator_id: 操作人ID
            reason: 撤回原因

        Returns:
            更新后的实例
        """
        instance = await self._get_instance(instance_id)
        if not instance:
            raise NotFoundException("审批流程不存在", ErrorCode.WORKFLOW_INSTANCE_NOT_FOUND)

        # 验证权限
        if instance.initiator_id != operator_id:
            raise ForbiddenException("只有发起人可以撤回审批")

        # 检查状态
        if instance.status not in ["PENDING", "APPROVING"]:
            raise BusinessException(
                ErrorCode.WORKFLOW_CANNOT_WITHDRAW,
                "当前状态不允许撤回"
            )

        # 检查是否允许撤回
        definition = await self._get_definition(instance.definition_id)
        if not definition.allow_withdraw:
            raise BusinessException(
                ErrorCode.WORKFLOW_CANNOT_WITHDRAW,
                "此工作流不允许撤回"
            )

        # 更新实例状态
        instance.status = "CANCELLED"
        instance.cancelled_at = datetime.now()
        instance.cancel_reason = reason

        # 取消待处理的任务
        await self._cancel_pending_tasks(instance_id)

        await self.db.commit()
        await self.db.refresh(instance)

        return instance

    async def _cancel_pending_tasks(self, instance_id: UUID) -> None:
        """取消待处理的任务"""
        stmt = update(OaWorkflowTask).where(
            and_(
                OaWorkflowTask.instance_id == instance_id,
                OaWorkflowTask.status == "PENDING",
                OaWorkflowTask.is_deleted == False
            )
        ).values(status="CANCELLED")
        await self.db.execute(stmt)

    # ========================================================================
    # 催办
    # ========================================================================

    async def urge_instance(
        self,
        instance_id: UUID,
        operator_id: UUID,
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        催办审批实例

        给当前节点所有待处理审批人发送系统通知，并记录催办次数。

        Args:
            instance_id: 审批实例ID
            operator_id: 操作人ID（必须是发起人）
            message: 催办消息（默认："请尽快处理该审批申请"）

        Returns:
            {
                "instance_id": str,
                "urge_count": int,       # 本次催办后的累计催办次数
                "last_urge_at": str,     # ISO8601 格式的最后催办时间
                "notified_users": int,   # 本次被通知的审批人数量
            }

        Raises:
            NotFoundException: 实例不存在
            ForbiddenException: 非发起人操作
            BusinessException(INVALID_OPERATION): 审批已结束，无法催办
            BusinessException(RATE_LIMIT_EXCEEDED): 距上次催办不足1小时
        """
        import logging as _logging
        _logger = _logging.getLogger(__name__)

        instance = await self._get_instance(instance_id)
        if not instance:
            raise NotFoundException("审批实例不存在", ErrorCode.WORKFLOW_INSTANCE_NOT_FOUND)

        # 权限验证：只有发起人可以催办
        if instance.initiator_id != operator_id:
            raise ForbiddenException("只有发起人可以催办")

        # 状态验证：只有进行中的实例可以催办
        if instance.status not in ["PENDING", "APPROVING"]:
            raise BusinessException(
                ErrorCode.INVALID_OPERATION,
                "审批已结束，无法催办"
            )

        # 防频繁催办：距上次催办不足1小时
        if instance.last_urge_at:
            elapsed = (datetime.now() - instance.last_urge_at).total_seconds()
            if elapsed < 3600:  # 1小时 = 3600秒
                remaining = int((3600 - elapsed) / 60)
                raise BusinessException(
                    ErrorCode.RATE_LIMIT_EXCEEDED,
                    f"催办过于频繁，请 {remaining} 分钟后再试"
                )

        # 查找当前节点的待处理任务
        stmt = select(OaWorkflowTask).where(
            and_(
                OaWorkflowTask.instance_id == instance_id,
                OaWorkflowTask.status == "PENDING",
                OaWorkflowTask.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        pending_tasks = result.scalars().all()

        # 给每个待处理审批人发系统通知（记录催办并更新任务催办次数）
        notified_count = 0
        urge_message = message or "请尽快处理该审批申请"
        for task in pending_tasks:
            if task.assignee_id:
                # 更新任务的催办提醒次数
                task.overdue_reminders = (task.overdue_reminders or 0) + 1
                notified_count += 1
                _logger.info(
                    "[WorkflowUrge] Notified assignee: task_id=%s, assignee_id=%s, msg=%s",
                    task.id,
                    task.assignee_id,
                    urge_message,
                )

        # 更新实例的催办记录
        now = datetime.now()
        instance.last_urge_at = now
        instance.urge_count = (instance.urge_count or 0) + 1

        await self.db.commit()

        _logger.info(
            "[WorkflowUrge] instance_id=%s, urge_count=%s, notified=%s",
            instance_id,
            instance.urge_count,
            notified_count,
        )

        return {
            "instance_id": str(instance_id),
            "urge_count": instance.urge_count,
            "last_urge_at": now.isoformat(),
            "notified_users": notified_count,
        }

    # ========================================================================
    # 抄送处理
    # ========================================================================

    async def _create_cc_records(
        self,
        instance: OaWorkflowInstance,
        cc_user_ids: List[UUID]
    ) -> List[OaWorkflowCC]:
        """创建抄送记录"""
        records = []
        for user_id in cc_user_ids:
            record = OaWorkflowCC(
                instance_id=instance.id,
                cc_user_id=user_id,
                cc_at=datetime.now(),
            )
            self.db.add(record)
            records.append(record)
        return records

    async def mark_cc_read(self, cc_id: UUID, user_id: UUID) -> OaWorkflowCC:
        """标记抄送已读"""
        stmt = select(OaWorkflowCC).where(
            and_(
                OaWorkflowCC.id == cc_id,
                OaWorkflowCC.cc_user_id == user_id,
                OaWorkflowCC.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        cc_record = result.scalar_one_or_none()
        
        if not cc_record:
            raise NotFoundException("抄送记录不存在")

        cc_record.is_read = True
        cc_record.read_at = datetime.now()
        
        await self.db.commit()
        await self.db.refresh(cc_record)
        
        return cc_record

    # ========================================================================
    # 通知
    # ========================================================================

    async def _notify_assignees(self, instance: OaWorkflowInstance) -> None:
        """通知审批人有新任务"""
        # 查询待处理的任务
        stmt = select(OaWorkflowTask).where(
            and_(
                OaWorkflowTask.instance_id == instance.id,
                OaWorkflowTask.status == "PENDING",
                OaWorkflowTask.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        tasks = result.scalars().all()

        # 为每个任务的审批人创建通知
        for task in tasks:
            if task.assignee_id:
                notification = Notification(
                    user_id=task.assignee_id,
                    title="新的审批任务",
                    content=f"您有一个新的审批任务：{instance.title}",
                    type="WORKFLOW_TASK",
                    related_id=str(instance.id),
                    created_at=datetime.now(),
                )
                self.db.add(notification)

    # ========================================================================
    # 业务回调
    # ========================================================================

    async def _on_instance_completed(
        self,
        instance: OaWorkflowInstance,
        result: str
    ) -> None:
        """
        审批完成后调用业务回调（策略模式）

        Args:
            instance: 审批实例（status 已更新为 APPROVED 或 REJECTED）
            result: 结果 "APPROVED" | "REJECTED"

        注意：
            - 回调失败不影响主流程，异常会被捕获并记录日志
            - 新业务类型在应用启动时注册到 BusinessCallbackRegistry
        """
        import logging as _logging
        _logger = _logging.getLogger(__name__)

        registry = BusinessCallbackRegistry.instance()
        handler = registry.get_handler(instance.business_type, self.db)

        try:
            if result == "APPROVED":
                await handler.on_approved(instance)
            elif result == "REJECTED":
                await handler.on_rejected(instance)
        except Exception as e:
            _logger.error(
                "[WorkflowCallback] Error in business callback: "
                "business_type=%s, instance_id=%s, error=%s",
                instance.business_type,
                instance.id,
                e,
                exc_info=True,
            )

    # ========================================================================
    # 查询方法
    # ========================================================================

    async def get_instance_detail(self, instance_id: UUID) -> Dict[str, Any]:
        """获取审批实例详情"""
        stmt = (
            select(OaWorkflowInstance)
            .options(
                selectinload(OaWorkflowInstance.definition),
                selectinload(OaWorkflowInstance.tasks),
                selectinload(OaWorkflowInstance.initiator),
            )
            .where(
                and_(
                    OaWorkflowInstance.id == instance_id,
                    OaWorkflowInstance.is_deleted == False
                )
            )
        )
        result = await self.db.execute(stmt)
        instance = result.scalar_one_or_none()
        
        if not instance:
            raise NotFoundException("审批实例不存在", ErrorCode.WORKFLOW_INSTANCE_NOT_FOUND)

        # 获取变量
        stmt = select(OaWorkflowVariable).where(
            OaWorkflowVariable.instance_id == instance_id
        )
        result = await self.db.execute(stmt)
        variables = result.scalars().all()

        # 构建响应
        return {
            "id": instance.id,
            "title": instance.title,
            "status": instance.status,
            "definition": {
                "id": instance.definition.id,
                "name": instance.definition.name,
                "code": instance.definition.code,
            } if instance.definition else None,
            "initiator": {
                "id": instance.initiator.id,
                "name": instance.initiator.real_name,
            } if instance.initiator else None,
            "business_type": instance.business_type,
            "business_id": instance.business_id,
            "form_data": instance.form_data,
            "current_node_id": instance.current_node_id,
            "tasks": [
                {
                    "id": task.id,
                    "node_id": task.node_id,
                    "task_type": task.task_type,
                    "status": task.status,
                    "assignee_id": task.assignee_id,
                    "action": task.action,
                    "comment": task.comment,
                    "completed_at": task.completed_at,
                }
                for task in instance.tasks
            ],
            "variables": [
                {
                    "name": var.name,
                    "value": var.value,
                    "value_type": var.value_type,
                }
                for var in variables
            ],
            "submitted_at": instance.submitted_at,
            "completed_at": instance.completed_at,
        }

    async def get_pending_tasks(self, user_id: UUID) -> List[OaWorkflowTask]:
        """获取用户的待审批任务"""
        stmt = (
            select(OaWorkflowTask)
            .options(selectinload(OaWorkflowTask.instance))
            .where(
                and_(
                    OaWorkflowTask.assignee_id == user_id,
                    OaWorkflowTask.status == "PENDING",
                    OaWorkflowTask.is_deleted == False
                )
            )
            .order_by(OaWorkflowTask.assigned_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_my_applications(
        self,
        user_id: UUID,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[OaWorkflowInstance], int]:
        """获取我发起的审批"""
        query = (
            select(OaWorkflowInstance)
            .options(selectinload(OaWorkflowInstance.definition))
            .where(
                and_(
                    OaWorkflowInstance.initiator_id == user_id,
                    OaWorkflowInstance.is_deleted == False
                )
            )
        )
        
        if status:
            query = query.where(OaWorkflowInstance.status == status)
        
        # 统计总数
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # 分页
        query = query.order_by(OaWorkflowInstance.submitted_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        instances = list(result.scalars().all())
        
        return instances, total

    async def get_my_cc_records(
        self,
        user_id: UUID,
        is_read: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[OaWorkflowCC], int]:
        """获取抄送给我的记录"""
        query = (
            select(OaWorkflowCC)
            .options(selectinload(OaWorkflowCC.instance))
            .where(
                and_(
                    OaWorkflowCC.cc_user_id == user_id,
                    OaWorkflowCC.is_deleted == False
                )
            )
        )
        
        if is_read is not None:
            query = query.where(OaWorkflowCC.is_read == is_read)
        
        # 统计总数
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # 分页
        query = query.order_by(OaWorkflowCC.cc_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        records = list(result.scalars().all())
        
        return records, total

    # ========================================================================
    # 辅助方法
    # ========================================================================

    async def _get_task(self, task_id: UUID) -> Optional[OaWorkflowTask]:
        """获取任务"""
        stmt = select(OaWorkflowTask).where(
            and_(
                OaWorkflowTask.id == task_id,
                OaWorkflowTask.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_instance(self, instance_id: UUID) -> Optional[OaWorkflowInstance]:
        """获取实例"""
        stmt = select(OaWorkflowInstance).where(
            and_(
                OaWorkflowInstance.id == instance_id,
                OaWorkflowInstance.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_node(self, node_id: UUID) -> Optional[OaWorkflowNode]:
        """获取节点"""
        stmt = select(OaWorkflowNode).where(
            and_(
                OaWorkflowNode.id == node_id,
                OaWorkflowNode.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ========================================================================
    # API 路由需要的方法
    # ========================================================================

    async def get_definitions(self) -> List[OaWorkflowDefinition]:
        """获取工作流定义列表"""
        stmt = select(OaWorkflowDefinition).where(
            OaWorkflowDefinition.is_deleted == False
        ).order_by(OaWorkflowDefinition.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_my_instances(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取我的申请列表"""
        query = (
            select(OaWorkflowInstance)
            .options(selectinload(OaWorkflowInstance.definition))
            .where(
                and_(
                    OaWorkflowInstance.initiator_id == user_id,
                    OaWorkflowInstance.is_deleted == False
                )
            )
        )

        if status:
            query = query.where(OaWorkflowInstance.status == status)

        # 统计总数
        count_query = select(func.count()).select_from(
            select(OaWorkflowInstance).where(
                and_(
                    OaWorkflowInstance.initiator_id == user_id,
                    OaWorkflowInstance.is_deleted == False,
                    OaWorkflowInstance.status == status if status else True
                )
            ).subquery()
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # 分页
        query = query.order_by(OaWorkflowInstance.submitted_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        instances = result.scalars().all()

        items = [
            {
                "id": str(inst.id),
                "title": inst.title,
                "status": inst.status,
                "definition_name": inst.definition.name if inst.definition else None,
                "business_type": inst.business_type,
                "submitted_at": inst.submitted_at.isoformat() if inst.submitted_at else None,
                "completed_at": inst.completed_at.isoformat() if inst.completed_at else None,
            }
            for inst in instances
        ]

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    async def get_my_pending_tasks(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """获取待我审批的任务"""
        query = (
            select(OaWorkflowTask)
            .options(selectinload(OaWorkflowTask.instance))
            .where(
                and_(
                    OaWorkflowTask.assignee_id == user_id,
                    OaWorkflowTask.status == "PENDING",
                    OaWorkflowTask.is_deleted == False
                )
            )
        )

        # 统计总数
        count_query = select(func.count()).select_from(
            select(OaWorkflowTask).where(
                and_(
                    OaWorkflowTask.assignee_id == user_id,
                    OaWorkflowTask.status == "PENDING",
                    OaWorkflowTask.is_deleted == False
                )
            ).subquery()
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # 分页
        query = query.order_by(OaWorkflowTask.assigned_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        tasks = result.scalars().all()

        items = [
            {
                "id": str(task.id),
                "instance_id": str(task.instance_id),
                "node_id": str(task.node_id),
                "task_type": task.task_type,
                "status": task.status,
                "title": task.instance.title if task.instance else None,
                "assignee_id": str(task.assignee_id),
                "assigned_at": task.assigned_at.isoformat() if task.assigned_at else None,
                "deadline": task.deadline.isoformat() if task.deadline else None,
            }
            for task in tasks
        ]

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    async def get_my_cc(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """获取抄送给我的"""
        query = (
            select(OaWorkflowCC)
            .options(selectinload(OaWorkflowCC.instance))
            .where(
                and_(
                    OaWorkflowCC.cc_user_id == user_id,
                    OaWorkflowCC.is_deleted == False
                )
            )
        )

        # 统计总数
        count_query = select(func.count()).select_from(
            select(OaWorkflowCC).where(
                and_(
                    OaWorkflowCC.cc_user_id == user_id,
                    OaWorkflowCC.is_deleted == False
                )
            ).subquery()
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # 分页
        query = query.order_by(OaWorkflowCC.cc_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        records = result.scalars().all()

        items = [
            {
                "id": str(record.id),
                "instance_id": str(record.instance_id),
                "title": record.instance.title if record.instance else None,
                "is_read": record.is_read,
                "cc_at": record.cc_at.isoformat() if record.cc_at else None,
            }
            for record in records
        ]

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    # ========================================================================
    # 统计接口
    # ========================================================================

    async def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        business_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取工作流统计数据

        Args:
            start_date: 开始时间（默认: 30天前）
            end_date: 结束时间（默认: 现在）
            business_type: 业务类型过滤

        Returns:
            {
                "summary": {
                    "total": int,              # 总申请数
                    "approved": int,           # 已通过数
                    "rejected": int,           # 已拒绝数
                    "cancelled": int,          # 已撤回数
                    "in_progress": int,        # 进行中数
                    "approve_rate": float,     # 通过率 0.0 ~ 1.0
                    "avg_duration_hours": float | None,  # 平均审批时长(小时)
                },
                "by_type": [
                    {
                        "business_type": str,
                        "total": int,
                        "approved": int,
                        "rejected": int,
                        "approve_rate": float,
                    }
                ]
            }
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        # 构建基础查询条件
        base_conditions = [
            OaWorkflowInstance.submitted_at >= start_date,
            OaWorkflowInstance.submitted_at <= end_date,
            OaWorkflowInstance.is_deleted == False,
        ]
        if business_type:
            base_conditions.append(OaWorkflowInstance.business_type == business_type)

        # 1. 总体汇总
        total_stmt = select(func.count()).select_from(
            select(OaWorkflowInstance).where(and_(*base_conditions)).subquery()
        )
        total = (await self.db.execute(total_stmt)).scalar() or 0

        # 按状态统计
        status_stmt = select(
            OaWorkflowInstance.status,
            func.count().label("cnt")
        ).where(and_(*base_conditions)).group_by(OaWorkflowInstance.status)
        status_result = await self.db.execute(status_stmt)
        status_counts = {row[0]: row[1] for row in status_result.fetchall()}

        approved = status_counts.get("APPROVED", 0)
        rejected = status_counts.get("REJECTED", 0)
        cancelled = status_counts.get("CANCELLED", 0)
        in_progress = status_counts.get("APPROVING", 0) + status_counts.get("PENDING", 0)

        approve_rate = round(approved / (approved + rejected), 3) if (approved + rejected) > 0 else 0

        # 平均审批时长（小时）
        duration_stmt = select(
            func.avg(
                func.extract("epoch", OaWorkflowInstance.completed_at - OaWorkflowInstance.submitted_at) / 3600
            )
        ).where(
            and_(
                *base_conditions,
                OaWorkflowInstance.status.in_(["APPROVED", "REJECTED"]),
                OaWorkflowInstance.completed_at.isnot(None)
            )
        )
        avg_duration = (await self.db.execute(duration_stmt)).scalar()

        # 2. 按业务类型分组
        by_type_stmt = select(
            OaWorkflowInstance.business_type,
            func.count().label("total"),
            func.sum(func.case((OaWorkflowInstance.status == "APPROVED", 1), else_=0)).label("approved"),
            func.sum(func.case((OaWorkflowInstance.status == "REJECTED", 1), else_=0)).label("rejected"),
        ).where(and_(*base_conditions)).group_by(OaWorkflowInstance.business_type)
        by_type_result = await self.db.execute(by_type_stmt)

        by_type = []
        for row in by_type_result.fetchall():
            biz_type = row[0]
            biz_total = row[1]
            biz_approved = row[2] or 0
            biz_rejected = row[3] or 0
            biz_approve_rate = round(biz_approved / (biz_approved + biz_rejected), 3) \
                if (biz_approved + biz_rejected) > 0 else 0
            by_type.append({
                "business_type": biz_type,
                "total": biz_total,
                "approved": biz_approved,
                "rejected": biz_rejected,
                "approve_rate": biz_approve_rate,
            })

        return {
            "summary": {
                "total": total,
                "approved": approved,
                "rejected": rejected,
                "cancelled": cancelled,
                "in_progress": in_progress,
                "approve_rate": approve_rate,
                "avg_duration_hours": round(float(avg_duration), 1) if avg_duration else None,
            },
            "by_type": by_type,
        }
