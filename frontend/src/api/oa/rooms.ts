import request from '@/utils/request'

// 教室预约API
export const roomApi = {
  // 获取教室列表
  getList: (params?: any) => {
    return request.get('/oa/rooms', { params })
  },

  // 获取教室详情
  getById: (id: string) => {
    return request.get(`/oa/rooms/${id}`)
  },

  // 创建教室
  create: (data: any) => {
    return request.post('/oa/rooms', data)
  },

  // 更新教室
  update: (id: string, data: any) => {
    return request.put(`/oa/rooms/${id}`, data)
  },

  // 删除教室
  delete: (id: string) => {
    return request.delete(`/oa/rooms/${id}`)
  },

  // 获取可用时间槽
  getAvailableSlots: (roomId: string, params: any) => {
    return request.get(`/oa/rooms/${roomId}/slots`, { params })
  },

  // 检查冲突
  checkConflict: (data: any) => {
    return request.post('/oa/rooms/check-conflict', data)
  }
}

// 预约记录API
export const bookingApi = {
  // 获取预约列表
  getList: (params?: any) => {
    return request.get('/oa/room-bookings', { params })
  },

  // 获取预约详情
  getById: (id: string) => {
    return request.get(`/oa/room-bookings/${id}`)
  },

  // 创建预约
  create: (data: any) => {
    return request.post('/oa/room-bookings', data)
  },

  // 取消预约
  cancel: (id: string) => {
    return request.post(`/oa/room-bookings/${id}/cancel`)
  },

  // 获取我的预约
  getMyList: (params?: any) => {
    return request.get('/oa/room-bookings/my', { params })
  },

  // 获取教室预约记录
  getByRoom: (roomId: string, params?: any) => {
    return request.get(`/oa/rooms/${roomId}/bookings`, { params })
  }
}
