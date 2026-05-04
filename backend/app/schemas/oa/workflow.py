"""
OA工作流Schema定义

包含工作流定义、审批节点、审批实例、审批任务、流程变量的Pydantic Schema
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# WorkflowDefinition Schemas
# ============================================================================

class WorkflowDefinitionCreate(BaseModel):
    """创建工作流定义"""
    name: str = Field(..., min_length=1, max_length=100, description="工作流名称")
    code: str = Field(..., min_length=1, max_length=50, description="工作流编码")
    description: Optional[str] = Field(None, description="工作流描述")
    business_type: Optional[str] = Field(None, max_length=50, description="关联业务类型")
    config: Optional[Dict[str, Any]] = Field(None, description="工作流配置")
    form_config: Optional[Dict[str, Any]] = Field(None, description="表单配置")
    allow_withdraw: bool = Field(True, description="允许撤回")
    allow_transfer: bool = Field(True, description="允许转交")
    allow_cc: bool = Field(True, description="允许抄送")


class WorkflowDefinitionUpdate(BaseModel):
    """更新工作流定义"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    config: Optional[Dict[str, Any]] = Field(None, description="工作流配置")
    form_config: Optional[Dict[str, Any]] = Field(None, description="表单配置")
    is_active: Optional[bool] = Field(None, description="是否启用")
    allow_withdraw: Optional[bool] = Field(None, description="允许撤回")
    allow_transfer: Optional[bool] = Field(None, description="允许转交")
    allow_cc: Optional[bool] = Field(None, description="允许抄送")


class WorkflowDefinitionOut(BaseModel):
    """工作流定义输出"""
    id: UUID
    name: str
    code: str
    description: Optional[str] = None
    version: int
    is_active: bool
    business_type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    form_config: Optional[Dict[str, Any]] = None
    allow_withdraw: bool
    allow_transfer: bool
    allow_cc: bool
    published_at: Optional[datetime] = None
    published_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkflowDefinitionListOut(BaseModel):
    """工作流定义列表项"""
    id: UUID
    name: str
    code: str
    version: int
    is_active: bool
    business_type: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# WorkflowNode Schemas
# ============================================================================

class WorkflowNodeCreate(BaseModel):
    """创建审批节点"""
    name: str = Field(..., min_length=1, max_length=100, description="节点名称")
    code: Optional[str] = Field(None, max_length=50, description="节点编码")
    node_type: str = Field(..., description="节点类型: START/END/APPROVAL/CONDITION/CC/AUTO")
    order_index: int = Field(0, description="顺序索引")
    config: Optional[Dict[str, Any]] = Field(None, description="节点配置")
    approver_rule: Optional[Dict[str, Any]] = Field(None, description="审批人规则")
    timeout_hours: Optional[int] = Field(None, description="超时时限(小时)")
    timeout_action: Optional[str] = Field(None, description="超时动作: SKIP/AUTO_APPROVE/NOTIFY")
    condition_expression: Optional[str] = Field(None, description="条件表达式")
    group_id: Optional[UUID] = Field(None, description="节点分组ID")
    is_required: bool = Field(True, description="是否必须审批")


class WorkflowNodeUpdate(BaseModel):
    """更新审批节点"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="节点名称")
    code: Optional[str] = Field(None, max_length=50, description="节点编码")
    node_type: Optional[str] = Field(None, description="节点类型")
    order_index: Optional[int] = Field(None, description="顺序索引")
    config: Optional[Dict[str, Any]] = Field(None, description="节点配置")
    approver_rule: Optional[Dict[str, Any]] = Field(None, description="审批人规则")
    timeout_hours: Optional[int] = Field(None, description="超时时限(小时)")
    timeout_action: Optional[str] = Field(None, description="超时动作")
    condition_expression: Optional[str] = Field(None, description="条件表达式")
    is_required: Optional[bool] = Field(None, description="是否必须审批")


class WorkflowNodeOut(BaseModel):
    """审批节点输出"""
    id: UUID
    definition_id: UUID
    name: str
    code: Optional[str] = None
    node_type: str
    order_index: int
    config: Optional[Dict[str, Any]] = None
    approver_rule: Optional[Dict[str, Any]] = None
    timeout_hours: Optional[int] = None
    timeout_action: Optional[str] = None
    condition_expression: Optional[str] = None
    group_id: Optional[UUID] = None
    is_required: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# WorkflowInstance Schemas
# ============================================================================

class WorkflowInstanceCreate(BaseModel):
    """创建审批实例"""
    definition_id: UUID = Field(..., description="工作流定义ID")
    business_type: str = Field(..., max_length=50, description="业务类型")
    business_id: UUID = Field(..., description="业务数据ID")
    title: str = Field(..., max_length=200, description="审批标题")
    summary: Optional[str] = Field(None, description="审批摘要")
    form_data: Optional[Dict[str, Any]] = Field(None, description="表单数据")
    cc_list: Optional[List[UUID]] = Field(None, description="抄送用户ID列表")


class WorkflowInstanceOut(BaseModel):
    """审批实例输出"""
    id: UUID
    definition_id: UUID
    definition: Optional[WorkflowDefinitionOut] = None
    business_type: str
    business_id: UUID
    initiator_id: UUID
    initiator_name: Optional[str] = None
    status: str
    current_node_id: Optional[UUID] = None
    completed_node_ids: Optional[List[UUID]] = None
    approval_summary: Optional[Dict[str, Any]] = None
    cc_list: Optional[List[UUID]] = None
    form_data: Optional[Dict[str, Any]] = None
    title: str
    summary: Optional[str] = None
    submitted_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancel_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkflowInstanceListOut(BaseModel):
    """审批实例列表项"""
    id: UUID
    definition_id: UUID
    definition_name: Optional[str] = None
    business_type: str
    business_id: UUID
    initiator_id: UUID
    initiator_name: Optional[str] = None
    status: str
    title: str
    submitted_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WorkflowInstanceCancel(BaseModel):
    """撤回审批实例"""
    reason: Optional[str] = Field(None, description="撤回原因")


# ============================================================================
# WorkflowTask Schemas
# ============================================================================

class WorkflowTaskOut(BaseModel):
    """审批任务输出"""
    id: UUID
    instance_id: UUID
    node_id: UUID
    node_name: Optional[str] = None
    task_type: str
    status: str
    assignee_id: Optional[UUID] = None
    assignee_name: Optional[str] = None
    assignee_type: Optional[str] = None
    original_assignee_id: Optional[UUID] = None
    assigned_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    is_overdue: bool
    overdue_reminders: int
    comment: Optional[str] = None
    action: Optional[str] = None
    order_index: int
    is_required: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WorkflowTaskListOut(BaseModel):
    """审批任务列表项"""
    id: UUID
    instance_id: UUID
    node_id: UUID
    node_name: Optional[str] = None
    task_type: str
    status: str
    assignee_id: Optional[UUID] = None
    assignee_name: Optional[str] = None
    title: Optional[str] = None  # 来自instance
    business_type: Optional[str] = None
    assigned_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    is_overdue: bool

    class Config:
        from_attributes = True


class TaskAction(BaseModel):
    """审批任务操作"""
    action: str = Field(..., description="操作类型: APPROVE/REJECT/TRANSFER/DELEGATE")
    comment: Optional[str] = Field(None, description="审批意见")
    transfer_to: Optional[UUID] = Field(None, description="转交给谁")
    transfer_reason: Optional[str] = Field(None, description="转交原因")
    delegate_to: Optional[UUID] = Field(None, description="代理给谁")


class TaskTransfer(BaseModel):
    """转交任务"""
    transfer_to: UUID = Field(..., description="转交给谁")
    reason: Optional[str] = Field(None, description="转交原因")


class TaskDelegate(BaseModel):
    """代理任务"""
    delegate_to: UUID = Field(..., description="代理给谁")
    reason: Optional[str] = Field(None, description="代理原因")


# ============================================================================
# WorkflowCC Schemas
# ============================================================================

class WorkflowCCOut(BaseModel):
    """抄送记录输出"""
    id: UUID
    instance_id: UUID
    instance_title: Optional[str] = None
    business_type: Optional[str] = None
    cc_user_id: UUID
    cc_user_name: Optional[str] = None
    cc_at: datetime
    is_read: bool
    read_at: Optional[datetime] = None
    reason: Optional[str] = None

    class Config:
        from_attributes = True


class WorkflowCCMarkRead(BaseModel):
    """标记抄送已读"""
    pass


# ============================================================================
# WorkflowVariable Schemas
# ============================================================================

class WorkflowVariableSchema(BaseModel):
    """流程变量Schema"""
    name: str = Field(..., max_length=100, description="变量名称")
    value: Optional[str] = Field(None, description="变量值")
    value_type: str = Field("STRING", description="类型: STRING/NUMBER/BOOLEAN/DATE/JSON/ARRAY")
    source: Optional[str] = Field(None, description="来源: SYSTEM/FORM/APPROVAL/CONDITION")


class WorkflowVariableCreate(WorkflowVariableSchema):
    """创建流程变量"""
    pass


class WorkflowVariableOut(WorkflowVariableSchema):
    """流程变量输出"""
    id: UUID
    instance_id: UUID
    node_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Query Schemas
# ============================================================================

class WorkflowInstanceQuery(BaseModel):
    """审批实例查询参数"""
    status: Optional[str] = Field(None, description="状态过滤")
    business_type: Optional[str] = Field(None, description="业务类型过滤")
    keyword: Optional[str] = Field(None, description="关键词搜索")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")


class WorkflowTaskQuery(BaseModel):
    """审批任务查询参数"""
    status: Optional[str] = Field(None, description="状态过滤")
    task_type: Optional[str] = Field(None, description="任务类型过滤")
    is_overdue: Optional[bool] = Field(None, description="是否超时")


class WorkflowCCQuery(BaseModel):
    """抄送记录查询参数"""
    is_read: Optional[bool] = Field(None, description="是否已读")
    business_type: Optional[str] = Field(None, description="业务类型过滤")
