import request from '@/utils/request'

// 资产API
export const assetApi = {
  // 获取资产列表
  getList: (params?: any) => {
    return request.get('/oa/assets', { params })
  },

  // 获取资产详情
  getById: (id: string) => {
    return request.get(`/oa/assets/${id}`)
  },

  // 创建资产
  create: (data: any) => {
    return request.post('/oa/assets', data)
  },

  // 更新资产
  update: (id: string, data: any) => {
    return request.put(`/oa/assets/${id}`, data)
  },

  // 删除资产
  delete: (id: string) => {
    return request.delete(`/oa/assets/${id}`)
  },

  // 领用资产
  claim: (id: string, data: any) => {
    return request.post(`/oa/assets/${id}/claim`, data)
  },

  // 归还资产
  return: (id: string) => {
    return request.post(`/oa/assets/${id}/return`)
  },

  // 调拨资产
  transfer: (id: string, data: any) => {
    return request.post(`/oa/assets/${id}/transfer`, data)
  },

  // 报修资产
  repair: (id: string, data: any) => {
    return request.post(`/oa/assets/${id}/repair`, data)
  },

  // 报废资产
  scrap: (id: string, data: any) => {
    return request.post(`/oa/assets/${id}/scrap`, data)
  },

  // 获取资产操作历史
  getHistory: (id: string, params?: any) => {
    return request.get(`/oa/assets/${id}/history`, { params })
  },

  // 批量导入
  import: (data: any) => {
    return request.post('/oa/assets/import', data)
  },

  // 导出资产
  export: (params?: any) => {
    return request.get('/oa/assets/export', { params })
  }
}

// 资产分类API
export const assetCategoryApi = {
  // 获取分类列表
  getList: (params?: any) => {
    return request.get('/oa/asset-categories', { params })
  },

  // 获取分类详情
  getById: (id: string) => {
    return request.get(`/oa/asset-categories/${id}`)
  },

  // 创建分类
  create: (data: any) => {
    return request.post('/oa/asset-categories', data)
  },

  // 更新分类
  update: (id: string, data: any) => {
    return request.put(`/oa/asset-categories/${id}`, data)
  },

  // 删除分类
  delete: (id: string) => {
    return request.delete(`/oa/asset-categories/${id}`)
  }
}

// 资产操作记录API
export const assetOperationApi = {
  // 获取操作记录列表
  getList: (params?: any) => {
    return request.get('/oa/asset-operations', { params })
  },

  // 获取记录详情
  getById: (id: string) => {
    return request.get(`/oa/asset-operations/${id}`)
  }
}
