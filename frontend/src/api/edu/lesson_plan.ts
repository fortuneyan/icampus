import request from '@/utils/request'

export function getLessonPlanList(params?: any) {
  return request.get('/edu/lesson-plans', { params })
}

export function getLessonPlan(id: string) {
  return request.get(`/edu/lesson-plans/${id}`)
}

export function createLessonPlan(data: any) {
  return request.post('/edu/lesson-plans', data)
}

export function updateLessonPlan(id: string, data: any) {
  return request.put(`/edu/lesson-plans/${id}`, data)
}

export function deleteLessonPlan(id: string) {
  return request.delete(`/edu/lesson-plans/${id}`)
}

export function submitLessonPlan(id: string) {
  return request.post(`/edu/lesson-plans/${id}/submit`)
}