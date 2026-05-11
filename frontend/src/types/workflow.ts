/**
 * 工作流模块类型定义
 * 与后端 Pydantic Schema 及 SQLAlchemy Model 对齐
 */

// ============================================================
// 枚举类型
// ============================================================

/** 工作流实例状态 */
export enum InstanceStatus {
  PENDING = 'PENDING',       // 待审批（已提交，等待第一个审批人）
  APPROVING = 'APPROVING',  // 审批中
  APPROVED = 'APPROVED',     // 已通过
  REJECTED = 'REJECTED',     // 已拒绝
  CANCELLED = 'CANCELLED',   // 已撤回
  EXPIRED = 'EXPIRED',       // 已超时
}

/** 工作流节点类型 */
export enum NodeType {
  START = 'START',       // 开始节点
  END = 'END',           // 结束节点
  APPROVAL = 'APPROVAL', // 审批节点
  CONDITION = 'CONDITION', // 条件节点
  CC = 'CC',             // 抄送节点
}

/** 审批动作 */
export enum ApproveAction {
  APPROVE = 'APPROVE',   // 通过
  REJECT = 'REJECT',      // 拒绝
  TRANSFER = 'TRANSFER',  // 转交
  DELEGATE = 'DELEGATE',  // 转派
  URGE = 'URGE',          // 催办
}

/** 超时处理方式 */
export enum TimeoutAction {
  NOTIFY = 'NOTIFY',         // 仅提醒
  AUTO_APPROVE = 'AUTO_APPROVE', // 自动通过
  AUTO_REJECT = 'AUTO_REJECT',   // 自动拒绝
  ESCALATE = 'ESCALATE',     // 升级处理
}

/** 审批人规则类型 */
export enum ApproverRuleType {
  USER = 'USER',             // 指定用户
  ROLE = 'ROLE',             // 指定角色
  DEPARTMENT_LEADER = 'DEPARTMENT_LEADER', // 部门主管
  MULTI_LEVEL_LEADER = 'MULTI_LEVEL_LEADER', // 多级主管
  FORM_FIELD = 'FORM_FIELD', // 表单字段
  SCRIPT = 'SCRIPT',         // 脚本计算
  CUSTOM = 'CUSTOM',         // 自定义
}

// ============================================================
// 条件表达式类型
// ============================================================

/** 简单条件（三段式） */
export interface SimpleCondition {
  field: string;      // 字段路径，如 "form.amount"
  operator: '==' | '!=' | '>' | '>=' | '<' | '<=' | 'in' | 'not_in' | 'contains';
  value: string | number | boolean | string[] | number[];
}

/** 条件表达式（支持嵌套） */
export interface ConditionExpression {
  op: 'AND' | 'OR' | 'NOT';
  conditions?: ConditionExpression[];
  condition?: SimpleCondition;  // NOT 操作符使用
}

// ============================================================
// 审批人规则
// ============================================================

export interface ApproverRule {
  type: ApproverRuleType;
  user_ids?: string[];
  role_ids?: string[];
  department_ids?: string[];
  field_name?: string;        // FORM_FIELD 类型时使用的表单字段名
  script?: string;            // SCRIPT 类型时的脚本内容
}

// ============================================================
// 工作流节点
// ============================================================

export interface WorkflowNode {
  id: string;
  name: string;
  code: string;
  node_type: NodeType;
  order_index: number;
  approver_rule?: ApproverRule;
  config?: Record<string, any>;
  timeout_hours?: number;
  timeout_action?: TimeoutAction;
  condition_expression?: ConditionExpression;
  is_current?: boolean;
  is_completed?: boolean;
  is_pending?: boolean;
  operator_name?: string;
  completed_at?: string;
  tasks?: WorkflowTask[];
}

/** 工作流定义状态 */
export enum DefinitionStatus {
  DRAFT = 'draft',       // 草稿状态（不可发起审批）
  PUBLISHED = 'published', // 已发布（可发起审批）
  DISABLED = 'disabled',  // 已禁用（不可发起审批）
}

// ============================================================
// 工作流定义
// ============================================================

export interface WorkflowDefinition {
  id: string;
  name: string;
  code: string;
  description?: string;
  category?: string;
  business_type?: string;
  version: number;
  status: DefinitionStatus;  // 工作流定义状态: draft/published/disabled
  is_active: boolean;        // 是否启用（功能开关）
  form_config?: FormConfig;
  allow_withdraw: boolean;
  allow_transfer: boolean;
  allow_cc: boolean;
  allow_urge?: boolean;
  allow_all_initiator?: boolean;
  allowed_roles?: string[];
  allowed_departments?: string[];
  nodes?: WorkflowNode[];
  instance_count?: number;
  created_at?: string;
  updated_at?: string;
  published_at?: string;
  published_by?: string;
}

/** 表单字段配置 */
export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'textarea' | 'number' | 'date' | 'datetime' | 'select' | 'checkbox' | 'radio' | 'file';
  required?: boolean;
  options?: { label: string; value: string }[];
  placeholder?: string;
  default_value?: any;
}

/** 表单配置 */
export interface FormConfig {
  fields: FormField[];
  layout?: 'single' | 'double';
}

// ============================================================
// 工作流实例
// ============================================================

export interface WorkflowInstance {
  id: string;
  instance_id: string;
  workflow_id: string;
  workflow_name?: string;
  workflow_code?: string;
  business_type?: string;
  business_id?: string;
  title: string;
  description?: string;
  form_data?: Record<string, any>;
  form_fields?: FormField[];
  status: InstanceStatus;
  result?: string;
  current_node_id?: string;
  current_node_name?: string;
  can_withdraw?: boolean;
  can_urge?: boolean;
  urge_count?: number;
  last_urge_at?: string;
  is_overdue?: boolean;
  initiator_id: string;
  initiator_name?: string;
  created_at?: string;
  updated_at?: string;
  completed_at?: string;
  nodes?: WorkflowNode[];
  histories?: WorkflowHistory[];
  attachments?: WorkflowAttachment[];
  cc_list?: WorkflowCC[];
}

// ============================================================
// 审批任务
// ============================================================

export interface WorkflowTask {
  id: string;
  instance_id: string;
  node_id: string;
  node_name?: string;
  workflow_name?: string;
  title?: string;
  assignee_id: string;
  assignee_name?: string;
  action?: ApproveAction;
  comment?: string;
  status: 'PENDING' | 'COMPLETED' | 'TRANSFERRED' | 'DELEGATED';
  is_read?: boolean;
  is_overdue?: boolean;
  due_at?: string;
  processed_at?: string;
  created_at?: string;
  updated_at?: string;
}

// ============================================================
// 审批历史
// ============================================================

export interface WorkflowHistory {
  id: string;
  action: ApproveAction;
  node_name?: string;
  operator_id: string;
  operator_name?: string;
  comment?: string;
  attachment_count?: number;
  created_at?: string;
}

// ============================================================
// 抄送
// ============================================================

export interface WorkflowCC {
  id: string;
  instance_id: string;
  user_id: string;
  user_name?: string;
  is_read?: boolean;
  read_at?: string;
  created_at?: string;
}

// ============================================================
// 附件
// ============================================================

export interface WorkflowAttachment {
  id: string;
  filename: string;
  size: number;
  url: string;
  uploaded_by?: string;
  uploaded_at?: string;
}

// ============================================================
// 统计数据
// ============================================================

/** 统计摘要 */
export interface WorkflowStatisticsSummary {
  total: number;
  approved: number;
  rejected: number;
  cancelled: number;
  in_progress: number;
  approve_rate: number;
  avg_duration_hours: number;
}

/** 按类型统计 */
export interface WorkflowStatisticsByType {
  business_type: string;
  total: number;
  approved: number;
  rejected: number;
  approve_rate: number;
}

/** 完整统计数据 */
export interface WorkflowStatistics {
  summary: WorkflowStatisticsSummary;
  by_type: WorkflowStatisticsByType[];
}

// ============================================================
// 请求参数类型
// ============================================================

/** 发起审批请求 */
export interface StartInstanceRequest {
  workflow_id: string;
  business_type: string;
  business_id: string;
  title: string;
  context?: Record<string, any>;
  cc_list?: string[];
  summary?: string;
}

/** 催办请求 */
export interface UrgeRequest {
  message?: string;
}

/** 审批操作请求 */
export interface ApproveRequest {
  comment?: string;
}

/** 拒绝请求 */
export interface RejectRequest {
  comment: string;
}

/** 转交请求 */
export interface TransferRequest {
  target_user_id: string;
  comment?: string;
}

/** 转派请求 */
export interface DelegateRequest {
  delegate_to: string;
  comment?: string;
}

/** 工作流定义查询参数 */
export interface WorkflowDefinitionQuery {
  page?: number;
  page_size?: number;
  name?: string;
  status?: 'active' | 'inactive';
}

/** 工作流实例查询参数 */
export interface WorkflowInstanceQuery {
  page?: number;
  page_size?: number;
  status?: InstanceStatus;
  business_type?: string;
}

/** 工作流统计查询参数 */
export interface WorkflowStatisticsQuery {
  start_date?: string;   // YYYY-MM-DD
  end_date?: string;     // YYYY-MM-DD
  business_type?: string;
}

/** 审批任务查询参数 */
export interface WorkflowTaskQuery {
  page?: number;
  page_size?: number;
  status?: string;
}

// ============================================================
// 分页响应
// ============================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// ============================================================
// 后端响应包装
// ============================================================

export interface ApiResponse<T> {
  code: number;
  message?: string;
  data: T;
}

export interface ApiPageResponse<T> {
  code: number;
  message?: string;
  data: {
    items: T[];
    total: number;
    page: number;
    page_size: number;
  };
}
