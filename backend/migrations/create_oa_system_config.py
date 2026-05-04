"""
数据库迁移脚本：创建OA系统配置表并插入默认配置

创建以下表：
1. oa_system_config - 系统配置表

执行方式: python migrations/create_oa_system_config.py
"""
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy import text
from app.core.database import engine


async def migrate():
    """执行数据库迁移"""
    async with engine.begin() as conn:
        print("=" * 60)
        print("OA系统配置表迁移")
        print("=" * 60)

        # 1. 创建系统配置表
        print("\n📦 正在创建 oa_system_config 表...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS oa_system_config (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                config_key VARCHAR(100) NOT NULL UNIQUE,
                config_value TEXT,
                config_type VARCHAR(20) DEFAULT 'STRING' NOT NULL,
                category VARCHAR(50) NOT NULL,
                description TEXT,
                is_system BOOLEAN DEFAULT FALSE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
            )
        """))
        print("   ✅ oa_system_config 表创建成功")

        # 创建索引
        print("\n📇 正在创建索引...")
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_config_key ON oa_system_config(config_key)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_config_category ON oa_system_config(category)"))
        print("   ✅ 索引创建成功")

        # 2. 插入默认配置
        print("\n📝 正在插入默认配置...")
        default_configs = [
            # 教室预约配置
            ("room_booking.default_duration_hours", "2", "NUMBER", "ROOM", "教室预约默认时长(小时)"),
            ("room_booking.max_advance_days", "30", "NUMBER", "ROOM", "教室预约最大提前天数"),
            ("room_booking.max_duration_hours", "4", "NUMBER", "ROOM", "单次预约最大时长(小时)"),
            ("room_booking.auto_reminder_minutes", "30", "NUMBER", "ROOM", "预约开始前提醒时间(分钟)"),
            ("room_booking.allow_weekends", "true", "BOOLEAN", "ROOM", "是否允许周末预约"),

            # 资产管理配置
            ("asset.borrow_max_days", "30", "NUMBER", "ASSET", "资产借用最大天数"),
            ("asset.auto_reminder_days", "3", "NUMBER", "ASSET", "借用到期前提醒天数"),
            ("asset.overdue_reminder_interval", "1", "NUMBER", "ASSET", "超期提醒间隔(天)"),
            ("asset.require_approval", "true", "BOOLEAN", "ASSET", "借用是否需要审批"),

            # 工作日志配置
            ("worklog.weekly_submit_deadline", "17:00", "STRING", "WORKLOG", "周报提交截止时间"),
            ("worklog.weekly_reminder_day", "5", "NUMBER", "WORKLOG", "周报提醒星期几(1-7)"),
            ("worklog.weekly_reminder_time", "09:00", "STRING", "WORKLOG", "周报提醒时间"),
            ("worklog.monthly_submit_deadline", "3", "NUMBER", "WORKLOG", "月报提交截止日"),
            ("worklog.require_plan", "true", "BOOLEAN", "WORKLOG", "是否要求填写下期计划"),

            # 公告配置
            ("announcement.default_priority", "0", "NUMBER", "ANNOUNCEMENT", "公告默认优先级(0-普通 1-重要 2-紧急)"),
            ("announcement.allow_comment", "true", "BOOLEAN", "ANNOUNCEMENT", "是否允许评论"),
            ("announcement.show_author", "true", "BOOLEAN", "ANNOUNCEMENT", "是否显示作者"),
            ("announcement.max_attachments", "5", "NUMBER", "ANNOUNCEMENT", "最大附件数量"),

            # 任务看板配置
            ("task.default_priority", "MEDIUM", "STRING", "TASK", "任务默认优先级"),
            ("task.reminder_before_due_hours", "24", "NUMBER", "TASK", "到期前提醒小时数"),
            ("task.auto_archive_completed_days", "30", "NUMBER", "TASK", "完成后自动归档天数(0-不自动归档)"),
            ("task.allow_subtasks", "true", "BOOLEAN", "TASK", "是否允许子任务"),

            # 审批配置
            ("approval.timeout_hours", "72", "NUMBER", "APPROVAL", "审批超时默认小时数"),
            ("approval.timeout_action", "NOTIFY", "STRING", "APPROVAL", "超时动作: SKIP/AUTO_APPROVE/NOTIFY"),
            ("approval.reminder_interval_hours", "24", "NUMBER", "APPROVAL", "催办提醒间隔(小时)"),
            ("approval.allow_withdraw", "true", "BOOLEAN", "APPROVAL", "是否允许撤回"),
            ("approval.allow_transfer", "true", "BOOLEAN", "APPROVAL", "是否允许转交"),
        ]

        for config in default_configs:
            key, value, config_type, category, description = config
            try:
                await conn.execute(text("""
                    INSERT INTO oa_system_config (config_key, config_value, config_type, category, description)
                    VALUES (:key, :value, :type, :category, :desc)
                    ON CONFLICT (config_key) DO UPDATE SET
                        config_value = EXCLUDED.config_value,
                        config_type = EXCLUDED.config_type,
                        category = EXCLUDED.category,
                        description = EXCLUDED.description,
                        updated_at = CURRENT_TIMESTAMP
                """), {"key": key, "value": value, "type": config_type, "category": category, "desc": description})
            except Exception as e:
                print(f"   ⚠️ 配置 {key} 插入失败: {str(e)[:30]}")

        print(f"   ✅ 已插入/更新 {len(default_configs)} 条配置")

        # 3. 验证配置
        print("\n📋 验证配置数据...")
        result = await conn.execute(text("""
            SELECT category, COUNT(*) as count
            FROM oa_system_config
            GROUP BY category
            ORDER BY category
        """))
        categories = result.fetchall()
        print("   配置统计:")
        for cat, count in categories:
            print(f"      - {cat}: {count} 条")

        # 显示所有配置
        result = await conn.execute(text("""
            SELECT config_key, config_value, category
            FROM oa_system_config
            ORDER BY category, config_key
        """))
        configs = result.fetchall()

        print("\n   完整配置列表:")
        current_category = None
        for config in configs:
            key, value, category = config
            if category != current_category:
                print(f"\n      [{category}]")
                current_category = category
            print(f"         {key} = {value}")

        print("\n" + "=" * 60)
        print("🎉 系统配置表迁移完成!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(migrate())
