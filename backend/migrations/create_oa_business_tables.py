"""
数据库迁移脚本：创建OA业务模块相关表

创建以下14张表：

公告模块 (3张):
1. oa_announcement - 公告主表
2. oa_announcement_read - 已读记录表
3. oa_announcement_comment - 评论表

教室预约模块 (2张):
4. oa_room - 教室/场地表
5. oa_room_booking - 预约记录表

资产管理模块 (3张):
6. oa_asset_category - 资产分类表
7. oa_asset - 资产主表
8. oa_borrow_record - 借用记录表

工作日志模块 (1张):
9. oa_work_log - 工作日志表

任务看板模块 (4张):
10. oa_task_project - 项目表
11. oa_task - 任务表
12. oa_task_comment - 任务评论表
13. oa_task_attachment - 任务附件表

执行方式: python migrations/create_oa_business_tables.py
"""
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


async def run_migration():
    """执行数据库迁移"""

    # 创建独立引擎用于需要单独事务的操作
    temp_engine = create_async_engine(
        settings.DATABASE_URL,
        isolation_level="AUTOCOMMIT",  # 使用自动提交模式
        echo=False,
    )

    async with temp_engine.begin() as conn:
        tables = [
            # ========== 公告模块 ==========
            # 1. 公告主表
            {
                "name": "oa_announcement",
                "sql": """
                    CREATE TABLE IF NOT EXISTS oa_announcement (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        title VARCHAR(200) NOT NULL,
                        content_md TEXT DEFAULT '' NOT NULL,
                        content_html TEXT,
                        author_id UUID REFERENCES users(id) ON DELETE SET NULL,
                        category_id UUID REFERENCES announcement_categories(id) ON DELETE SET NULL,
                        org_scope JSONB,
                        role_scope JSONB,
                        priority INTEGER DEFAULT 0 NOT NULL,
                        status VARCHAR(20) DEFAULT 'DRAFT' NOT NULL,
                        publish_time TIMESTAMP,
                        pin_top BOOLEAN DEFAULT FALSE NOT NULL,
                        allow_comment BOOLEAN DEFAULT TRUE NOT NULL,
                        attachment_urls JSONB,
                        read_count INTEGER DEFAULT 0 NOT NULL,
                        comment_count INTEGER DEFAULT 0 NOT NULL,
                        search_vector TSVECTOR,
                        is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                    )
                """
            },
            # 2. 已读记录表
            {
                "name": "oa_announcement_read",
                "sql": """
                    CREATE TABLE IF NOT EXISTS oa_announcement_read (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        announcement_id UUID NOT NULL REFERENCES oa_announcement(id) ON DELETE CASCADE,
                        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                    )
                """
            },
            # 3. 评论表
            {
                "name": "oa_announcement_comment",
                "sql": """
                    CREATE TABLE IF NOT EXISTS oa_announcement_comment (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        announcement_id UUID NOT NULL REFERENCES oa_announcement(id) ON DELETE CASCADE,
                        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        parent_id UUID REFERENCES oa_announcement_comment(id) ON DELETE CASCADE,
                        content_md TEXT NOT NULL,
                        content_html TEXT,
                        reply_to_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                        is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                    )
                """
            },

            # ========== 教室预约模块 ==========
            # 4. 教室/场地表
            {
                "name": "oa_room",
                "sql": """
                    CREATE TABLE IF NOT EXISTS oa_room (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        name VARCHAR(100) NOT NULL,
                        room_type VARCHAR(20) NOT NULL,
                        building VARCHAR(50),
                        floor INTEGER,
                        capacity INTEGER,
                        area_sqm NUMERIC(10, 2),
                        location VARCHAR(200),
                        equipment JSONB,
                        equipment_md TEXT,
                        booking_rules JSONB,
                        org_id UUID REFERENCES departments(id) ON DELETE SET NULL,
                        status VARCHAR(20) DEFAULT 'ACTIVE' NOT NULL,
                        is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                    )
                """
            },
            # 5. 预约记录表
            {
                "name": "oa_room_booking",
                "sql": """
                    CREATE TABLE IF NOT EXISTS oa_room_booking (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        room_id UUID NOT NULL REFERENCES oa_room(id) ON DELETE CASCADE,
                        workflow_instance_id UUID REFERENCES oa_workflow_instance(id) ON DELETE SET NULL,
                        applicant_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        title VARCHAR(200) NOT NULL,
                        agenda_md TEXT,
                        attendee_count INTEGER DEFAULT 1 NOT NULL,
                        attendees JSONB,
                        booking_date DATE NOT NULL,
                        start_time TIME NOT NULL,
                        end_time TIME NOT NULL,
                        start_datetime TIMESTAMP,
                        end_datetime TIMESTAMP,
                        status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
                        reject_reason TEXT,
                        reminder_sent BOOLEAN DEFAULT FALSE NOT NULL,
                        cancelled_at TIMESTAMP,
                        cancel_reason TEXT,
                        is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                    )
                """
            },

            # ========== 资产管理模块 ==========
            # 6. 资产分类表
            {
                "name": "oa_asset_category",
                "sql": """
                    CREATE TABLE IF NOT EXISTS oa_asset_category (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        name VARCHAR(100) NOT NULL,
                        code VARCHAR(50) NOT NULL UNIQUE,
                        parent_id UUID REFERENCES oa_asset_category(id) ON DELETE CASCADE,
                        icon VARCHAR(100),
                        description TEXT,
                        sort_order INTEGER DEFAULT 0 NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                    )
                """
            },
            # 7. 资产主表
            {
                "name": "oa_asset",
                "sql": """
                    CREATE TABLE IF NOT EXISTS oa_asset (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        name VARCHAR(200) NOT NULL,
                        category_id UUID REFERENCES oa_asset_category(id) ON DELETE SET NULL,
                        asset_code VARCHAR(100) NOT NULL UNIQUE,
                        barcode VARCHAR(100),
                        qr_code VARCHAR(255),
                        brand VARCHAR(100),
                        model VARCHAR(100),
                        spec_md TEXT,
                        description_md TEXT,
                        purchase_date DATE,
                        purchase_price NUMERIC(12, 2),
                        supplier VARCHAR(200),
                        warranty_expire DATE,
                        current_org_id UUID REFERENCES departments(id) ON DELETE SET NULL,
                        storage_location VARCHAR(200),
                        status VARCHAR(20) DEFAULT 'IDLE' NOT NULL,
                        image_urls JSONB,
                        is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                    )
                """
            },
            # 8. 借用记录表
            {
                "name": "oa_borrow_record",
                "sql": """
                    CREATE TABLE IF NOT EXISTS oa_borrow_record (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        asset_id UUID NOT NULL REFERENCES oa_asset(id) ON DELETE CASCADE,
                        workflow_instance_id UUID REFERENCES oa_workflow_instance(id) ON DELETE SET NULL,
                        borrower_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        purpose_md TEXT,
                        borrow_date DATE NOT NULL,
                        expected_return_date DATE NOT NULL,
                        actual_return_date DATE,
                        actual_return_condition TEXT,
                        status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
                        approver_id UUID REFERENCES users(id) ON DELETE SET NULL,
                        approver_comment TEXT,
                        approved_at TIMESTAMP,
                        reminder_count INTEGER DEFAULT 0 NOT NULL,
                        last_reminder_at TIMESTAMP,
                        is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                    )
                """
            },

            # ========== 工作日志模块 ==========
            # 9. 工作日志表
            {
                "name": "oa_work_log",
                "sql": """
                    CREATE TABLE IF NOT EXISTS oa_work_log (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        author_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        log_type VARCHAR(20) NOT NULL,
                        period_start DATE NOT NULL,
                        period_end DATE NOT NULL,
                        week_number INTEGER,
                        year INTEGER,
                        month INTEGER,
                        summary_md TEXT,
                        plan_md TEXT,
                        attachment_urls JSONB,
                        total_hours NUMERIC(5, 2),
                        task_count INTEGER DEFAULT 0 NOT NULL,
                        bug_count INTEGER DEFAULT 0 NOT NULL,
                        reviewer_id UUID REFERENCES users(id) ON DELETE SET NULL,
                        review_md TEXT,
                        review_status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
                        review_at TIMESTAMP,
                        submitted_at TIMESTAMP,
                        is_draft BOOLEAN DEFAULT TRUE NOT NULL,
                        reminder_sent BOOLEAN DEFAULT FALSE NOT NULL,
                        is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                    )
                """
            },

            # ========== 任务看板模块 ==========
            # 10. 项目表
            {
                "name": "oa_task_project",
                "sql": """
                    CREATE TABLE IF NOT EXISTS oa_task_project (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        name VARCHAR(200) NOT NULL,
                        description_md TEXT,
                        owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        org_id UUID REFERENCES departments(id) ON DELETE CASCADE,
                        start_date DATE,
                        end_date DATE,
                        status VARCHAR(20) DEFAULT 'ACTIVE' NOT NULL,
                        config JSONB,
                        is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                    )
                """
            },
            # 11. 任务表
            {
                "name": "oa_task",
                "sql": """
                    CREATE TABLE IF NOT EXISTS oa_task (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        project_id UUID REFERENCES oa_task_project(id) ON DELETE CASCADE,
                        parent_id UUID REFERENCES oa_task(id) ON DELETE CASCADE,
                        title VARCHAR(200) NOT NULL,
                        description_md TEXT,
                        creator_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        assignee_id UUID REFERENCES users(id) ON DELETE SET NULL,
                        assignee_type VARCHAR(20),
                        assignee_value VARCHAR(100),
                        priority VARCHAR(20) DEFAULT 'MEDIUM' NOT NULL,
                        status VARCHAR(20) DEFAULT 'TODO' NOT NULL,
                        progress INTEGER DEFAULT 0 NOT NULL,
                        start_date DATE,
                        due_date DATE,
                        completed_at TIMESTAMP,
                        estimated_hours NUMERIC(6, 2),
                        actual_hours NUMERIC(6, 2),
                        tags JSONB,
                        sort_order INTEGER DEFAULT 0 NOT NULL,
                        is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                    )
                """
            },
            # 12. 任务评论表
            {
                "name": "oa_task_comment",
                "sql": """
                    CREATE TABLE IF NOT EXISTS oa_task_comment (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        task_id UUID NOT NULL REFERENCES oa_task(id) ON DELETE CASCADE,
                        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        parent_id UUID REFERENCES oa_task_comment(id) ON DELETE CASCADE,
                        content_md TEXT NOT NULL,
                        content_html TEXT,
                        mentions JSONB,
                        is_edited BOOLEAN DEFAULT FALSE NOT NULL,
                        edited_at TIMESTAMP,
                        is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                    )
                """
            },
            # 13. 任务附件表
            {
                "name": "oa_task_attachment",
                "sql": """
                    CREATE TABLE IF NOT EXISTS oa_task_attachment (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        task_id UUID NOT NULL REFERENCES oa_task(id) ON DELETE CASCADE,
                        uploader_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        file_name VARCHAR(255) NOT NULL,
                        file_url VARCHAR(500) NOT NULL,
                        file_size BIGINT,
                        file_type VARCHAR(50),
                        thumbnail_url VARCHAR(500),
                        is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                    )
                """
            },
        ]

        print("=" * 60)
        print("OA业务模块表迁移")
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
                print(f"📦 [{i}/{len(tables)}] 正在创建 {table_name} 表...")
                await conn.execute(text(sql))
                print(f"   ✅ {table_name} 表创建成功")
            else:
                print(f"⚠️  [{i}/{len(tables)}] {table_name} 表已存在，跳过")

        # 创建索引
        print("\n📇 正在创建索引...")
        indexes = [
            # oa_announcement 索引
            "CREATE INDEX IF NOT EXISTS idx_announcement_author ON oa_announcement(author_id)",
            "CREATE INDEX IF NOT EXISTS idx_announcement_category ON oa_announcement(category_id)",
            "CREATE INDEX IF NOT EXISTS idx_announcement_status ON oa_announcement(status)",
            "CREATE INDEX IF NOT EXISTS idx_announcement_priority ON oa_announcement(priority)",
            "CREATE INDEX IF NOT EXISTS idx_announcement_publish_time ON oa_announcement(publish_time)",
            "CREATE INDEX IF NOT EXISTS idx_announcement_pintop ON oa_announcement(pin_top)",
            "CREATE INDEX IF NOT EXISTS idx_announcement_search ON oa_announcement USING gin(search_vector)",

            # oa_announcement_read 索引
            "CREATE INDEX IF NOT EXISTS idx_announcement_read_user ON oa_announcement_read(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_announcement_read_announcement ON oa_announcement_read(announcement_id)",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_announcement_read_unique ON oa_announcement_read(announcement_id, user_id)",

            # oa_announcement_comment 索引
            "CREATE INDEX IF NOT EXISTS idx_comment_announcement ON oa_announcement_comment(announcement_id)",
            "CREATE INDEX IF NOT EXISTS idx_comment_user ON oa_announcement_comment(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_comment_parent ON oa_announcement_comment(parent_id)",

            # oa_room 索引
            "CREATE INDEX IF NOT EXISTS idx_room_type ON oa_room(room_type)",
            "CREATE INDEX IF NOT EXISTS idx_room_building ON oa_room(building)",
            "CREATE INDEX IF NOT EXISTS idx_room_status ON oa_room(status)",
            "CREATE INDEX IF NOT EXISTS idx_room_org ON oa_room(org_id)",

            # oa_room_booking 索引
            "CREATE INDEX IF NOT EXISTS idx_booking_room_date ON oa_room_booking(room_id, booking_date)",
            "CREATE INDEX IF NOT EXISTS idx_booking_applicant ON oa_room_booking(applicant_id)",
            "CREATE INDEX IF NOT EXISTS idx_booking_status ON oa_room_booking(status)",
            "CREATE INDEX IF NOT EXISTS idx_booking_date ON oa_room_booking(booking_date)",

            # oa_asset_category 索引
            "CREATE INDEX IF NOT EXISTS idx_asset_category_parent ON oa_asset_category(parent_id)",
            "CREATE INDEX IF NOT EXISTS idx_asset_category_code ON oa_asset_category(code)",
            "CREATE INDEX IF NOT EXISTS idx_asset_category_sort ON oa_asset_category(sort_order)",

            # oa_asset 索引
            "CREATE INDEX IF NOT EXISTS idx_asset_code ON oa_asset(asset_code)",
            "CREATE INDEX IF NOT EXISTS idx_asset_category ON oa_asset(category_id)",
            "CREATE INDEX IF NOT EXISTS idx_asset_status ON oa_asset(status)",
            "CREATE INDEX IF NOT EXISTS idx_asset_org ON oa_asset(current_org_id)",
            "CREATE INDEX IF NOT EXISTS idx_asset_barcode ON oa_asset(barcode)",

            # oa_borrow_record 索引
            "CREATE INDEX IF NOT EXISTS idx_borrow_asset ON oa_borrow_record(asset_id)",
            "CREATE INDEX IF NOT EXISTS idx_borrow_borrower ON oa_borrow_record(borrower_id)",
            "CREATE INDEX IF NOT EXISTS idx_borrow_status ON oa_borrow_record(status)",
            "CREATE INDEX IF NOT EXISTS idx_borrow_expected_return ON oa_borrow_record(expected_return_date)",

            # oa_work_log 索引
            "CREATE INDEX IF NOT EXISTS idx_worklog_author ON oa_work_log(author_id)",
            "CREATE INDEX IF NOT EXISTS idx_worklog_type ON oa_work_log(log_type)",
            "CREATE INDEX IF NOT EXISTS idx_worklog_period ON oa_work_log(period_start, period_end)",
            "CREATE INDEX IF NOT EXISTS idx_worklog_reviewer ON oa_work_log(reviewer_id)",
            "CREATE INDEX IF NOT EXISTS idx_worklog_review_status ON oa_work_log(review_status)",

            # oa_task_project 索引
            "CREATE INDEX IF NOT EXISTS idx_project_owner ON oa_task_project(owner_id)",
            "CREATE INDEX IF NOT EXISTS idx_project_org ON oa_task_project(org_id)",
            "CREATE INDEX IF NOT EXISTS idx_project_status ON oa_task_project(status)",

            # oa_task 索引
            "CREATE INDEX IF NOT EXISTS idx_task_project ON oa_task(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_task_parent ON oa_task(parent_id)",
            "CREATE INDEX IF NOT EXISTS idx_task_assignee ON oa_task(assignee_id)",
            "CREATE INDEX IF NOT EXISTS idx_task_creator ON oa_task(creator_id)",
            "CREATE INDEX IF NOT EXISTS idx_task_status ON oa_task(status)",
            "CREATE INDEX IF NOT EXISTS idx_task_priority ON oa_task(priority)",
            "CREATE INDEX IF NOT EXISTS idx_task_due_date ON oa_task(due_date)",

            # oa_task_comment 索引
            "CREATE INDEX IF NOT EXISTS idx_task_comment_task ON oa_task_comment(task_id)",
            "CREATE INDEX IF NOT EXISTS idx_task_comment_user ON oa_task_comment(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_task_comment_parent ON oa_task_comment(parent_id)",

            # oa_task_attachment 索引
            "CREATE INDEX IF NOT EXISTS idx_attachment_task ON oa_task_attachment(task_id)",
            "CREATE INDEX IF NOT EXISTS idx_attachment_uploader ON oa_task_attachment(uploader_id)",
        ]

        for idx_sql in indexes:
            await conn.execute(text(idx_sql))
        print(f"   ✅ 已创建 {len(indexes)} 个索引")

        # 创建约束
        print("\n🔐 正在创建约束...")
        constraints = [
            ("announcement_read", "ALTER TABLE oa_announcement_read ADD CONSTRAINT uq_announcement_read UNIQUE (announcement_id, user_id)"),
            ("worklog", "ALTER TABLE oa_work_log ADD CONSTRAINT uq_worklog_author_type_period UNIQUE (author_id, log_type, period_start)"),
            ("asset_category", "ALTER TABLE oa_asset_category ADD CONSTRAINT uq_asset_category_code UNIQUE (code)"),
            ("asset", "ALTER TABLE oa_asset ADD CONSTRAINT uq_asset_code UNIQUE (asset_code)"),
        ]

        for name, constraint_sql in constraints:
            try:
                await conn.execute(text(constraint_sql))
                print(f"   ✅ {name} 约束创建成功")
            except Exception:
                print(f"   ⚠️ {name} 约束已存在或创建失败，跳过")

        # 创建排他约束 (时间冲突检测)
        print("\n🔒 正在创建排他约束(时间冲突检测)...")
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
            await conn.execute(text("""
                ALTER TABLE oa_room_booking ADD CONSTRAINT no_room_booking_overlap
                EXCLUDE USING gist (
                    room_id WITH =,
                    tstzrange(start_datetime, end_datetime) WITH &&
                ) WHERE (status NOT IN ('CANCELLED', 'REJECTED'))
            """))
            print("   ✅ 教室预约时间排他约束创建成功")
        except Exception:
            print("   ⚠️ 教室预约排他约束创建失败(可能缺少btree_gist扩展或PostgreSQL版本不支持)")

        # 创建全文搜索触发器
        print("\n🔍 正在创建全文搜索触发器...")
        try:
            await conn.execute(text("""
                CREATE OR REPLACE FUNCTION update_announcement_search_vector()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.search_vector := setweight(to_tsvector('simple', COALESCE(NEW.title, '')), 'A') ||
                                         setweight(to_tsvector('simple', COALESCE(NEW.content_md, '')), 'B');
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """))
            await conn.execute(text("""
                DROP TRIGGER IF EXISTS update_announcement_search ON oa_announcement;
                CREATE TRIGGER update_announcement_search
                BEFORE INSERT OR UPDATE OF title, content_md ON oa_announcement
                FOR EACH ROW EXECUTE FUNCTION update_announcement_search_vector();
            """))
            print("   ✅ 全文搜索触发器创建成功")
        except Exception:
            print("   ⚠️ 全文搜索触发器创建失败")

        # 验证表创建
        print("\n📋 验证表创建...")
        result = await conn.execute(text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name LIKE 'oa_%'
            ORDER BY table_name
        """))
        tables_created = result.fetchall()
        print(f"   ✅ 已创建 {len(tables_created)} 张OA表:")
        for t in tables_created:
            print(f"      - {t[0]}")

        print("\n" + "=" * 60)
        print("🎉 业务模块表迁移完成!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_migration())
