import request from '@/utils/request'

export function getTeachingPlanList(params?: any) {
  return request.get('/edu/teaching-plans', { params })
}

export function getTeachingPlan(id: string) {
  return request.get(`/edu/teaching-plans/${id}`)
}

export function createTeachingPlan(data: any) {
  return request.post('/edu/teaching-plans', data)
}

export function updateTeachingPlan(id: string, data: any) {
  return request.put(`/edu/teaching-plans/${id}`, data)
}

export function deleteTeachingPlan(id: string) {
  return request.delete(`/edu/teaching-plans/${id}`)
}

export function submitTeachingPlan(id: string) {
  return request.post(`/edu/teaching-plans/${id}/submit`)
}

export function approveTeachingPlan(id: string, data: any) {
  return request.post(`/edu/teaching-plans/${id}/approve`, data)
}