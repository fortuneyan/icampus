import request from '@/utils/request'

export interface CourseForm {
  code: string
  name: string
  category?: string
  credit?: number
  hours?: number
  teacher_id?: string
  grade_id?: string
  semester?: string
  exam_type?: string
}

export function getCourseList(params?: { grade_id?: string; status?: string; page?: number; page_size?: number }) {
  return request.get('/edu/courses', { params })
}

export function getCourseOptions(grade_id?: string) {
  return request.get('/edu/courses/options', { params: { grade_id } })
}

export function getCourseDetail(id: string) {
  return request.get(`/edu/courses/${id}`)
}

export function createCourse(data: CourseForm) {
  return request.post('/edu/courses', data)
}

export function updateCourse(id: string, data: CourseForm) {
  return request.put(`/edu/courses/${id}`, data)
}

export function deleteCourse(id: string) {
  return request.delete(`/edu/courses/${id}`)
}