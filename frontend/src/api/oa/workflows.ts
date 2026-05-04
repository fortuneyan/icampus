import request from '@/utils/request'

// 工作流定义API
export const workflowApi = {
  // 获取工作流列表
  getList: (params?: any) => {
    return request.get('/oa/workflows/', { params })
  },

  // 获取工作流详情
  getById: (id: string) => {
    return request.get(`/oa/workflows/${id}/`)
  },

  // 创建工作流
  create: (data: any) => {
    return request.post('/oa/workflows/', data)
  },

  // 更新工作流
  update: (id: string, data: any) => {
    return request.put(`/oa/workflows/${id}/`, data)
  },

  // 删除工作流
  delete: (id: string) => {
    return request.delete(`/oa/workflows/${id}/`)
  },

  // 发布工作流
  publish: (id: string) => {
    return request.post(`/oa/workflows/${id}/publish`)
  },

  // 获取工作流节点
  getNodes: (workflowId: string) => {
    return request.get(`/oa/workflows/${workflowId}/nodes/`)
  },

  // 保存工作流节点
  saveNodes: (workflowId: string, data: any) => {
    return request.post(`/oa/workflows/${workflowId}/nodes/`, data)
  }
}

// 审批实例API
export const instanceApi = {
  // 发起审批
  start: (data: any) => {
    return request.post('/oa/workflows/instances', data)
  },

  // 获取我的审批列表
  getMyList: (params?: any) => {
    return request.get('/oa/workflows/instances', { params })
  },

  // 获取待我审批列表
  getTodoList: (params?: any) => {
    return request.get('/oa/workflows/tasks', { params })
  },

  // 获取我已审批列表
  getDoneList: (params?: any) => {
    return request.get('/oa/workflows/instances/done', { params })
  },

  // 获取审批详情
  getById: (id: string) => {
    return request.get(`/oa/workflows/instances/${id}`)
  },

  // 审批操作
  approve: (id: string, data: any) => {
    return request.post(`/oa/workflows/tasks/${id}/approve`, data)
  },

  // 转交
  transfer: (id: string, data: any) => {
    return request.post(`/oa/workflows/tasks/${id}/transfer`, data)
  },

  // 撤回
  withdraw: (id: string) => {
    return request.post(`/oa/workflows/instances/${id}/cancel`)
  },

  // 催办
  urge: (id: string) => {
    return request.post(`/oa/workflows/instances/${id}/urge`)
  }
}

// 审批任务API
export const taskApi = {
  // 获取任务列表
  getList: (params?: any) => {
    return request.get('/oa/workflows/tasks', { params })
  },

  // 获取任务详情
  getById: (id: string) => {
    return request.get(`/oa/workflows/tasks/${id}`)
  },

  // 完成任务
  complete: (id: string, data: any) => {
    return request.post(`/oa/workflows/tasks/${id}/approve`, data)
  },

  // 转交任务
  transfer: (id: string, data: any) => {
    return request.post(`/oa/workflows/tasks/${id}/transfer`, data)
  }
}

// 抄送API
export const ccApi = {
  // 获取抄送我的列表
  getMyList: (params?: any) => {
    return request.get('/oa/workflows/cc', { params })
  },

  // 标记已读
  markRead: (id: string) => {
    return request.post(`/oa/workflows/cc/${id}/read`)
  }
}
