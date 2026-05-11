"""
工作流超时处理服务

由定时任务（APScheduler）每10分钟调用一次
负责检测并处理超时的审批任务
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.oa.workflow import OaWorkflowTask, OaWorkflowInstance, OaWorkflowNode
from app.models import Notification


class WorkflowTimeoutService:
    """
    工作流超时处理服务

    由定时任务（APScheduler / Celery Beat）每10分钟调用一次
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_overdue_tasks(self) -> Dict[str, int]:
        """
        处理所有超时任务

        Returns:
            {
                "notified": int,      # 触发NOTIFY的任务数
                "auto_approved": int, # 触发AUTO_APPROVE的任务数
                "skipped": int,       # 触发SKIP的任务数
            }

        处理逻辑：
            1. 查询所有 deadline < now() AND status="PENDING" 的任务
            2. 根据节点的 timeout_action 执行相应操作：
               - NOTIFY: 给审批人发提醒通知，标记 is_overdue=True
               - AUTO_APPROVE: 自动通过（调用引擎的 handle_task）
               - SKIP: 跳过该节点，推进流程
        """
        now = datetime.now()

        # 查询超时且未处理的任务
        stmt = (
            select(OaWorkflowTask)
            .where(
                and_(
                    OaWorkflowTask.deadline < now,
                    OaWorkflowTask.status == "PENDING",
                    OaWorkflowTask.is_overdue == False,
                    OaWorkflowTask.is_deleted == False,
                )
            )
        )
        result = await self.db.execute(stmt)
        overdue_tasks: List[OaWorkflowTask] = list(result.scalars().all())

        stats = {"notified": 0, "auto_approved": 0, "skipped": 0}

        for task in overdue_tasks:
            # 获取节点配置
            node = await self._get_node(task.node_id)
            if not node:
                continue

            timeout_action = node.timeout_action or "NOTIFY"
            task.is_overdue = True  # 标记为已超时

            if timeout_action == "NOTIFY":
                await self._notify_overdue(task)
                stats["notified"] += 1

            elif timeout_action == "AUTO_APPROVE":
                await self._auto_approve_task(task)
                stats["auto_approved"] += 1

            elif timeout_action == "SKIP":
                await self._skip_task(task)
                stats["skipped"] += 1

        await self.db.commit()
        return stats

    async def _notify_overdue(self, task: OaWorkflowTask) -> None:
        """发送超时提醒通知"""
        if task.assignee_id:
            # 获取实例标题
            instance_title = "审批任务"
            instance_stmt = select(OaWorkflowInstance.title).where(
                OaWorkflowInstance.id == task.instance_id
            )
            instance_result = await self.db.execute(instance_stmt)
            instance_title_row = instance_result.scalar_one_or_none()
            if instance_title_row:
                instance_title = instance_title_row

            notification = Notification(
                user_id=task.assignee_id,
                title="审批超时提醒",
                content=f"您有一个审批任务「{instance_title}」已超时，请尽快处理",
                type="WORKFLOW_OVERDUE",
                related_id=str(task.instance_id),
                created_at=datetime.now(),
            )
            self.db.add(notification)

    async def _auto_approve_task(self, task: OaWorkflowTask) -> None:
        """自动通过超时任务"""
        from app.services.oa.workflow_engine import WorkflowEngine

        # 用系统账户ID执行审批
        SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

        try:
            engine = WorkflowEngine(self.db)
            # 注意：_approve_task 是引擎内部方法，这里直接更新任务状态
            task.status = "APPROVED"
            task.action = "AUTO_APPROVE"
            task.completed_at = datetime.now()
            task.comment = "超时自动通过"

            # 推进流程到下一节点
            instance = await self._get_instance(task.instance_id)
            node = await self._get_node(task.node_id)
            if instance and node:
                engine_instance = WorkflowEngine(self.db)
                await engine_instance._move_to_next_node(instance, node)
        except Exception:
            pass  # 自动审批失败不影响其他任务

    async def _skip_task(self, task: OaWorkflowTask) -> None:
        """跳过超时任务，推进流程"""
        task.status = "SKIPPED"
        task.action = "SKIP"
        task.completed_at = datetime.now()
        task.comment = "超时自动跳过"

        # 推进流程到下一节点
        from app.services.oa.workflow_engine import WorkflowEngine
        engine = WorkflowEngine(self.db)
        instance = await self._get_instance(task.instance_id)
        node = await self._get_node(task.node_id)
        if instance and node:
            await engine._move_to_next_node(instance, node)

    async def _get_node(self, node_id: UUID):
        """获取节点"""
        from app.models.oa.workflow import OaWorkflowNode
        stmt = select(OaWorkflowNode).where(
            and_(
                OaWorkflowNode.id == node_id,
                OaWorkflowNode.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_instance(self, instance_id: UUID):
        """获取实例"""
        stmt = select(OaWorkflowInstance).where(
            and_(
                OaWorkflowInstance.id == instance_id,
                OaWorkflowInstance.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
