import request from '@/utils/request'

export interface ClassForm {
  name: string
  grade_id?: string
  class_no: number
  teacher_id?: string
  room_id?: string
}

export function getClassList(params?: { grade_id?: string; status?: string; page?: number; page_size?: number }) {
  return request.get('/edu/classes', { params })
}

export function getClassTree(grade_id?: string) {
  return request.get('/edu/classes/tree', { params: { grade_id } })
}

export function getClassOptions(grade_id?: string) {
  return request.get('/edu/classes/options', { params: { grade_id } })
}

export function getClassDetail(id: string) {
  return request.get(`/edu/classes/${id}`)
}

export function createClass(data: ClassForm) {
  return request.post('/edu/classes', data)
}

export function updateClass(id: string, data: ClassForm) {
  return request.put(`/edu/classes/${id}`, data)
}

export function deleteClass(id: string) {
  return request.delete(`/edu/classes/${id}`)
}