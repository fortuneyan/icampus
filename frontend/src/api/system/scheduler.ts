import request from '@/utils/request'

export interface SchedulerTask {
  id: string
  name: string
  task_type: string
  cron: string
  description?: string
  enabled: boolean
  status: string
  last_run?: string
  last_result?: string
  next_run?: string
  run_count: number
  created_at: string
  updated_at: string
  params?: Record<string, any>
}

export interface TaskLog {
  id: string
  task_id: string
  task_name: string
  start_time: string
  end_time?: string
  duration?: string
  status: string
  message?: string
}

export interface TaskType {
  value: string
  label: string
  color: string
}

export interface SchedulerStats {
  total_tasks: number
  enabled_tasks: number
  running_tasks: number
  today_executions: number
}

/**
 * 获取定时任务列表
 */
export const getSchedulerTasks = (params?: {
  keyword?: string
  task_type?: string
  status?: string
  page?: number
  page_size?: number
}) => {
  return request.get('/system/scheduler/tasks', { params })
}

/**
 * 获取定时任务详情
 */
export const getSchedulerTask = (taskId: string) => {
  return request.get(`/system/scheduler/tasks/${taskId}`)
}

/**
 * 创建定时任务
 */
export const createSchedulerTask = (data: {
  name: string
  task_type: string
  cron: string
  description?: string
  params?: Record<string, any>
}) => {
  return request.post('/system/scheduler/tasks', data)
}

/**
 * 更新定时任务
 */
export const updateSchedulerTask = (
  taskId: string,
  data: Partial<{
    name: string
    task_type: string
    cron: string
    description: string
    params: Record<string, any>
    enabled: boolean
  }>
) => {
  return request.put(`/system/scheduler/tasks/${taskId}`, data)
}

/**
 * 删除定时任务
 */
export const deleteSchedulerTask = (taskId: string) => {
  return request.delete(`/system/scheduler/tasks/${taskId}`)
}

/**
 * 启用/禁用定时任务
 */
export const toggleSchedulerTask = (taskId: string) => {
  return request.post(`/system/scheduler/tasks/${taskId}/toggle`)
}

/**
 * 立即执行定时任务
 */
export const runSchedulerTaskNow = (taskId: string) => {
  return request.post(`/system/scheduler/tasks/${taskId}/run`)
}

/**
 * 获取任务执行日志
 */
export const getSchedulerLogs = (params?: {
  task_id?: string
  status?: string
  page?: number
  page_size?: number
}) => {
  return request.get('/system/scheduler/logs', { params })
}

/**
 * 获取任务类型列表
 */
export const getTaskTypes = () => {
  return request.get('/system/scheduler/types')
}
