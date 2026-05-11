"""
OA工作流核心模型

包含工作流定义、审批节点、审批实例、审批任务、流程变量等核心模型
"""
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import (
    Column, String, Integer, Text, DateTime, ForeignKey, 
    Boolean, JSON, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.soft_delete import SoftDeleteMixin
from app.models.timestamp import TimestampMixin


class OaWorkflowDefinition(Base, SoftDeleteMixin, TimestampMixin):
    """
    工作流定义（模板）

    定义一个工作流的结构和节点
    """
    __tablename__ = "oa_workflow_definition"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # 基本信息
    name = Column(String(100), nullable=False, comment="工作流名称")
    code = Column(String(50), nullable=False, unique=True, comment="工作流编码")
    description = Column(Text, nullable=True, comment="工作流描述")
    
    # 版本控制
    version = Column(Integer, default=1, nullable=False, comment="版本号")
    
    # 状态字段: draft-草稿, published-已发布, disabled-已禁用
    status = Column(String(20), default="draft", nullable=False, comment="状态")
    is_active = Column(Boolean, default=False, nullable=False, comment="是否启用")
    
    # 流程配置 (JSON)
    # 包含节点定义、路由规则等
    config = Column(JSON, nullable=True, comment="工作流配置")
    
    # 表单配置 (JSON)
    # 定义发起审批时需要填写的字段
    form_config = Column(JSON, nullable=True, comment="表单配置")
    
    # 业务类型标识
    business_type = Column(String(50), nullable=True, comment="关联业务类型")
    
    # 权限控制
    allow_withdraw = Column(Boolean, default=True, nullable=False, comment="允许撤回")
    allow_transfer = Column(Boolean, default=True, nullable=False, comment="允许转交")
    allow_cc = Column(Boolean, default=True, nullable=False, comment="允许抄送")
    
    # 发布信息
    published_at = Column(DateTime, nullable=True, comment="发布时间")
    published_by = Column(UUID(as_uuid=True), nullable=True, comment="发布人")
    
    # 关系
    nodes = relationship("OaWorkflowNode", back_populates="definition", 
                         cascade="all, delete-orphan", lazy="selectin")
    instances = relationship("OaWorkflowInstance", back_populates="definition",
                            cascade="all, delete-orphan", lazy="selectin")

    __table_args__ = (
        Index("idx_workflow_definition_code", "code"),
        Index("idx_workflow_definition_business_type", "business_type"),
        Index("idx_workflow_definition_active", "is_active"),
    )

    def __repr__(self):
        return f"<OaWorkflowDefinition(id={self.id}, name={self.name}, code={self.code})>"


class OaWorkflowNode(Base, SoftDeleteMixin, TimestampMixin):
    """
    审批节点

    定义工作流中的各个审批节点
    """
    __tablename__ = "oa_workflow_node"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # 所属工作流
    definition_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("oa_workflow_definition.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 节点基本信息
    name = Column(String(100), nullable=False, comment="节点名称")
    code = Column(String(50), nullable=True, comment="节点编码")
    node_type = Column(String(20), nullable=False, comment="节点类型: START/END/APPROVAL/CONDITION/CC/AUTO")
    
    # 位置信息
    order_index = Column(Integer, default=0, nullable=False, comment="顺序索引")
    
    # 审批配置 (JSON)
    # type=APPROVAL时: {approver_type, approver_rule, timeout_hours, auto_approve}
    # type=CONDITION时: {conditions, branches}
    # type=CC时: {cc_rule}
    # type=AUTO时: {action, params}
    config = Column(JSON, nullable=True, comment="节点配置")
    
    # 审批人规则 (JSON)
    # 支持: user/role/department_leader/direct_manager/multi_level/or/and
    approver_rule = Column(JSON, nullable=True, comment="审批人规则")
    
    # 超时配置
    timeout_hours = Column(Integer, nullable=True, comment="超时时限(小时)")
    timeout_action = Column(String(20), nullable=True, comment="超时动作: SKIP/AUTO_APPROVE/NOTIFY")
    
    # 条件表达式 (用于CONDITION节点)
    condition_expression = Column(Text, nullable=True, comment="条件表达式")
    
    # 节点分组 (用于并行节点)
    group_id = Column(UUID(as_uuid=True), nullable=True, comment="节点分组ID")
    
    # 关系
    definition = relationship("OaWorkflowDefinition", back_populates="nodes")
    tasks = relationship("OaWorkflowTask", back_populates="node", 
                        cascade="all, delete-orphan", lazy="selectin")

    __table_args__ = (
        Index("idx_workflow_node_definition", "definition_id"),
        Index("idx_workflow_node_type", "node_type"),
        Index("idx_workflow_node_order", "definition_id", "order_index"),
    )

    def __repr__(self):
        return f"<OaWorkflowNode(id={self.id}, name={self.name}, type={self.node_type})>"


class OaWorkflowInstance(Base, SoftDeleteMixin, TimestampMixin):
    """
    审批实例

    记录一次具体的审批流程
    """
    __tablename__ = "oa_workflow_instance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # 关联工作流定义
    definition_id = Column(
        UUID(as_uuid=True),
        ForeignKey("oa_workflow_definition.id"),
        nullable=False
    )
    
    # 关联业务数据
    business_type = Column(String(50), nullable=False, comment="业务类型")
    business_id = Column(UUID(as_uuid=True), nullable=False, comment="业务数据ID")
    
    # 发起人
    initiator_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    
    # 审批实例状态
    status = Column(String(20), default="PENDING", nullable=False, 
                   comment="状态: PENDING/APPROVING/APPROVED/REJECTED/CANCELLED/EXPIRED")
    
    # 审批进度
    current_node_id = Column(UUID(as_uuid=True), nullable=True, comment="当前节点ID")
    completed_node_ids = Column(JSON, nullable=True, comment="已完成的节点ID列表")
    
    # 审批意见汇总 (JSON)
    approval_summary = Column(JSON, nullable=True, comment="审批意见汇总")
    
    # 抄送列表 (JSON) - 用户ID列表
    cc_list = Column(JSON, nullable=True, comment="抄送列表")
    
    # 表单数据 (JSON)
    form_data = Column(JSON, nullable=True, comment="表单数据")
    
    # 标题和摘要
    title = Column(String(200), nullable=False, comment="审批标题")
    summary = Column(Text, nullable=True, comment="审批摘要")
    
    # 时间记录
    submitted_at = Column(DateTime, nullable=False, default=datetime.now, comment="提交时间")
    started_at = Column(DateTime, nullable=True, comment="开始审批时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    
    # 撤回信息
    cancelled_at = Column(DateTime, nullable=True, comment="撤回时间")
    cancel_reason = Column(Text, nullable=True, comment="撤回原因")

    # 催办记录
    last_urge_at = Column(DateTime, nullable=True, comment="最后催办时间")
    urge_count = Column(Integer, default=0, nullable=False, comment="催办次数")
    
    # 关系
    definition = relationship("OaWorkflowDefinition", back_populates="instances")
    tasks = relationship("OaWorkflowTask", back_populates="instance",
                        cascade="all, delete-orphan", lazy="selectin")
    initiator = relationship("User", foreign_keys=[initiator_id])

    __table_args__ = (
        Index("idx_workflow_instance_definition", "definition_id"),
        Index("idx_workflow_instance_business", "business_type", "business_id"),
        Index("idx_workflow_instance_initiator", "initiator_id"),
        Index("idx_workflow_instance_status", "status"),
        Index("idx_workflow_instance_submitted", "submitted_at"),
        UniqueConstraint("business_type", "business_id", name="uq_workflow_instance_business"),
    )

    def __repr__(self):
        return f"<OaWorkflowInstance(id={self.id}, title={self.title}, status={self.status})>"


class OaWorkflowTask(Base, SoftDeleteMixin, TimestampMixin):
    """
    审批任务

    记录每个节点的具体审批任务
    """
    __tablename__ = "oa_workflow_task"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # 关联审批实例
    instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("oa_workflow_instance.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 关联审批节点
    node_id = Column(
        UUID(as_uuid=True),
        ForeignKey("oa_workflow_node.id"),
        nullable=False
    )
    
    # 任务类型
    task_type = Column(String(20), nullable=False, 
                      comment="任务类型: APPROVAL/CC/AUTO/NOTIFY")
    
    # 任务状态
    status = Column(String(20), default="PENDING", nullable=False,
                   comment="状态: PENDING/APPROVED/REJECTED/TRANSFERRED/DELEGATED/SKIPPED/CANCELLED")
    
    # 审批人
    assignee_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    assignee_type = Column(String(20), nullable=True,
                          comment="审批人类型: USER/ROLE/DEPARTMENT")
    
    # 原始审批人 (用于转交/转派记录)
    original_assignee_id = Column(
        UUID(as_uuid=True),
        nullable=True
    )
    
    # 任务状态时间
    assigned_at = Column(DateTime, nullable=True, comment="分配时间")
    started_at = Column(DateTime, nullable=True, comment="开始处理时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    
    # 超时信息
    deadline = Column(DateTime, nullable=True, comment="截止时间")
    is_overdue = Column(Boolean, default=False, nullable=False, comment="是否超时")
    overdue_reminders = Column(Integer, default=0, nullable=False, comment="催办次数")
    
    # 审批意见
    comment = Column(Text, nullable=True, comment="审批意见")
    action = Column(String(20), nullable=True, comment="操作: APPROVE/REJECT/TRANSFER/DELEGATE/SKIP")
    
    # 转交/转派记录
    transfer_from = Column(UUID(as_uuid=True), nullable=True, comment="从谁转来")
    transfer_to = Column(UUID(as_uuid=True), nullable=True, comment="转给谁")
    transfer_reason = Column(Text, nullable=True, comment="转交原因")
    
    # 代理记录
    delegate_from = Column(UUID(as_uuid=True), nullable=True, comment="代理谁")
    delegate_to = Column(UUID(as_uuid=True), nullable=True, comment="代理给谁")
    
    # 顺序 (处理并行节点)
    order_index = Column(Integer, default=0, nullable=False, comment="处理顺序")
    
    # 是否必审批
    is_required = Column(Boolean, default=True, nullable=False, comment="是否必须审批")
    
    # 关系
    instance = relationship("OaWorkflowInstance", back_populates="tasks")
    node = relationship("OaWorkflowNode", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assignee_id])

    __table_args__ = (
        Index("idx_workflow_task_instance", "instance_id"),
        Index("idx_workflow_task_node", "node_id"),
        Index("idx_workflow_task_assignee", "assignee_id"),
        Index("idx_workflow_task_status", "status"),
        Index("idx_workflow_task_assignee_status", "assignee_id", "status"),
    )

    def __repr__(self):
        return f"<OaWorkflowTask(id={self.id}, status={self.status}, assignee_id={self.assignee_id})>"


class OaWorkflowVariable(Base, SoftDeleteMixin, TimestampMixin):
    """
    流程变量

    存储审批流程中的变量数据
    """
    __tablename__ = "oa_workflow_variable"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # 关联审批实例
    instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("oa_workflow_instance.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 变量名称
    name = Column(String(100), nullable=False, comment="变量名称")
    
    # 变量值
    value = Column(Text, nullable=True, comment="变量值")
    
    # 变量类型
    value_type = Column(String(20), nullable=False, default="STRING",
                       comment="类型: STRING/NUMBER/BOOLEAN/DATE/JSON/ARRAY")
    
    # 变量来源
    source = Column(String(20), nullable=True, 
                   comment="来源: SYSTEM/FORM/APPROVAL/CONDITION")
    
    # 所属节点 (可选，用于记录节点级别的变量)
    node_id = Column(
        UUID(as_uuid=True),
        ForeignKey("oa_workflow_node.id"),
        nullable=True
    )
    
    # 关系
    instance = relationship("OaWorkflowInstance", 
                           foreign_keys=[instance_id],
                           backref="variables")

    __table_args__ = (
        Index("idx_workflow_variable_instance", "instance_id"),
        Index("idx_workflow_variable_name", "instance_id", "name"),
    )

    def __repr__(self):
        return f"<OaWorkflowVariable(id={self.id}, name={self.name}, value={self.value})>"


class OaWorkflowCC(Base, SoftDeleteMixin, TimestampMixin):
    """
    审批抄送记录

    记录抄送给相关人员的信息
    """
    __tablename__ = "oa_workflow_cc"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # 关联审批实例
    instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("oa_workflow_instance.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # 抄送人
    cc_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    
    # 抄送时间
    cc_at = Column(DateTime, nullable=False, default=datetime.now, comment="抄送时间")
    
    # 阅读状态
    is_read = Column(Boolean, default=False, nullable=False, comment="是否已读")
    read_at = Column(DateTime, nullable=True, comment="阅读时间")
    
    # 抄送原因
    reason = Column(String(200), nullable=True, comment="抄送原因")
    
    # 关系
    instance = relationship("OaWorkflowInstance", backref="cc_records")
    cc_user = relationship("User", foreign_keys=[cc_user_id])

    __table_args__ = (
        Index("idx_workflow_cc_instance", "instance_id"),
        Index("idx_workflow_cc_user", "cc_user_id"),
        Index("idx_workflow_cc_user_unread", "cc_user_id", "is_read"),
    )

    def __repr__(self):
        return f"<OaWorkflowCC(id={self.id}, cc_user_id={self.cc_user_id}, is_read={self.is_read})>"
