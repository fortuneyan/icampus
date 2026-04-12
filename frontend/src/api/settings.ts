import request from '@/utils/request'

export interface SystemConfig {
  setting_key: string
  setting_value: string
  value_type: string
  description?: string
}

export interface SystemInfo {
  app_version: string
  python_version: string
  database_type: string
  os_type: string
  server_time: string
}

export function getConfig(key?: string) {
  return request.get('/settings/config', { params: { key } })
}

export function updateConfig(data: { setting_key: string; setting_value: string; value_type: string }) {
  return request.put('/settings/config', data)
}

export function getSystemInfo() {
  return request.get('/settings/system-info')
}

export function getLogs(params?: {
  start_date?: string
  end_date?: string
  level?: string
  page?: number
  page_size?: number
}) {
  return request.get('/settings/logs', { params })
}
