import request from '@/utils/request'

export interface ResourceForm {
  title: string
  resource_type: string
  category_id?: string
  description?: string
  file_url?: string
}

export function getResourceList(params?: { keyword?: string; resource_type?: string; category_id?: string; page?: number; page_size?: number }) {
  return request.get('/resource/resources', { params })
}

export function getResourceDetail(id: string) {
  return request.get(`/resource/resources/${id}`)
}

export function createResource(data: ResourceForm) {
  return request.post('/resource/resources', data)
}

export function updateResource(id: string, data: ResourceForm) {
  return request.put(`/resource/resources/${id}`, data)
}

export function deleteResource(id: string) {
  return request.delete(`/resource/resources/${id}`)
}

export function auditResource(id: string, data: { status: string }) {
  return request.put(`/resource/resources/${id}/audit`, data)
}

export function getCategoryOptions() {
  return request.get('/resource/categories/options')
}

export function getRecommendResources(params?: { user_id?: string; limit?: number }) {
  return request.get('/resource/recommend', { params })
}