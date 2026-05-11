import request from '@/utils/request'

// 公告API
export const announcementApi = {
  // 获取公告列表
  getList: (params?: any) => {
    return request.get('/oa/announcements', { params })
  },

  // 获取公告详情
  getById: (id: string) => {
    return request.get(`/oa/announcements/${id}`)
  },

  // 创建公告
  create: (data: any) => {
    return request.post('/oa/announcements', data)
  },

  // 更新公告
  update: (id: string, data: any) => {
    return request.put(`/oa/announcements/${id}`, data)
  },

  // 删除公告
  delete: (id: string) => {
    return request.delete(`/oa/announcements/${id}`)
  },

  // 发布公告
  publish: (id: string) => {
    return request.post(`/oa/announcements/${id}/publish`)
  },

  // 撤销公告
  revoke: (id: string) => {
    return request.post(`/oa/announcements/${id}/revoke`)
  },

  // 置顶公告
  top: (id: string) => {
    return request.post(`/oa/announcements/${id}/top`)
  },

  // 取消置顶
  untop: (id: string) => {
    return request.post(`/oa/announcements/${id}/untop`)
  },

  // 获取我的公告
  getMyList: (params?: any) => {
    return request.get('/oa/announcements/my', { params })
  },

  // 标记已读
  markRead: (id: string) => {
    return request.post(`/oa/announcements/${id}/read`)
  },

  // 获取阅读记录
  getReadRecords: (id: string, params?: any) => {
    return request.get(`/oa/announcements/${id}/reads`, { params })
  },

  // 获取评论列表
  getComments: (id: string, params?: any) => {
    return request.get(`/oa/announcements/${id}/comments`, { params })
  },

  // 添加评论
  addComment: (id: string, data: any) => {
    return request.post(`/oa/announcements/${id}/comments`, data)
  }
}

// 公告分类API
export const categoryApi = {
  // 获取分类列表
  getList: (params?: any) => {
    return request.get('/oa/announcement-categories', { params })
  },

  // 获取分类详情
  getById: (id: string) => {
    return request.get(`/oa/announcement-categories/${id}`)
  },

  // 创建分类
  create: (data: any) => {
    return request.post('/oa/announcement-categories', data)
  },

  // 更新分类
  update: (id: string, data: any) => {
    return request.put(`/oa/announcement-categories/${id}`, data)
  },

  // 删除分类
  delete: (id: string) => {
    return request.delete(`/oa/announcement-categories/${id}`)
  }
}
