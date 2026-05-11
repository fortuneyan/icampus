import request from '@/utils/request'

// 工作日志API
export const worklogApi = {
  // 获取日志列表
  getList: (params?: any) => {
    return request.get('/oa/worklogs', { params })
  },

  // 获取日志详情
  getById: (id: string) => {
    return request.get(`/oa/worklogs/${id}`)
  },

  // 创建日志
  create: (data: any) => {
    return request.post('/oa/worklogs', data)
  },

  // 更新日志
  update: (id: string, data: any) => {
    return request.put(`/oa/worklogs/${id}`, data)
  },

  // 删除日志
  delete: (id: string) => {
    return request.delete(`/oa/worklogs/${id}`)
  },

  // 获取我的日志
  getMyList: (params?: any) => {
    return request.get('/oa/worklogs/my', { params })
  },

  // 获取下属日志
  getSubordinateList: (params?: any) => {
    return request.get('/oa/worklogs/subordinates', { params })
  },

  // 评论日志
  comment: (id: string, data: any) => {
    return request.post(`/oa/worklogs/${id}/comment`, data)
  },

  // 点赞日志
  like: (id: string) => {
    return request.post(`/oa/worklogs/${id}/like`)
  },

  // 取消点赞
  unlike: (id: string) => {
    return request.post(`/oa/worklogs/${id}/unlike`)
  },

  // 获取统计数据
  getStatistics: (params?: any) => {
    return request.get('/oa/worklogs/statistics', { params })
  },

  // 日志周报
  getWeeklyReport: (params: any) => {
    return request.get('/oa/worklogs/weekly-report', { params })
  },

  // 日志月报
  getMonthlyReport: (params: any) => {
    return request.get('/oa/worklogs/monthly-report', { params })
  },

  // 提交审核
  submit: (id: string) => {
    return request.post(`/oa/worklogs/${id}/submit`)
  },

  // 获取团队日志（主任视图）
  getTeamLogs: (params?: any) => {
    return request.get('/oa/worklogs/team', { params })
  },

  // 审核日志
  review: (id: string, data: any) => {
    return request.post(`/oa/worklogs/${id}/review`, data)
  },

  // 获取日志统计（按用户）
  getStats: (params?: any) => {
    return request.get('/oa/worklogs/stats', { params })
  }
}

// 日志分类API
export const worklogCategoryApi = {
  // 获取分类列表
  getList: (params?: any) => {
    return request.get('/oa/worklog-categories', { params })
  },

  // 创建分类
  create: (data: any) => {
    return request.post('/oa/worklog-categories', data)
  },

  // 更新分类
  update: (id: string, data: any) => {
    return request.put(`/oa/worklog-categories/${id}`, data)
  },

  // 删除分类
  delete: (id: string) => {
    return request.delete(`/oa/worklog-categories/${id}`)
  }
}

// 日志评论API
export const worklogCommentApi = {
  // 获取评论列表
  getList: (worklogId: string, params?: any) => {
    return request.get(`/oa/worklogs/${worklogId}/comments`, { params })
  },

  // 删除评论
  delete: (worklogId: string, commentId: string) => {
    return request.delete(`/oa/worklogs/${worklogId}/comments/${commentId}`)
  }
}
