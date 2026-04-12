import request from '@/utils/request'

export interface DashboardStats {
  student_count: number
  teacher_count: number
  class_count: number
  course_count: number
}

export function getDashboardStats() {
  return request.get<any, { data: DashboardStats }>('/dashboard/overview')
}

export function getDashboardStatistics() {
  return request.get<any, any>('/dashboard/statistics')
}

export function getDashboardCharts() {
  return request.get<any, any>('/dashboard/charts')
}

export function getQuickActions() {
  return request.get<any, any>('/dashboard/quick-actions')
}