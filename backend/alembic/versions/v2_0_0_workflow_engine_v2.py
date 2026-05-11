"""OA工作流引擎 v2.0 数据库迁移脚本

Revision ID: v2_0_0
Revises: 
Create Date: 2026-05-11 10:00:00.000000

功能：
1. 新增流程连线表（oa_workflow_sequence_flow）
2. 新增并行分支状态表（oa_workflow_branch_state）
3. 新增审计日志表（oa_workflow_audit_log）
4. 新增版本管理表（oa_workflow_version）
5. 新增子流程实例表（oa_workflow_subflow_instance）
6. 新增边界事件表（oa_workflow_boundary_event）
7. 新增定时任务表（oa_workflow_timer_job）
8. 新增通知设置表（oa_workflow_notification_setting）
9. 新增离线操作表（oa_workflow_offline_action）
10. 增强oa_workflow_node表（新增12个字段）
11. 增强oa_workflow_task表（新增2个字段）
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'v2_0_0'
down_revision = None  # 替换为实际的上一版本
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================
    # 1. 新增流程连线表
    # ==========================================
    op.create_table(
        'oa_workflow_sequence_flow',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('definition_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('oa_workflow_definition.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=True),
        sa.Column('code', sa.String(50), nullable=True),
        sa.Column('source_node_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('oa_workflow_node.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_node_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('oa_workflow_node.id', ondelete='CASCADE'), nullable=False),
        sa.Column('condition_expression', sa.Text(), nullable=True),
        sa.Column('flow_type', sa.String(20), nullable=False, server_default='DEFAULT'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('style', postgresql.JSONB(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('source_node_id', 'target_node_id', name='uq_sequence_flow_pair')
    )
    op.create_index('idx_sequence_flow_definition', 'oa_workflow_sequence_flow', ['definition_id'], unique=False)
    op.create_index('idx_sequence_flow_source', 'oa_workflow_sequence_flow', ['source_node_id'], unique=False)
    op.create_index('idx_sequence_flow_target', 'oa_workflow_sequence_flow', ['target_node_id'], unique=False)
    
    # ==========================================
    # 2. 新增并行分支状态表
    # ==========================================
    op.create_table(
        'oa_workflow_branch_state',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('instance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('oa_workflow_instance.id', ondelete='CASCADE'), nullable=False),
        sa.Column('gateway_node_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('oa_workflow_node.id'), nullable=False),
        sa.Column('branch_id', sa.String(100), nullable=False),
        sa.Column('branch_index', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='WAITING'),
        sa.Column('current_node_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('started_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('ended_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('triggered_by_flow_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    op.create_index('idx_branch_state_instance', 'oa_workflow_branch_state', ['instance_id'], unique=False)
    op.create_index('idx_branch_state_gateway', 'oa_workflow_branch_state', ['gateway_node_id'], unique=False)
    op.create_index('idx_branch_state_status', 'oa_workflow_branch_state', ['status'], unique=False)
    
    # ==========================================
    # 3. 新增审计日志表
    # ==========================================
    op.create_table(
        'oa_workflow_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('instance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('oa_workflow_instance.id'), nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('node_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('operator_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('operator_name', sa.String(100), nullable=True),
        sa.Column('operator_ip', sa.String(50), nullable=True),
        sa.Column('operated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('before_state', postgresql.JSONB(), nullable=True),
        sa.Column('after_state', postgresql.JSONB(), nullable=True),
        sa.Column('extra_data', postgresql.JSONB(), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    op.create_index('idx_audit_instance', 'oa_workflow_audit_log', ['instance_id'], unique=False)
    op.create_index('idx_audit_operator', 'oa_workflow_audit_log', ['operator_id'], unique=False)
    op.create_index('idx_audit_action', 'oa_workflow_audit_log', ['action_type'], unique=False)
    op.create_index('idx_audit_time', 'oa_workflow_audit_log', ['operated_at'], unique=False)
    op.create_index('idx_audit_instance_time', 'oa_workflow_audit_log', ['instance_id', 'operated_at'], unique=False)
    
    # ==========================================
    # 4. 新增版本管理表
    # ==========================================
    op.create_table(
        'oa_workflow_version',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('definition_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('oa_workflow_definition.id'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='DRAFT'),
        sa.Column('changelog', sa.Text(), nullable=True),
        sa.Column('published_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('published_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('snapshot', postgresql.JSONB(), nullable=False),
        sa.Column('active_instances', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('definition_id', 'version', name='uq_version_number')
    )
    op.create_index('idx_version_definition', 'oa_workflow_version', ['definition_id'], unique=False)
    op.create_index('idx_version_status', 'oa_workflow_version', ['status'], unique=False)
    
    # ==========================================
    # 5. 新增子流程实例表
    # ==========================================
    op.create_table(
        'oa_workflow_subflow_instance',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('parent_instance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('oa_workflow_instance.id', ondelete='CASCADE'), nullable=False),
        sa.Column('parent_node_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('oa_workflow_node.id'), nullable=False),
        sa.Column('subflow_definition_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('oa_workflow_definition.id'), nullable=False),
        sa.Column('subflow_instance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('oa_workflow_instance.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='RUNNING'),
        sa.Column('input_mapping', postgresql.JSON(), nullable=True),
        sa.Column('output_mapping', postgresql.JSON(), nullable=True),
        sa.Column('started_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('ended_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    op.create_index('idx_subflow_parent_instance', 'oa_workflow_subflow_instance', ['parent_instance_id'], unique=False)
    op.create_index('idx_subflow_subflow_instance', 'oa_workflow_subflow_instance', ['subflow_instance_id'], unique=False)
    op.create_index('idx_subflow_status', 'oa_workflow_subflow_instance', ['status'], unique=False)
    
    # ==========================================
    # 6. 新增边界事件表
    # ==========================================
    op.create_table(
        'oa_workflow_boundary_event',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('definition_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('oa_workflow_definition.id', ondelete='CASCADE'), nullable=False),
        sa.Column('attached_node_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('oa_workflow_node.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(20), nullable=False),
        sa.Column('event_name', sa.String(100), nullable=True),
        sa.Column('timer_duration', sa.Integer(), nullable=True),
        sa.Column('timer_unit', sa.String(10), nullable=False, server_default='minutes'),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('target_node_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('oa_workflow_node.id'), nullable=True),
        sa.Column('cancel_activity', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    op.create_index('idx_boundary_definition', 'oa_workflow_boundary_event', ['definition_id'], unique=False)
    op.create_index('idx_boundary_attached_node', 'oa_workflow_boundary_event', ['attached_node_id'], unique=False)
    op.create_index('idx_boundary_event_type', 'oa_workflow_boundary_event', ['event_type'], unique=False)
    
    # ==========================================
    # 7. 新增定时任务表
    # ==========================================
    op.create_table(
        'oa_workflow_timer_job',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('instance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('oa_workflow_instance.id', ondelete='CASCADE'), nullable=False),
        sa.Column('node_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('oa_workflow_node.id'), nullable=False),
        sa.Column('boundary_event_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('oa_workflow_boundary_event.id'), nullable=False),
        sa.Column('trigger_time', sa.TIMESTAMP(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='PENDING'),
        sa.Column('result', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    op.create_index('idx_timer_job_instance', 'oa_workflow_timer_job', ['instance_id'], unique=False)
    op.create_index('idx_timer_job_trigger_time', 'oa_workflow_timer_job', ['trigger_time'], unique=False)
    op.create_index('idx_timer_job_status', 'oa_workflow_timer_job', ['status'], unique=False)
    
    # ==========================================
    # 8. 新增通知设置表
    # ==========================================
    op.create_table(
        'oa_workflow_notification_setting',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('push_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('wechat_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('email_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sms_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('notify_on_assigned', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notify_on_overdue', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notify_on_completed', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notify_on_instance_completed', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('dnd_periods', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    op.create_index('idx_notification_setting_user', 'oa_workflow_notification_setting', ['user_id'], unique=False)
    
    # ==========================================
    # 9. 新增离线操作表
    # ==========================================
    op.create_table(
        'oa_workflow_offline_action',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('oa_workflow_task.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('action_time', sa.TIMESTAMP(), nullable=False),
        sa.Column('sync_status', sa.String(20), nullable=False, server_default='PENDING'),
        sa.Column('sync_result', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    op.create_index('idx_offline_action_user', 'oa_workflow_offline_action', ['user_id'], unique=False)
    op.create_index('idx_offline_action_task', 'oa_workflow_offline_action', ['task_id'], unique=False)
    op.create_index('idx_offline_action_sync_status', 'oa_workflow_offline_action', ['sync_status'], unique=False)
    
    # ==========================================
    # 10. 增强 oa_workflow_node 表（新增字段）
    # ==========================================
    with op.batch_alter_table('oa_workflow_node') as batch_op:
        # 会签/或签配置
        batch_op.add_column(sa.Column('multi_instance_type', sa.String(20), nullable=True))
        batch_op.add_column(sa.Column('multi_instance_condition', sa.String(20), nullable=True))
        batch_op.add_column(sa.Column('multi_instance_count', sa.Integer(), nullable=True))
        
        # 并行网关配置
        batch_op.add_column(sa.Column('gateway_direction', sa.String(20), nullable=True))
        batch_op.add_column(sa.Column('parallel_group_id', postgresql.UUID(as_uuid=True), nullable=True))
        
        # 超时配置
        batch_op.add_column(sa.Column('timeout_duration', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('timeout_unit', sa.String(10), nullable=False, server_default='minutes'))
        batch_op.add_column(sa.Column('timeout_action', sa.String(20), nullable=True))
        batch_op.add_column(sa.Column('timeout_variable', sa.String(50), nullable=True))
        
        # 表单权限配置
        batch_op.add_column(sa.Column('field_permissions', postgresql.JSON(), nullable=True))
        
        # 节点位置（用于流程设计器）
        batch_op.add_column(sa.Column('position_x', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('position_y', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('width', sa.Integer(), nullable=False, server_default='120'))
        batch_op.add_column(sa.Column('height', sa.Integer(), nullable=False, server_default='80'))
        
        # 版本号
        batch_op.add_column(sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
        
        # 子流程配置
        batch_op.add_column(sa.Column('is_subflow', sa.Boolean(), nullable=False, server_default='false'))
        batch_op.add_column(sa.Column('subflow_definition_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('oa_workflow_definition.id'), nullable=True))
        batch_op.add_column(sa.Column('input_mapping', postgresql.JSON(), nullable=True))
        batch_op.add_column(sa.Column('output_mapping', postgresql.JSON(), nullable=True))
    
    # ==========================================
    # 11. 增强 oa_workflow_task 表（新增字段）
    # ==========================================
    with op.batch_alter_table('oa_workflow_task') as batch_op:
        # 多实例相关字段
        batch_op.add_column(sa.Column('multi_instance_total', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('multi_instance_index', sa.Integer(), nullable=True))
        
        # 版本号（用于乐观锁）
        batch_op.add_column(sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
        
        # 重试次数
        batch_op.add_column(sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))
        
        # 升级来源
        batch_op.add_column(sa.Column('escalated_from', postgresql.UUID(as_uuid=True), nullable=True))
    
    # ==========================================
    # 12. 增强 oa_workflow_definition 表（新增字段）
    # ==========================================
    with op.batch_alter_table('oa_workflow_definition') as batch_op:
        # 版本管理
        batch_op.add_column(sa.Column('current_version', sa.Integer(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('published_version', sa.Integer(), nullable=True))
        # 状态字段: draft-草稿, published-已发布, disabled-已禁用
        batch_op.add_column(sa.Column('status', sa.String(20), nullable=False, server_default='draft'))
    
    # ==========================================
    # 13. 创建索引（性能优化）
    # ==========================================
    # oa_workflow_node 索引
    op.create_index('idx_workflow_node_definition', 'oa_workflow_node', ['definition_id'], unique=False)
    op.create_index('idx_workflow_node_type', 'oa_workflow_node', ['node_type'], unique=False)
    
    # oa_workflow_instance 索引（如果还没有）
    # op.create_index('idx_workflow_instance_definition', 'oa_workflow_instance', ['definition_id'], unique=False)
    # op.create_index('idx_workflow_instance_status', 'oa_workflow_instance', ['status'], unique=False)
    # op.create_index('idx_workflow_instance_initiator', 'oa_workflow_instance', ['initiator_id'], unique=False)
    
    # oa_workflow_task 索引（如果还没有）
    # op.create_index('idx_workflow_task_instance', 'oa_workflow_task', ['instance_id'], unique=False)
    # op.create_index('idx_workflow_task_assignee', 'oa_workflow_task', ['assignee_id'], unique=False)
    # op.create_index('idx_workflow_task_status', 'oa_workflow_task', ['status'], unique=False)


def downgrade() -> None:
    # ==========================================
    # 反向迁移：删除新增的表和字段
    # ==========================================
    
    # 删除索引
    op.drop_index('idx_workflow_node_type', table_name='oa_workflow_node')
    op.drop_index('idx_workflow_node_definition', table_name='oa_workflow_node')
    
    # 增强 oa_workflow_definition 表（删除字段）
    with op.batch_alter_table('oa_workflow_definition') as batch_op:
        batch_op.drop_column('status')
        batch_op.drop_column('published_version')
        batch_op.drop_column('current_version')
    
    # 增强 oa_workflow_task 表（删除字段）
    with op.batch_alter_table('oa_workflow_task') as batch_op:
        batch_op.drop_column('escalated_from')
        batch_op.drop_column('retry_count')
        batch_op.drop_column('version')
        batch_op.drop_column('multi_instance_index')
        batch_op.drop_column('multi_instance_total')
    
    # 增强 oa_workflow_node 表（删除字段）
    with op.batch_alter_table('oa_workflow_node') as batch_op:
        batch_op.drop_column('output_mapping')
        batch_op.drop_column('input_mapping')
        batch_op.drop_column('subflow_definition_id')
        batch_op.drop_column('is_subflow')
        batch_op.drop_column('version')
        batch_op.drop_column('height')
        batch_op.drop_column('width')
        batch_op.drop_column('position_y')
        batch_op.drop_column('position_x')
        batch_op.drop_column('field_permissions')
        batch_op.drop_column('timeout_variable')
        batch_op.drop_column('timeout_action')
        batch_op.drop_column('timeout_unit')
        batch_op.drop_column('timeout_duration')
        batch_op.drop_column('parallel_group_id')
        batch_op.drop_column('gateway_direction')
        batch_op.drop_column('multi_instance_count')
        batch_op.drop_column('multi_instance_condition')
        batch_op.drop_column('multi_instance_type')
    
    # 删除表（按依赖顺序）
    op.drop_table('oa_workflow_offline_action')
    op.drop_table('oa_workflow_notification_setting')
    op.drop_table('oa_workflow_timer_job')
    op.drop_table('oa_workflow_boundary_event')
    op.drop_table('oa_workflow_subflow_instance')
    op.drop_table('oa_workflow_version')
    op.drop_table('oa_workflow_audit_log')
    op.drop_table('oa_workflow_branch_state')
    op.drop_table('oa_workflow_sequence_flow')
