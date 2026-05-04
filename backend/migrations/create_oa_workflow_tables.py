"""
数据库迁移脚本：创建OA工作流相关表

创建以下6张表：
1. oa_workflow_definition - 工作流定义
2. oa_workflow_node - 审批节点
3. oa_workflow_instance - 审批实例
4. oa_workflow_task - 审批任务
5. oa_workflow_variable - 流程变量
6. oa_workflow_cc - 抄送记录

执行方式: python migrations/create_oa_workflow_tables.py
"""
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy import text
from app.core.database import engine


async def migrate():
    """执行数据库迁移"""
    async with engine.begin() as conn:
        tables = [
            # 1. 工作流定义表
            {
                "name": "oa_workflow_definition",
                "sql": """
                    CREATE TABLE IF NOT EXISTS oa_workflow_definition (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        name VARCHAR(100) NOT NULL,
                        code VARCHAR(50) NOT NULL UNIQUE,
                        description TEXT,
                        version INTEGER DEFAULT 1 NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE NOT NULL,
                        config JSONB,
                        form_config JSONB,
                        business_type VARCHAR(50),
                        allow_withdraw BOOLEAN DEFAULT TRUE NOT NULL,
                        allow_transfer BOOLEAN DEFAULT TRUE NOT NULL,
                        allow_cc BOOLEAN DEFAULT TRUE NOT NULL,
                        published_at TIMESTAMP,
                        published_by UUID,
                        is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                    )
                """
            },
            # 2. 审批节点表
            {
                "name": "oa_workflow_node",
                "sql": """
                    CREATE TABLE IF NOT EXISTS oa_workflow_node (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        definition_id UUID NOT NULL REFERENCES oa_workflow_definition(id) ON DELETE CASCADE,
                        name VARCHAR(100) NOT NULL,
                        code VARCHAR(50),
                        node_type VARCHAR(20) NOT NULL,
                        order_index INTEGER DEFAULT 0 NOT NULL,
                        config JSONB,
                        approver_rule JSONB,
                        timeout_hours INTEGER,
                        timeout_action VARCHAR(20),
                        condition_expression TEXT,
                        group_id UUID,
                        is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                    )
                """
            },
            # 3. 审批实例表
            {
                "name": "oa_workflow_instance",
                "sql": """
                    CREATE TABLE IF NOT EXISTS oa_workflow_instance (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        definition_id UUID NOT NULL REFERENCES oa_workflow_definition(id),
                        business_type VARCHAR(50) NOT NULL,
                        business_id UUID NOT NULL,
                        initiator_id UUID NOT NULL REFERENCES users(id),
                        status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
                        current_node_id UUID,
                        completed_node_ids JSONB,
                        approval_summary JSONB,
                        cc_list JSONB,
                        form_data JSONB,
                        title VARCHAR(200) NOT NULL,
                        summary TEXT,
                        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        cancelled_at TIMESTAMP,
                        cancel_reason TEXT,
                        is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                    )
                """
            },
            # 4. 审批任务表
            {
                "name": "oa_workflow_task",
                "sql": """
                    CREATE TABLE IF NOT EXISTS oa_workflow_task (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        instance_id UUID NOT NULL REFERENCES oa_workflow_instance(id) ON DELETE CASCADE,
                        node_id UUID NOT NULL REFERENCES oa_workflow_node(id),
                        task_type VARCHAR(20) NOT NULL,
                        status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
                        assignee_id UUID REFERENCES users(id),
                        assignee_type VARCHAR(20),
                        original_assignee_id UUID,
                        assigned_at TIMESTAMP,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        deadline TIMESTAMP,
                        is_overdue BOOLEAN DEFAULT FALSE NOT NULL,
                        overdue_reminders INTEGER DEFAULT 0 NOT NULL,
                        comment TEXT,
                        action VARCHAR(20),
                        transfer_from UUID,
                        transfer_to UUID,
                        transfer_reason TEXT,
                        delegate_from UUID,
                        delegate_to UUID,
                        order_index INTEGER DEFAULT 0 NOT NULL,
                        is_required BOOLEAN DEFAULT TRUE NOT NULL,
                        is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                    )
                """
            },
            # 5. 流程变量表
            {
                "name": "oa_workflow_variable",
                "sql": """
                    CREATE TABLE IF NOT EXISTS oa_workflow_variable (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        instance_id UUID NOT NULL REFERENCES oa_workflow_instance(id) ON DELETE CASCADE,
                        name VARCHAR(100) NOT NULL,
                        value TEXT,
                        value_type VARCHAR(20) DEFAULT 'STRING' NOT NULL,
                        source VARCHAR(20),
                        node_id UUID REFERENCES oa_workflow_node(id),
                        is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                    )
                """
            },
            # 6. 抄送记录表
            {
                "name": "oa_workflow_cc",
                "sql": """
                    CREATE TABLE IF NOT EXISTS oa_workflow_cc (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        instance_id UUID NOT NULL REFERENCES oa_workflow_instance(id) ON DELETE CASCADE,
                        cc_user_id UUID NOT NULL REFERENCES users(id),
                        cc_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        is_read BOOLEAN DEFAULT FALSE NOT NULL,
                        read_at TIMESTAMP,
                        reason VARCHAR(200),
                        is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                    )
                """
            }
        ]

        print("=" * 60)
        print("OA工作流表迁移")
        print("=" * 60)

        # 创建表
        for i, table in enumerate(tables, 1):
            table_name = table["name"]
            sql = table["sql"]

            # 检查表是否存在
            result = await conn.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = '{table_name}'
                )
            """))
            exists = result.scalar()

            if not exists:
                print(f"📦 [{i}/6] 正在创建 {table_name} 表...")
                await conn.execute(text(sql))
                print(f"   ✅ {table_name} 表创建成功")
            else:
                print(f"⚠️  [{i}/6] {table_name} 表已存在，跳过")

        # 创建索引
        print("\n📇 正在创建索引...")
        indexes = [
            # oa_workflow_definition 索引
            "CREATE INDEX IF NOT EXISTS idx_workflow_def_code ON oa_workflow_definition(code)",
            "CREATE INDEX IF NOT EXISTS idx_workflow_def_business_type ON oa_workflow_definition(business_type)",
            "CREATE INDEX IF NOT EXISTS idx_workflow_def_active ON oa_workflow_definition(is_active)",

            # oa_workflow_node 索引
            "CREATE INDEX IF NOT EXISTS idx_workflow_node_definition ON oa_workflow_node(definition_id)",
            "CREATE INDEX IF NOT EXISTS idx_workflow_node_type ON oa_workflow_node(node_type)",
            "CREATE INDEX IF NOT EXISTS idx_workflow_node_order ON oa_workflow_node(definition_id, order_index)",

            # oa_workflow_instance 索引
            "CREATE INDEX IF NOT EXISTS idx_workflow_inst_definition ON oa_workflow_instance(definition_id)",
            "CREATE INDEX IF NOT EXISTS idx_workflow_inst_business ON oa_workflow_instance(business_type, business_id)",
            "CREATE INDEX IF NOT EXISTS idx_workflow_inst_initiator ON oa_workflow_instance(initiator_id)",
            "CREATE INDEX IF NOT EXISTS idx_workflow_inst_status ON oa_workflow_instance(status)",
            "CREATE INDEX IF NOT EXISTS idx_workflow_inst_submitted ON oa_workflow_instance(submitted_at)",

            # oa_workflow_task 索引
            "CREATE INDEX IF NOT EXISTS idx_workflow_task_instance ON oa_workflow_task(instance_id)",
            "CREATE INDEX IF NOT EXISTS idx_workflow_task_node ON oa_workflow_task(node_id)",
            "CREATE INDEX IF NOT EXISTS idx_workflow_task_assignee ON oa_workflow_task(assignee_id)",
            "CREATE INDEX IF NOT EXISTS idx_workflow_task_status ON oa_workflow_task(status)",
            "CREATE INDEX IF NOT EXISTS idx_workflow_task_assignee_status ON oa_workflow_task(assignee_id, status)",

            # oa_workflow_variable 索引
            "CREATE INDEX IF NOT EXISTS idx_workflow_var_instance ON oa_workflow_variable(instance_id)",
            "CREATE INDEX IF NOT EXISTS idx_workflow_var_name ON oa_workflow_variable(instance_id, name)",

            # oa_workflow_cc 索引
            "CREATE INDEX IF NOT EXISTS idx_workflow_cc_instance ON oa_workflow_cc(instance_id)",
            "CREATE INDEX IF NOT EXISTS idx_workflow_cc_user ON oa_workflow_cc(cc_user_id)",
            "CREATE INDEX IF NOT EXISTS idx_workflow_cc_user_unread ON oa_workflow_cc(cc_user_id, is_read)",
        ]

        for idx_sql in indexes:
            await conn.execute(text(idx_sql))
        print(f"   ✅ 已创建 {len(indexes)} 个索引")

        # 创建唯一约束
        print("\n🔐 正在创建约束...")
        constraints = [
            "ALTER TABLE oa_workflow_instance ADD CONSTRAINT uq_workflow_inst_business UNIQUE (business_type, business_id)"
        ]
        for constraint_sql in constraints:
            try:
                await conn.execute(text(constraint_sql))
            except Exception as e:
                if "duplicate" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"   ⚠️ 约束已存在，跳过")
                else:
                    print(f"   ⚠️ 约束创建失败: {e}")

        # 验证表创建
        print("\n📋 验证表创建...")
        result = await conn.execute(text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name LIKE 'oa_workflow%'
            ORDER BY table_name
        """))
        tables_created = result.fetchall()
        print(f"   ✅ 已创建 {len(tables_created)} 张工作流表:")
        for t in tables_created:
            print(f"      - {t[0]}")

        print("\n" + "=" * 60)
        print("🎉 工作流表迁移完成!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(migrate())
