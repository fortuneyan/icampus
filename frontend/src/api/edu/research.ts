import request from '@/utils/request'

export function getResearchProjectList(params?: any) {
  return request.get('/edu/research-projects', { params })
}

export function getResearchProject(id: string) {
  return request.get(`/edu/research-projects/${id}`)
}

export function createResearchProject(data: any) {
  return request.post('/edu/research-projects', data)
}

export function updateResearchProject(id: string, data: any) {
  return request.put(`/edu/research-projects/${id}`, data)
}

export function deleteResearchProject(id: string) {
  return request.delete(`/edu/research-projects/${id}`)
}

export function submitResearchProject(id: string) {
  return request.post(`/edu/research-projects/${id}/submit`)
}

export function approveResearchProject(id: string, data: any) {
  return request.post(`/edu/research-projects/${id}/approve`, data)
}

export function completeResearchProject(id: string) {
  return request.post(`/edu/research-projects/${id}/complete`)
}