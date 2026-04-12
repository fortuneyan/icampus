/**
 * AI 学习记录追踪 API
 * 路径: /api/v1/ai/learning-records
 */
import request from '@/utils/request'

export interface LearningRecordForm {
  resource_type?: string
  resource_id?: string
  resource_name?: string
  action_type: string
  duration?: number
  progress?: number
  score?: number
}

export interface LearningRecord extends LearningRecordForm {
  id: string
  created_at?: string
}

/** 获取学习记录列表 */
export function getLearningRecords(params?: {
  resource_type?: string
  action_type?: string
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}) {
  return request.get('/ai/learning-records', { params })
}

/** 创建学习记录 */
export function createLearningRecord(data: LearningRecordForm) {
  return request.post('/ai/learning-records', data)
}

/** 获取学习统计 */
export function getLearningStatistics(days?: number) {
  return request.get('/ai/learning-records/statistics', { params: { days } })
}

/** 获取每日学习数据 */
export function getDailyLearning(days?: number) {
  return request.get('/ai/learning-records/daily', { params: { days } })
}
