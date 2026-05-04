"""
数据库迁移脚本：为公告分类创建表并插入测试数据
"""
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy import text
from app.core.database import engine


async def migrate():
    """执行数据库迁移"""
    async with engine.begin() as conn:
        # 1. 检查表是否存在
        result = await conn.execute(text('''
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'announcement_categories'
            )
        '''))
        exists = result.scalar()

        if not exists:
            print('📦 正在创建 announcement_categories 表...')
            # 创建表
            await conn.execute(text('''
                CREATE TABLE announcement_categories (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(50) NOT NULL,
                    code VARCHAR(30) NOT NULL UNIQUE,
                    color VARCHAR(20) DEFAULT '#1890ff',
                    icon VARCHAR(100),
                    sort_order INTEGER DEFAULT 0,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''))
            print('✅ announcement_categories 表创建成功')
        else:
            print('⚠️ announcement_categories 表已存在，跳过创建')

        # 2. 插入测试数据
        print('📝 正在插入测试数据...')
        await conn.execute(text('''
            INSERT INTO announcement_categories (name, code, color, icon, sort_order, description, is_active)
            VALUES
                ('通知公告', 'notice', '#1890ff', 'bell', 1, '学校各类通知公告', TRUE),
                ('活动通知', 'activity', '#52c41a', 'calendar', 2, '校园活动相关通知', TRUE),
                ('紧急通知', 'urgent', '#f5222d', 'warning', 3, '紧急重要通知', TRUE),
                ('学术通知', 'academic', '#722ed1', 'book', 4, '学术讲座、会议通知', TRUE),
                ('考试通知', 'exam', '#fa8c16', 'edit', 5, '考试安排及相关通知', TRUE)
            ON CONFLICT (code) DO NOTHING
        '''))
        print('✅ 测试数据插入成功')

        # 3. 验证数据
        result = await conn.execute(text('''
            SELECT id, name, code, color, sort_order FROM announcement_categories ORDER BY sort_order
        '''))
        rows = result.fetchall()
        print('\n📋 当前分类数据:')
        print('-' * 60)
        print(f"{'ID':<38} {'名称':<10} {'编码':<10} {'颜色':<10}")
        print('-' * 60)
        for row in rows:
            print(f'{row[0]:<38} {row[1]:<10} {row[2]:<10} {row[3]:<10}')
        print('-' * 60)
        print(f'总计: {len(rows)} 条记录')


if __name__ == '__main__':
    print('=' * 60)
    print('公告分类数据库迁移')
    print('=' * 60)
    asyncio.run(migrate())
    print('\n🎉 迁移完成!')
