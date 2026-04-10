import request from '@/utils/request'

export interface ExamForm {
  title: string
  exam_type: string
  academic_year?: string
  semester?: string
  duration?: number
  total_score?: number
  status?: string
}

export function getExamList(params?: { keyword?: string; exam_type?: string; page?: number; page_size?: number }) {
  return request.get('/exam/papers', { params })
}

export function getExamDetail(id: string) {
  return request.get(`/exam/papers/${id}`)
}

export function createExam(data: ExamForm) {
  return request.post('/exam/papers', data)
}

export function updateExam(id: string, data: ExamForm) {
  return request.put(`/exam/papers/${id}`, data)
}

export function deleteExam(id: string) {
  return request.delete(`/exam/papers/${id}`)
}