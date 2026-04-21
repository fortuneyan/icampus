import request from '@/utils/request'

export interface HomeworkForm {
  title: string
  content?: string
  course_id?: string
  grade_id?: string
  class_id?: string
  homework_type?: string
  total_score?: number
  submit_start?: string
  submit_end?: string
  notify_enabled?: boolean
}

export interface SubmissionForm {
  content?: string
  attachment_urls?: string[]
}

export interface WrongQuestionForm {
  question_content: string
  question_type?: string
  correct_answer?: string
  student_answer?: string
  score?: number
  source_type?: string
  source_id?: string
}

export interface FeedbackForm {
  feedback_type: string
  content: string
}

export function getHomeworks(params?: { course_id?: string; class_id?: string; status?: string; page?: number; page_size?: number }) {
  return request.get('/homework/homeworks', { params })
}

export function createHomework(data: HomeworkForm) {
  return request.post('/homework/homeworks', data)
}

export function updateHomework(id: string, data: Partial<HomeworkForm>) {
  return request.put(`/homework/homeworks/${id}`, data)
}

export function getSubmissions(homeworkId: string) {
  return request.get(`/homework/homeworks/${homeworkId}/submissions`)
}

export function submitHomework(homeworkId: string, data: SubmissionForm) {
  return request.post(`/homework/homeworks/${homeworkId}/submit`, data)
}

export function gradeSubmission(submissionId: string, score: number, feedback?: string) {
  return request.put(`/homework/submissions/${submissionId}/grade`, null, { params: { score, feedback } })
}

export function getWrongQuestions(params?: { student_id?: string; is_mastered?: boolean; page?: number; page_size?: number }) {
  return request.get('/homework/wrong-questions', { params })
}

export function createWrongQuestion(data: WrongQuestionForm) {
  return request.post('/homework/wrong-questions', data)
}

export function getFeedbacks(homeworkId: string) {
  return request.get(`/homework/homeworks/${homeworkId}/feedbacks`)
}

export function createFeedback(homeworkId: string, data: FeedbackForm) {
  return request.post(`/homework/homeworks/${homeworkId}/feedback`, data)
}

export function getHomeworkStats() {
  return request.get('/homework/homeworks/stats')
}