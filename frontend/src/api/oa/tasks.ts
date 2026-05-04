import request from '@/utils/request'

// 任务看板API
export const taskBoardApi = {
  // 获取看板列表
  getBoardList: (params?: any) => {
    return request.get('/oa/task-boards', { params })
  },

  // 获取看板详情
  getBoardById: (id: string) => {
    return request.get(`/oa/task-boards/${id}`)
  },

  // 创建看板
  createBoard: (data: any) => {
    return request.post('/oa/task-boards', data)
  },

  // 更新看板
  updateBoard: (id: string, data: any) => {
    return request.put(`/oa/task-boards/${id}`, data)
  },

  // 删除看板
  deleteBoard: (id: string) => {
    return request.delete(`/oa/task-boards/${id}`)
  },

  // 获取看板列
  getColumns: (boardId: string, params?: any) => {
    return request.get(`/oa/task-boards/${boardId}/columns`, { params })
  },

  // 创建列
  createColumn: (boardId: string, data: any) => {
    return request.post(`/oa/task-boards/${boardId}/columns`, data)
  },

  // 更新列
  updateColumn: (boardId: string, columnId: string, data: any) => {
    return request.put(`/oa/task-boards/${boardId}/columns/${columnId}`, data)
  },

  // 删除列
  deleteColumn: (boardId: string, columnId: string) => {
    return request.delete(`/oa/task-boards/${boardId}/columns/${columnId}`)
  },

  // 排序列
  sortColumns: (boardId: string, data: any) => {
    return request.post(`/oa/task-boards/${boardId}/columns/sort`, data)
  }
}

// 任务卡片API
export const taskCardApi = {
  // 获取任务列表
  getList: (params?: any) => {
    return request.get('/oa/tasks', { params })
  },

  // 获取任务详情
  getById: (id: string) => {
    return request.get(`/oa/tasks/${id}`)
  },

  // 创建任务
  create: (data: any) => {
    return request.post('/oa/tasks', data)
  },

  // 更新任务
  update: (id: string, data: any) => {
    return request.put(`/oa/tasks/${id}`, data)
  },

  // 删除任务
  delete: (id: string) => {
    return request.delete(`/oa/tasks/${id}`)
  },

  // 移动任务
  move: (id: string, data: any) => {
    return request.post(`/oa/tasks/${id}/move`, data)
  },

  // 复制任务
  copy: (id: string, data: any) => {
    return request.post(`/oa/tasks/${id}/copy`, data)
  },

  // 分配任务
  assign: (id: string, data: any) => {
    return request.post(`/oa/tasks/${id}/assign`, data)
  },

  // 设置截止日期
  setDueDate: (id: string, data: any) => {
    return request.post(`/oa/tasks/${id}/due-date`, data)
  },

  // 设置优先级
  setPriority: (id: string, data: any) => {
    return request.post(`/oa/tasks/${id}/priority`, data)
  },

  // 设置标签
  setTags: (id: string, data: any) => {
    return request.post(`/oa/tasks/${id}/tags`, data)
  },

  // 添加子任务
  addSubTask: (id: string, data: any) => {
    return request.post(`/oa/tasks/${id}/subtasks`, data)
  },

  // 获取子任务列表
  getSubTasks: (id: string, params?: any) => {
    return request.get(`/oa/tasks/${id}/subtasks`, { params })
  },

  // 添加评论
  addComment: (id: string, data: any) => {
    return request.post(`/oa/tasks/${id}/comments`, data)
  },

  // 获取评论列表
  getComments: (id: string, params?: any) => {
    return request.get(`/oa/tasks/${id}/comments`, { params })
  },

  // 获取任务历史
  getHistory: (id: string, params?: any) => {
    return request.get(`/oa/tasks/${id}/history`, { params })
  },

  // 获取我负责的任务
  getMyTasks: (params?: any) => {
    return request.get('/oa/tasks/my', { params })
  },

  // 获取我参与的任务
  getParticipatingTasks: (params?: any) => {
    return request.get('/oa/tasks/participating', { params })
  }
}

// 看板成员API
export const boardMemberApi = {
  // 获取成员列表
  getList: (boardId: string) => {
    return request.get(`/oa/task-boards/${boardId}/members`)
  },

  // 添加成员
  add: (boardId: string, data: any) => {
    return request.post(`/oa/task-boards/${boardId}/members`, data)
  },

  // 移除成员
  remove: (boardId: string, memberId: string) => {
    return request.delete(`/oa/task-boards/${boardId}/members/${memberId}`)
  },

  // 更新成员角色
  updateRole: (boardId: string, memberId: string, data: any) => {
    return request.put(`/oa/task-boards/${boardId}/members/${memberId}`, data)
  }
}
