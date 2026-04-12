/**
 * 教材管理 API
 */
import request from '@/utils/request'

export interface Textbook {
  id?: string
  isbn: string
  title: string
  subtitle?: string
  author?: string
  publisher?: string
  subject?: string
  grade_level?: string
  grade_level_text?: string
  semester?: string
  edition?: string
  price?: number
  cost_price?: number
  stock_quantity?: number
  min_stock?: number
  reorder_point?: number
  description?: string
  cover_image?: string
  page_count?: number
  status?: string
  status_text?: string
  course_id?: number
  created_at?: string
  updated_at?: string
}

export interface TextbookAdoption {
  id?: string
  textbook_id: number
  grade_level: string
  semester: string
  school_year: string
  adoption_year?: number
  adoption_reason?: string
  approved_by?: string
  approved_at?: string
  is_mandatory?: boolean
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

/**
 * 获取教材列表
 */
export function getTextbookList(params: {
  page?: number
  page_size?: number
  keyword?: string
  subject?: string
  grade_level?: string
  status?: string
}) {
  return request.get<any, PageResult<Textbook>>('/edu/textbooks', { params })
}

/**
 * 获取教材详情
 */
export function getTextbook(id: number) {
  return request.get<any, { data: Textbook }>(`/edu/textbooks/${id}`)
}

/**
 * 创建教材
 */
export function createTextbook(data: Partial<Textbook>) {
  return request.post<any, { data: Textbook }>('/edu/textbooks', data)
}

/**
 * 更新教材
 */
export function updateTextbook(id: number, data: Partial<Textbook>) {
  return request.put<any, { data: Textbook }>(`/edu/textbooks/${id}`, data)
}

/**
 * 删除教材
 */
export function deleteTextbook(id: number) {
  return request.delete<any, { data: null }>(`/edu/textbooks/${id}`)
}

/**
 * 更新库存
 */
export function updateStock(id: number, quantity: number, operation: 'add' | 'subtract' | 'set') {
  return request.post<any, { data: Textbook }>(`/edu/textbooks/${id}/stock`, null, {
    params: { quantity, operation }
  })
}

/**
 * 获取教材选用列表
 */
export function getAdoptionList(params: {
  grade_level?: string
  semester?: string
  school_year?: string
}) {
  return request.get<any, { data: TextbookAdoption[] }>('/edu/adoptions', { params })
}

/**
 * 创建教材选用
 */
export function createAdoption(data: Partial<TextbookAdoption>) {
  return request.post<any, { data: TextbookAdoption }>('/edu/adoptions', data)
}

/**
 * 审批教材选用
 */
export function approveAdoption(id: number, approved_by: string) {
  return request.put<any, { data: TextbookAdoption }>(`/edu/adoptions/${id}/approve`, null, {
    params: { approved_by }
  })
}

/**
 * 获取学科统计
 */
export function getSubjectStatistics() {
  return request.get<any, { data: Record<string, any> }>('/edu/textbooks/statistics/subjects')
}

/**
 * 获取低库存教材
 */
export function getLowStockTextbooks() {
  return request.get<any, { data: Textbook[] }>('/edu/textbooks/statistics/low-stock')
}

// 学科列表
export const SUBJECTS = [
  { value: 'chinese', label: '语文' },
  { value: 'math', label: '数学' },
  { value: 'english', label: '英语' },
  { value: 'physics', label: '物理' },
  { value: 'chemistry', label: '化学' },
  { value: 'biology', label: '生物' },
  { value: 'politics', label: '道德与法治' },
  { value: 'history', label: '历史' },
  { value: 'geography', label: '地理' },
  { value: 'music', label: '音乐' },
  { value: 'art', label: '美术' },
  { value: 'pe', label: '体育与健康' },
  { value: 'information', label: '信息技术' }
]

// 年级列表
export const GRADE_LEVELS = [
  { value: 'grade_1', label: '一年级' },
  { value: 'grade_2', label: '二年级' },
  { value: 'grade_3', label: '三年级' },
  { value: 'grade_4', label: '四年级' },
  { value: 'grade_5', label: '五年级' },
  { value: 'grade_6', label: '六年级' },
  { value: 'grade_7', label: '七年级（初一）' },
  { value: 'grade_8', label: '八年级（初二）' },
  { value: 'grade_9', label: '九年级（初三）' },
  { value: 'high_1', label: '高一' },
  { value: 'high_2', label: '高二' },
  { value: 'high_3', label: '高三' }
]

// 学期列表
export const SEMESTERS = [
  { value: 'first', label: '第一学期' },
  { value: 'second', label: '第二学期' }
]

// 状态列表
export const STATUS_LIST = [
  { value: 'draft', label: '草稿' },
  { value: 'published', label: '已发布' },
  { value: 'out_of_stock', label: '缺货' },
  { value: 'discontinued', label: '停用' }
]
