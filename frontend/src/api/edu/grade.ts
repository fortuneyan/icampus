import request from '@/utils/request'

export interface GradeForm {
  grade_level?: number
  name: string
  code: string
  academic_year: string
  head_teacher_id?: string
  status?: string
  description?: string
}

export function getGradeList(params?: { name?: string; page?: number; page_size?: number }) {
  return request.get('/edu/grades', { params })
}

export function getGradeOptions() {
  return request.get('/edu/grades/options')
}

export function getTeacherOptions() {
  return request.get('/system/users/options?role=teacher')
}

export function getGradeDetail(id: string) {
  return request.get(`/edu/grades/${id}`)
}

export function createGrade(data: GradeForm) {
  const payload: any = { ...data }
  if (!payload.head_teacher_id) delete payload.head_teacher_id
  if (!payload.description) delete payload.description
  if (payload.grade_level === '') delete payload.grade_level
  return request.post('/edu/grades', payload)
}

export function updateGrade(id: string, data: GradeForm) {
  const payload: any = { ...data }
  if (!payload.head_teacher_id) delete payload.head_teacher_id
  if (!payload.description) delete payload.description
  if (payload.grade_level === '') delete payload.grade_level
  return request.put(`/edu/grades/${id}`, payload)
}

export function deleteGrade(id: string) {
  return request.delete(`/edu/grades/${id}`)
}