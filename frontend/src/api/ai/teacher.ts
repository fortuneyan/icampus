/**
 * AI 教师助手 API
 * 路径: /api/v1/ai/teacher/{lesson-plans|courseware}
 */
import request from '@/utils/request'

export interface LessonPlan {
  id: string
  course_id?: string
  course_name?: string
  grade_level?: string
  title: string
  teaching_objectives?: string
  teaching_keypoints?: string
  teaching_methods?: string
  teaching_steps?: string
  homework?: string
  ai_generated: boolean
  status?: string
  created_at?: string
}

export interface LessonPlanForm {
  course_id?: string
  course_name?: string
  grade_level?: string
  title: string
  teaching_objectives?: string
  teaching_keypoints?: string
  teaching_methods?: string
  teaching_steps?: string
  homework?: string
  ai_generated?: boolean
  source_content?: string
}

export interface LessonPlanGenerateParams {
  course_name: string
  grade_level: string
  topic: string
  duration?: number
  requirements?: string
}

/** 兼容别名 */
export type LessonPlanGenerateRequest = LessonPlanGenerateParams

/** 获取教案列表 */
export function getLessonPlans(params?: {
  keyword?: string
  grade_level?: string
  page?: number
  page_size?: number
}) {
  return request.get('/ai/teacher/lesson-plans', { params })
}

/** 获取教案列表（兼容别名） */
export const getLessonPlanList = getLessonPlans

/** 获取教案详情 */
export function getLessonPlan(planId: string) {
  return request.get(`/ai/teacher/lesson-plans/${planId}`)
}

/** 获取教案详情（兼容别名） */
export const getLessonPlanDetail = getLessonPlan

/** 创建教案 */
export function createLessonPlan(data: LessonPlanForm) {
  return request.post('/ai/teacher/lesson-plans', data)
}

/** 更新教案 */
export function updateLessonPlan(planId: string, data: Partial<LessonPlanForm>) {
  return request.put(`/ai/teacher/lesson-plans/${planId}`, data)
}

/** 删除教案 */
export function deleteLessonPlan(planId: string) {
  return request.delete(`/ai/teacher/lesson-plans/${planId}`)
}

/** AI 生成教案 */
export function generateLessonPlan(data: LessonPlanGenerateParams) {
  return request.post('/ai/teacher/lesson-plans/generate', data)
}

/** 获取课件推荐 */
export function recommendCourseware(params: {
  course_name: string
  topic?: string
  grade_level?: string
}) {
  return request.get('/ai/teacher/courseware/recommend', { params })
}

// ==================== AI 出题系统 ====================

/** 题型枚举 */
export const QUESTION_TYPES = {
  single: { label: '单选题', value: 'single' },
  multiple: { label: '多选题', value: 'multiple' },
  fill: { label: '填空题', value: 'fill' },
  essay: { label: '解答题', value: 'essay' },
  calculation: { label: '计算题', value: 'calculation' },
}

/** 题目选项 */
export interface QuestionOption {
  label: string
  content: string
  is_correct: boolean
}

/** 单个题目 */
export interface Question {
  content: string
  question_type: 'single' | 'multiple' | 'fill' | 'essay' | 'calculation'
  options?: QuestionOption[]
  answer?: string
  analysis?: string
  difficulty: number
  score: number
  knowledge_points: string[]
  source: string
  saved?: boolean
  saved_id?: string
}

/** 题目集 */
export interface QuestionSet {
  set_id: string
  title: string
  course_name: string
  grade_level: string
  topic: string
  total_count: number
  questions: Question[]
  generated_at: string
  saved_count?: number
}

/** 出题请求参数 */
export interface QuestionGenerateParams {
  course_name: string
  grade_level: string
  topic: string
  question_types: string[]
  difficulty?: number
  count?: number
  knowledge_points?: string[]
  requirements?: string
}

/** AI 出题 */
export function generateQuestions(data: QuestionGenerateParams) {
  return request.post('/ai/teacher/questions/generate', data)
}

/** 保存单题 */
export function saveQuestion(data: {
  content: string
  question_type: string
  options?: QuestionOption[]
  answer?: string
  analysis?: string
  difficulty?: number
  score?: number
  knowledge_points?: string[]
}) {
  return request.post('/ai/teacher/questions/save', data)
}

/** 批量保存题目 */
export function saveQuestionsBatch(questions: {
  content: string
  question_type: string
  options?: QuestionOption[]
  answer?: string
  analysis?: string
  difficulty?: number
  score?: number
  knowledge_points?: string[]
}[]) {
  return request.post('/ai/teacher/questions/save-batch', questions)
}
