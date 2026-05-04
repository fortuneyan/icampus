"""
OA工作流初始化脚本

预置工作流模板数据：
- 教室预约审批流程
- 资产借用审批流程

使用方法:
    cd backend
    python scripts/init_oa_workflow.py
"""
import asyncio
import logging
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models.oa import OaWorkflowDefinition, OaWorkflowNode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_workflow_data(session: AsyncSession):
    """初始化工作流数据"""
    
    # 检查是否已有数据
    result = await session.execute(select(OaWorkflowDefinition))
    existing = result.scalars().all()
    if existing:
        logger.info(f"已有 {len(existing)} 个工作流定义，跳过初始化")
        return
    
    logger.info("开始初始化工作流数据...")
    
    # =========================================================================
    # 1. 教室预约审批流程
    # =========================================================================
    logger.info("创建教室预约审批流程...")
    
    room_booking_def = OaWorkflowDefinition(
        id=uuid4(),
        name="教室预约审批",
        code="ROOM_BOOKING",
        description="用于教室和场地预约的审批流程",
        business_type="ROOM_BOOKING",
        is_active=True,
        allow_withdraw=True,
        allow_transfer=True,
        allow_cc=True,
        config={
            "allow_parallel": False,
            "auto_approve_when_no_approver": False,
        },
        form_config={
            "fields": [
                {"name": "room_id", "type": "select", "required": True, "label": "预约教室"},
                {"name": "title", "type": "text", "required": True, "label": "预约主题"},
                {"name": "agenda", "type": "textarea", "required": False, "label": "会议议程"},
                {"name": "attendee_count", "type": "number", "required": True, "label": "参会人数"},
                {"name": "start_time", "type": "datetime", "required": True, "label": "开始时间"},
                {"name": "end_time", "type": "datetime", "required": True, "label": "结束时间"},
            ]
        }
    )
    session.add(room_booking_def)
    await session.flush()
    
    # 创建节点
    nodes = [
        # 开始节点
        OaWorkflowNode(
            id=uuid4(),
            definition_id=room_booking_def.id,
            name="开始",
            code="START",
            node_type="START",
            order_index=1,
            is_required=True,
        ),
        # 部门负责人审批
        OaWorkflowNode(
            id=uuid4(),
            definition_id=room_booking_def.id,
            name="部门负责人审批",
            code="DEPT_APPROVAL",
            node_type="APPROVAL",
            order_index=2,
            approver_rule={
                "type": "department_leader"
            },
            timeout_hours=24,
            timeout_action="NOTIFY",
            is_required=True,
        ),
        # 结束节点
        OaWorkflowNode(
            id=uuid4(),
            definition_id=room_booking_def.id,
            name="结束",
            code="END",
            node_type="END",
            order_index=3,
            is_required=False,
        ),
    ]
    for node in nodes:
        session.add(node)
    
    logger.info(f"教室预约审批流程创建完成，包含 {len(nodes)} 个节点")
    
    # =========================================================================
    # 2. 资产借用审批流程
    # =========================================================================
    logger.info("创建资产借用审批流程...")
    
    asset_borrow_def = OaWorkflowDefinition(
        id=uuid4(),
        name="资产借用审批",
        code="ASSET_BORROW",
        description="用于资产借用的审批流程",
        business_type="ASSET_BORROW",
        is_active=True,
        allow_withdraw=True,
        allow_transfer=True,
        allow_cc=True,
        config={
            "allow_parallel": False,
            "auto_approve_when_no_approver": False,
        },
        form_config={
            "fields": [
                {"name": "asset_id", "type": "select", "required": True, "label": "借用资产"},
                {"name": "purpose", "type": "textarea", "required": True, "label": "借用用途"},
                {"name": "borrow_date", "type": "date", "required": True, "label": "借用日期"},
                {"name": "expected_return_date", "type": "date", "required": True, "label": "预计归还日期"},
            ]
        }
    )
    session.add(asset_borrow_def)
    await session.flush()
    
    # 创建节点
    nodes = [
        # 开始节点
        OaWorkflowNode(
            id=uuid4(),
            definition_id=asset_borrow_def.id,
            name="开始",
            code="START",
            node_type="START",
            order_index=1,
            is_required=True,
        ),
        # 部门负责人审批
        OaWorkflowNode(
            id=uuid4(),
            definition_id=asset_borrow_def.id,
            name="部门负责人审批",
            code="DEPT_APPROVAL",
            node_type="APPROVAL",
            order_index=2,
            approver_rule={
                "type": "department_leader"
            },
            timeout_hours=48,
            timeout_action="NOTIFY",
            is_required=True,
        ),
        # 资产管理员审批
        OaWorkflowNode(
            id=uuid4(),
            definition_id=asset_borrow_def.id,
            name="资产管理员审批",
            code="ASSET_ADMIN_APPROVAL",
            node_type="APPROVAL",
            order_index=3,
            approver_rule={
                "type": "role",
                "value": ["asset_admin"]
            },
            timeout_hours=24,
            timeout_action="NOTIFY",
            is_required=True,
        ),
        # 结束节点
        OaWorkflowNode(
            id=uuid4(),
            definition_id=asset_borrow_def.id,
            name="结束",
            code="END",
            node_type="END",
            order_index=4,
            is_required=False,
        ),
    ]
    for node in nodes:
        session.add(node)
    
    logger.info(f"资产借用审批流程创建完成，包含 {len(nodes)} 个节点")
    
    # =========================================================================
    # 3. 通用审批流程（用于其他业务）
    # =========================================================================
    logger.info("创建通用审批流程...")
    
    general_def = OaWorkflowDefinition(
        id=uuid4(),
        name="通用审批流程",
        code="GENERAL_APPROVAL",
        description="通用的审批流程模板",
        business_type=None,
        is_active=True,
        allow_withdraw=True,
        allow_transfer=True,
        allow_cc=True,
        config={
            "allow_parallel": False,
            "auto_approve_when_no_approver": False,
        },
        form_config={
            "fields": [
                {"name": "title", "type": "text", "required": True, "label": "审批标题"},
                {"name": "content", "type": "textarea", "required": True, "label": "审批内容"},
            ]
        }
    )
    session.add(general_def)
    await session.flush()
    
    # 创建节点
    nodes = [
        # 开始节点
        OaWorkflowNode(
            id=uuid4(),
            definition_id=general_def.id,
            name="开始",
            code="START",
            node_type="START",
            order_index=1,
            is_required=True,
        ),
        # 直接上级审批
        OaWorkflowNode(
            id=uuid4(),
            definition_id=general_def.id,
            name="直接上级审批",
            code="MANAGER_APPROVAL",
            node_type="APPROVAL",
            order_index=2,
            approver_rule={
                "type": "direct_manager"
            },
            timeout_hours=48,
            timeout_action="NOTIFY",
            is_required=True,
        ),
        # 结束节点
        OaWorkflowNode(
            id=uuid4(),
            definition_id=general_def.id,
            name="结束",
            code="END",
            node_type="END",
            order_index=3,
            is_required=False,
        ),
    ]
    for node in nodes:
        session.add(node)
    
    logger.info(f"通用审批流程创建完成，包含 {len(nodes)} 个节点")
    
    await session.commit()
    logger.info("工作流数据初始化完成！")


async def main():
    """主函数"""
    async with async_session_factory() as session:
        try:
            await init_workflow_data(session)
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
