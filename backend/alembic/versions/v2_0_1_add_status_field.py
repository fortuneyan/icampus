"""Add status field to oa_workflow_definition

Revision ID: v2_0_1
Revises: v2_0_0
Create Date: 2026-05-11 11:50:00.000000

功能：
1. 为 oa_workflow_definition 表添加 status 字段（草稿/已发布/已禁用）
2. 初始化现有记录的 status 值
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'v2_0_1'
down_revision = 'v2_0_0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加 status 字段
    op.add_column(
        'oa_workflow_definition',
        sa.Column('status', sa.String(20), nullable=False, server_default='draft')
    )
    
    # 创建索引
    op.create_index('idx_workflow_definition_status', 'oa_workflow_definition', ['status'], unique=False)
    
    # 初始化现有记录的 status 值
    # is_active=True → published, is_active=False → disabled
    op.execute("""
        UPDATE oa_workflow_definition 
        SET status = CASE 
            WHEN is_active = true THEN 'published'
            ELSE 'disabled'
        END
        WHERE status = 'draft'
    """)


def downgrade() -> None:
    op.drop_index('idx_workflow_definition_status', table_name='oa_workflow_definition')
    op.drop_column('oa_workflow_definition', 'status')
