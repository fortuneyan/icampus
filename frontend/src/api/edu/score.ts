import request from '@/utils/request'

export interface ScoreForm {
  student_id: string
  course_id: string
  semester: string
  score_type: string
  score?: number
  grade_letter?: string
}

export function getScoreList(params?: { student_id?: string; course_id?: string; semester?: string; page?: number; page_size?: number }) {
  return request.get('/edu/scores', { params })
}

export function getScoreStatistics(course_id: string, semester?: string) {
  return request.get('/edu/scores/statistics', { params: { course_id, semester } })
}

export function getScoreDetail(id: string) {
  return request.get(`/edu/scores/${id}`)
}

export function createScore(data: ScoreForm) {
  return request.post('/edu/scores', data)
}

export function updateScore(id: string, data: ScoreForm) {
  return request.put(`/edu/scores/${id}`, data)
}

export function deleteScore(id: string) {
  return request.delete(`/edu/scores/${id}`)
}