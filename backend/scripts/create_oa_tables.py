"""
创建OA模块数据库表

运行方式:
    python scripts/create_oa_tables.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.models.oa.workflow import (
    OaWorkflowDefinition,
    OaWorkflowNode,
    OaWorkflowInstance,
    OaWorkflowTask,
    OaWorkflowVariable,
    OaWorkflowCC,
)


async def create_tables():
    """创建OA相关表"""
    print("=" * 60)
    print("OA模块数据库表创建工具")
    print("=" * 60)
    
    # 检查是否为 SQLite
    is_sqlite = settings.DATABASE_URL.startswith("sqlite")
    
    if is_sqlite:
        db_url = settings.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
        engine = create_async_engine(
            db_url,
            echo=True,
            connect_args={"check_same_thread": False},
        )
    else:
        # PostgreSQL
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=True,
        )
    
    print(f"\n数据库URL: {settings.DATABASE_URL}")
    print(f"数据库类型: {'SQLite' if is_sqlite else 'PostgreSQL'}")
    
    # 要创建的表
    tables = [
        OaWorkflowDefinition.__table__,
        OaWorkflowNode.__table__,
        OaWorkflowInstance.__table__,
        OaWorkflowTask.__table__,
        OaWorkflowVariable.__table__,
        OaWorkflowCC.__table__,
    ]
    
    table_names = [t.name for t in tables]
    print(f"\n将要创建的表: {', '.join(table_names)}")
    
    try:
        async with engine.begin() as conn:
            # 检查表是否存在
            from sqlalchemy import inspect
            
            # 创建表
            print("\n正在创建表...")
            for table in tables:
                try:
                    await conn.run_sync(
                        lambda conn, t=table: t.create(conn, checkfirst=True)
                    )
                    print(f"  ✅ {table.name}")
                except Exception as e:
                    print(f"  ⚠️ {table.name}: {e}")
        
        print("\n" + "=" * 60)
        print("✅ OA工作流表创建完成!")
        print("=" * 60)
        
        # 初始化默认工作流
        print("\n正在初始化默认工作流...")
        await init_default_workflows()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


async def init_default_workflows():
    """初始化默认工作流"""
    from app.core.database import async_session_factory
    from app.services.oa.workflow_engine import WorkflowEngine
    
    async with async_session_factory() as session:
        engine = WorkflowEngine(session)
        
        # 检查是否已有工作流
        from sqlalchemy import select
        from app.models.oa.workflow import OaWorkflowDefinition
        
        result = await session.execute(
            select(OaWorkflowDefinition).where(
                OaWorkflowDefinition.code == "ROOM_BOOKING"
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print("  ℹ️ 默认工作流已存在，跳过初始化")
            return
        
        # 创建教室预约审批流程
        room_booking_flow = {
            "name": "教室预约审批",
            "code": "ROOM_BOOKING",
            "description": "教室/会议室预约审批流程",
            "icon": "Room",
            "category": "resource",
            "form_schema": {
                "fields": [
                    {"name": "room_id", "label": "会议室", "type": "select", "required": True},
                    {"name": "start_time", "label": "开始时间", "type": "datetime", "required": True},
                    {"name": "end_time", "label": "结束时间", "type": "datetime", "required": True},
                    {"name": "title", "label": "会议主题", "type": "text", "required": True},
                    {"name": "attendees", "label": "参会人员", "type": "user_select", "multiple": True},
                    {"name": "remark", "label": "备注", "type": "textarea"},
                ]
            },
            "nodes": [
                {
                    "node_id": "start",
                    "node_type": "start",
                    "node_name": "开始",
                    "approver_type": "starter",
                    "next_nodes": ["dept_approval"],
                },
                {
                    "node_id": "dept_approval",
                    "node_type": "serial",
                    "node_name": "部门负责人审批",
                    "approver_type": "department_leader",
                    "approver_config": {"level": 1},
                    "next_nodes": ["admin_approval"],
                },
                {
                    "node_id": "admin_approval",
                    "node_type": "serial",
                    "node_name": "行政审批",
                    "approver_type": "role",
                    "approver_config": {"role_code": "admin"},
                    "next_nodes": ["end"],
                },
                {
                    "node_id": "end",
                    "node_type": "end",
                    "node_name": "结束",
                    "approver_type": "system",
                },
            ],
        }
        
        try:
            await engine.create_workflow_definition(room_booking_flow)
            print("  ✅ 教室预约审批流程")
        except Exception as e:
            print(f"  ⚠️ 教室预约审批流程: {e}")
        
        # 创建资产借用审批流程
        asset_borrow_flow = {
            "name": "资产借用审批",
            "code": "ASSET_BORROW",
            "description": "资产借用/领用审批流程",
            "icon": "Box",
            "category": "asset",
            "form_schema": {
                "fields": [
                    {"name": "asset_id", "label": "资产", "type": "asset_select", "required": True},
                    {"name": "borrow_days", "label": "借用天数", "type": "number", "required": True},
                    {"name": "purpose", "label": "用途", "type": "textarea", "required": True},
                    {"name": "remark", "label": "备注", "type": "textarea"},
                ]
            },
            "nodes": [
                {
                    "node_id": "start",
                    "node_type": "start",
                    "node_name": "开始",
                    "approver_type": "starter",
                    "next_nodes": ["asset_admin"],
                },
                {
                    "node_id": "asset_admin",
                    "node_type": "serial",
                    "node_name": "资产管理员审批",
                    "approver_type": "role",
                    "approver_config": {"role_code": "asset_admin"},
                    "next_nodes": ["end"],
                },
                {
                    "node_id": "end",
                    "node_type": "end",
                    "node_name": "结束",
                    "approver_type": "system",
                },
            ],
        }
        
        try:
            await engine.create_workflow_definition(asset_borrow_flow)
            print("  ✅ 资产借用审批流程")
        except Exception as e:
            print(f"  ⚠️ 资产借用审批流程: {e}")
        
        # 创建通用审批流程
        general_approval_flow = {
            "name": "通用审批",
            "code": "GENERAL_APPROVAL",
            "description": "通用事项审批流程",
            "icon": "Document",
            "category": "general",
            "form_schema": {
                "fields": [
                    {"name": "title", "label": "审批标题", "type": "text", "required": True},
                    {"name": "content", "label": "审批内容", "type": "richtext", "required": True},
                    {"name": "attachments", "label": "附件", "type": "file", "multiple": True},
                ]
            },
            "nodes": [
                {
                    "node_id": "start",
                    "node_type": "start",
                    "node_name": "开始",
                    "approver_type": "starter",
                    "next_nodes": ["direct_manager"],
                },
                {
                    "node_id": "direct_manager",
                    "node_type": "serial",
                    "node_name": "直属领导审批",
                    "approver_type": "direct_manager",
                    "next_nodes": ["end"],
                },
                {
                    "node_id": "end",
                    "node_type": "end",
                    "node_name": "结束",
                    "approver_type": "system",
                },
            ],
        }
        
        try:
            await engine.create_workflow_definition(general_approval_flow)
            print("  ✅ 通用审批流程")
        except Exception as e:
            print(f"  ⚠️ 通用审批流程: {e}")
        
        await session.commit()
        print("\n✅ 默认工作流初始化完成!")


if __name__ == "__main__":
    asyncio.run(create_tables())
