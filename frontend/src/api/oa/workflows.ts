import request from '@/utils/request'
import type {
  WorkflowDefinition,
  WorkflowInstance,
  WorkflowTask,
  WorkflowNode,
  StartInstanceRequest,
  UrgeRequest,
  WorkflowStatisticsQuery,
  WorkflowStatistics,
  PaginatedResponse,
  ApiResponse,
  ApproveAction,
} from '@/types/workflow'

// ============================================================
// 工作流定义 API
// ============================================================

export const workflowApi = {
  /**
   * 获取工作流定义列表（分页）
   */
  getList: (params?: {
    page?: number;
    page_size?: number;
    name?: string;
    status?: string;
  }) => {
    return request.get<any, ApiResponse<PaginatedResponse<WorkflowDefinition>>>('/oa/workflows/', { params })
  },

  /**
   * 获取工作流定义详情
   */
  getById: (id: string) => {
    return request.get<any, ApiResponse<WorkflowDefinition>>(`/oa/workflows/${id}/`)
  },

  /**
   * 创建工作流定义
   */
  create: (data: Partial<WorkflowDefinition> & { nodes?: Partial<WorkflowNode>[] }) => {
    return request.post<any, ApiResponse<{ id: string }>>('/oa/workflows/', data)
  },

  /**
   * 更新工作流定义
   */
  update: (id: string, data: Partial<WorkflowDefinition> & { nodes?: Partial<WorkflowNode>[] }) => {
    return request.put<any, ApiResponse<{ id: string }>>(`/oa/workflows/${id}/`, data)
  },

  /**
   * 删除工作流定义
   */
  delete: (id: string) => {
    return request.delete<any, ApiResponse<{ id: string }>>(`/oa/workflows/${id}/`)
  },

  /**
   * 发布工作流
   */
  publish: (id: string) => {
    return request.post<any, ApiResponse<{ id: string }>>(`/oa/workflows/${id}/publish`)
  },

  /**
   * 获取工作流节点
   */
  getNodes: (workflowId: string) => {
    return request.get<any, ApiResponse<WorkflowNode[]>>(`/oa/workflows/${workflowId}/nodes/`)
  },

  /**
   * 保存工作流节点
   */
  saveNodes: (workflowId: string, data: Partial<WorkflowNode>[]) => {
    return request.post<any, ApiResponse<void>>(`/oa/workflows/${workflowId}/nodes/`, data)
  },

  /**
   * 获取工作流定义列表（不分页，用于下拉选择）
   */
  getDefinitions: () => {
    return request.get<any, ApiResponse<WorkflowDefinition[]>>('/oa/workflows/definitions')
  },
}

// ============================================================
// 审批实例 API
// ============================================================

export const instanceApi = {
  /**
   * 发起审批
   */
  start: (data: StartInstanceRequest) => {
    return request.post<any, ApiResponse<{ id: string }>>('/oa/workflows/instances', data)
  },

  /**
   * 获取我的审批列表（我发起的）
   */
  getMyList: (params?: {
    page?: number;
    page_size?: number;
    status?: string;
  }) => {
    return request.get<any, ApiResponse<PaginatedResponse<WorkflowInstance>>>('/oa/workflows/instances', { params })
  },

  /**
   * 获取待我审批列表
   */
  getTodoList: (params?: {
    page?: number;
    page_size?: number;
  }) => {
    return request.get<any, ApiResponse<PaginatedResponse<WorkflowTask>>>('/oa/workflows/tasks', { params })
  },

  /**
   * 获取我已审批列表
   */
  getDoneList: (params?: {
    page?: number;
    page_size?: number;
  }) => {
    return request.get<any, ApiResponse<PaginatedResponse<WorkflowInstance>>>('/oa/workflows/instances/done', { params })
  },

  /**
   * 获取审批详情
   */
  getById: (id: string) => {
    return request.get<any, ApiResponse<WorkflowInstance>>(`/oa/workflows/instances/${id}`)
  },

  /**
   * 审批通过
   */
  approve: (id: string, data?: { comment?: string }) => {
    return request.post<any, ApiResponse<{ id: string }>>(`/oa/workflows/tasks/${id}/approve`, data)
  },

  /**
   * 审批拒绝
   */
  reject: (id: string, data: { comment: string }) => {
    return request.post<any, ApiResponse<{ id: string }>>(`/oa/workflows/tasks/${id}/reject`, data)
  },

  /**
   * 转交任务
   */
  transfer: (id: string, data: { target_user_id: string; comment?: string }) => {
    return request.post<any, ApiResponse<{ id: string }>>(`/oa/workflows/tasks/${id}/transfer`, data)
  },

  /**
   * 转派任务
   */
  delegate: (id: string, data: { delegate_to: string; comment?: string }) => {
    return request.post<any, ApiResponse<{ id: string }>>(`/oa/workflows/tasks/${id}/delegate`, data)
  },

  /**
   * 撤回申请
   */
  withdraw: (id: string) => {
    return request.post<any, ApiResponse<{ id: string }>>(`/oa/workflows/instances/${id}/cancel`)
  },

  /**
   * 催办
   */
  urge: (id: string, data?: UrgeRequest) => {
    return request.post<any, ApiResponse<{ instance_id: string; urge_count: number; notified_users: number }>>(`/oa/workflows/instances/${id}/urge`, data)
  },

  /**
   * 获取工作流统计数据
   */
  getStatistics: (params?: WorkflowStatisticsQuery) => {
    return request.get<any, ApiResponse<WorkflowStatistics>>('/oa/workflows/statistics', { params })
  },
}

// ============================================================
// 审批任务 API
// ============================================================

export const taskApi = {
  /**
   * 获取任务列表（待我审批）
   */
  getList: (params?: {
    page?: number;
    page_size?: number;
  }) => {
    return request.get<any, ApiResponse<PaginatedResponse<WorkflowTask>>>('/oa/workflows/tasks', { params })
  },

  /**
   * 获取任务详情
   */
  getById: (id: string) => {
    return request.get<any, ApiResponse<WorkflowTask>>(`/oa/workflows/tasks/${id}`)
  },

  /**
   * 完成任务（审批通过）
   */
  complete: (id: string, data?: { comment?: string }) => {
    return request.post<any, ApiResponse<{ id: string }>>(`/oa/workflows/tasks/${id}/approve`, data)
  },

  /**
   * 转交任务
   */
  transfer: (id: string, data: { target_user_id: string; comment?: string }) => {
    return request.post<any, ApiResponse<{ id: string }>>(`/oa/workflows/tasks/${id}/transfer`, data)
  },

  /**
   * 转派任务
   */
  delegate: (id: string, data: { delegate_to: string; comment?: string }) => {
    return request.post<any, ApiResponse<{ id: string }>>(`/oa/workflows/tasks/${id}/delegate`, data)
  },

  /**
   * 拒绝审批
   */
  reject: (id: string, data: { comment: string }) => {
    return request.post<any, ApiResponse<{ id: string }>>(`/oa/workflows/tasks/${id}/reject`, data)
  },

  /**
   * 催办
   */
  urge: (id: string) => {
    return request.post<any, ApiResponse<{ instance_id: string }>>(`/oa/workflows/tasks/${id}/urge`)
  },
}

// ============================================================
// 抄送 API
// ============================================================

export const ccApi = {
  /**
   * 获取抄送我的列表
   */
  getMyList: (params?: {
    page?: number;
    page_size?: number;
  }) => {
    return request.get<any, ApiResponse<PaginatedResponse<any>>>('/oa/workflows/cc', { params })
  },

  /**
   * 标记已读
   */
  markRead: (id: string) => {
    return request.post<any, ApiResponse<void>>(`/oa/workflows/cc/${id}/read`)
  },
}

// ============================================================
// 条件表达式校验 API（前端本地校验，无需调用后端）
// ============================================================

/**
 * 校验条件表达式是否合法
 * @param expression 条件表达式
 * @returns 是否合法
 */
export const validateConditionExpression = (expression: any): boolean => {
  if (!expression) return true

  // 简单三段式校验
  if (expression.field && expression.operator && expression.value !== undefined) {
    return true
  }

  // 复合表达式校验
  if (expression.op && ['AND', 'OR', 'NOT'].includes(expression.op)) {
    if (expression.op === 'NOT') {
      return !!expression.condition
    }
    if (expression.conditions && Array.isArray(expression.conditions)) {
      return expression.conditions.every((c: any) => validateConditionExpression(c))
    }
  }

  return false
}

/**
 * 格式化条件表达式为人类可读文本
 */
export const formatConditionExpression = (expression: any, fields?: { name: string; label: string }[]): string => {
  if (!expression) return '无'

  const getFieldLabel = (fieldName: string): string => {
    if (fields) {
      const field = fields.find(f => f.name === fieldName)
      if (field) return field.label
    }
    return fieldName
  }

  const getOperatorText = (op: string): string => {
    const map: Record<string, string> = {
      '==': '等于',
      '!=': '不等于',
      '>': '大于',
      '>=': '大于等于',
      '<': '小于',
      '<=': '小于等于',
      'in': '包含于',
      'not_in': '不包含于',
      'contains': '包含',
    }
    return map[op] || op
  }

  // 简单三段式
  if (expression.field) {
    return `${getFieldLabel(expression.field)} ${getOperatorText(expression.operator)} ${expression.value}`
  }

  // 复合表达式
  if (expression.op === 'NOT') {
    return `非 (${formatConditionExpression(expression.condition, fields)})`
  }

  if (expression.conditions && Array.isArray(expression.conditions)) {
    const parts = expression.conditions.map((c: any) => formatConditionExpression(c, fields))
    const joiner = expression.op === 'AND' ? ' 且 ' : ' 或 '
    return parts.join(joiner)
  }

  return '未知条件'
}
