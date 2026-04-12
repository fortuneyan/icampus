/**
 * 教学进度跟踪 API
 */
import request from '@/utils/request'

export interface TeachingProgress {
  id?: string
  course_id: number
  teacher_id?: number
  class_id?: number
  chapter?: string
  chapter_number?: number
  unit_name?: string
  unit_number?: number
  planned_start_date?: string
  planned_end_date?: string
  actual_start_date?: string
  actual_end_date?: string
  status?: string
  status_text?: string
  progress_percentage?: number
  planned_hours?: number
  actual_hours?: number
  key_points?: string
  difficult_points?: string
  teaching_goals?: string
  notes?: string
  delay_reason?: string
  created_at?: string
  updated_at?: string
}

export interface ProgressUpdate {
  id?: string
  progress_id: number
  update_type: string
  old_value?: string
  new_value?: string
  updated_by?: string
  update_reason?: string
  created_at?: string
}

export interface ProgressReport {
  id?: string
  title: string
  report_type: string
  teacher_id: number
  school_year: string
  semester: string
  period_start: string
  period_end: string
  total_courses?: number
  completed_courses?: number
  in_progress_courses?: number
  delayed_courses?: number
  avg_progress?: number
  planned_vs_actual?: string
  issues?: string
  solutions?: string
  next_plan?: string
  status?: string
  reviewed_by?: string
  reviewed_at?: string
  review_comments?: string
  created_at?: string
}

export interface TeacherStatistics {
  total: number
  completed: number
  in_progress: number
  delayed: number
  avg_progress: number
  completion_rate: number
}

export interface CourseStatistics {
  total_chapters: number
  avg_progress: number
  status_distribution: {
    not_started: number
    in_progress: number
    completed: number
    delayed: number
  }
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// ============== 教学进度API ==============

/**
 * 获取教学进度列表
 */
export function getTeachingProgressList(params: {
  page?: number
  page_size?: number
  course_id?: number
  teacher_id?: number
  class_id?: number
  status?: string
  keyword?: string
}) {
  return request.get<any, PageResult<TeachingProgress>>('/edu/teaching-progress', { params })
}

/**
 * 获取教学进度详情
 */
export function getTeachingProgress(id: number) {
  return request.get<any, { data: TeachingProgress }>(`/edu/teaching-progress/${id}`)
}

/**
 * 创建教学进度
 */
export function createTeachingProgress(data: Partial<TeachingProgress>) {
  return request.post<any, { data: TeachingProgress }>('/edu/teaching-progress', data)
}

/**
 * 更新教学进度
 */
export function updateTeachingProgress(id: number, data: Partial<TeachingProgress>) {
  return request.put<any, { data: TeachingProgress }>(`/edu/teaching-progress/${id}`, data)
}

/**
 * 删除教学进度
 */
export function deleteTeachingProgress(id: number) {
  return request.delete<any, { data: null }>(`/edu/teaching-progress/${id}`)
}

/**
 * 更新完成百分比
 */
export function updateProgressPercentage(id: number, percentage: number) {
  return request.patch<any, { data: TeachingProgress }>(
    `/edu/teaching-progress/${id}/percentage`,
    null,
    { params: { percentage } }
  )
}

// ============== 进度更新记录API ==============

/**
 * 获取进度更新记录
 */
export function getProgressUpdates(progressId: number) {
  return request.get<any, { data: ProgressUpdate[] }>(`/edu/progress-updates/${progressId}`)
}

// ============== 进度报告API ==============

/**
 * 获取进度报告列表
 */
export function getProgressReportList(params: {
  teacher_id?: number
  report_type?: string
  school_year?: string
  semester?: string
}) {
  return request.get<any, { data: ProgressReport[] }>('/edu/progress-reports', { params })
}

/**
 * 获取进度报告详情
 */
export function getProgressReport(id: number) {
  return request.get<any, { data: ProgressReport }>(`/edu/progress-reports/${id}`)
}

/**
 * 创建进度报告
 */
export function createProgressReport(data: Partial<ProgressReport>) {
  return request.post<any, { data: ProgressReport }>('/edu/progress-reports', data)
}

/**
 * 提交进度报告
 */
export function submitProgressReport(id: number) {
  return request.post<any, { data: ProgressReport }>(`/edu/progress-reports/${id}/submit`)
}

/**
 * 审批进度报告
 */
export function approveProgressReport(id: number, reviewed_by: string, comments?: string) {
  return request.post<any, { data: ProgressReport }>(
    `/edu/progress-reports/${id}/approve`,
    null,
    { params: { reviewed_by, comments } }
  )
}

// ============== 统计分析API ==============

/**
 * 获取教师教学统计
 */
export function getTeacherStatistics(teacherId: number) {
  return request.get<any, { data: TeacherStatistics }>(`/edu/teaching-progress/statistics/teacher/${teacherId}`)
}

/**
 * 获取课程教学统计
 */
export function getCourseStatistics(courseId: number) {
  return request.get<any, { data: CourseStatistics }>(`/edu/teaching-progress/statistics/course/${courseId}`)
}

// ============== 辅助数据 ==============

// 状态选项
export const STATUS_OPTIONS = [
  { value: 'not_started', label: '未开始' },
  { value: 'in_progress', label: '进行中' },
  { value: 'completed', label: '已完成' },
  { value: 'delayed', label: '已延误' },
  { value: 'ahead', label: '提前完成' }
]

// 报告类型
export const REPORT_TYPES = [
  { value: 'weekly', label: '周报' },
  { value: 'monthly', label: '月报' },
  { value: 'termly', label: '学期报告' }
]

// 获取状态标签
export function getStatusLabel(status: string) {
  return STATUS_OPTIONS.find(s => s.value === status)?.label || status
}

// 获取状态类型
export function getStatusType(status: string) {
  switch (status) {
    case 'completed':
      return 'success'
    case 'in_progress':
      return 'primary'
    case 'delayed':
      return 'danger'
    case 'ahead':
      return 'warning'
    default:
      return 'info'
  }
}
