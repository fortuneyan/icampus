import request from '@/utils/request'

export interface CPUInfo {
  percent: number
  count: number
  frequency?: number
}

export interface MemoryInfo {
  total_gb: number
  used_gb: number
  available_gb: number
  percent: number
}

export interface DiskInfo {
  total_gb: number
  used_gb: number
  free_gb: number
  percent: number
}

export interface SystemInfo {
  cpu: CPUInfo
  memory: MemoryInfo
  disk: DiskInfo
  platform: string
  platform_version: string
  uptime_seconds: number
  timestamp: string
}

export interface DatabasePoolInfo {
  pool_size: number
  checked_out: number
  overflow: number
  checked_in: number
  status: string
}

export interface DatabaseInfo {
  pool: DatabasePoolInfo
  database: string
  status: string
}

export interface HealthCheck {
  status: string
  value?: string
  pool_size?: number
  checked_out?: number
}

export interface HealthStatus {
  overall: string
  checks: {
    cpu: HealthCheck
    memory: HealthCheck
    disk: HealthCheck
    database: HealthCheck
  }
  timestamp: string
}

export interface ProcessInfo {
  pid: number
  memory_mb: number
  cpu_percent: number
  num_threads: number
  create_time: string
  status: string
}

/**
 * 获取系统资源信息
 */
export const getSystemInfo = () => {
  return request.get('/system/monitor/system')
}

/**
 * 获取数据库连接池信息
 */
export const getDatabaseInfo = () => {
  return request.get('/system/monitor/database')
}

/**
 * 获取整体健康状态
 */
export const getHealthStatus = () => {
  return request.get('/system/monitor/health')
}

/**
 * 获取当前进程信息
 */
export const getProcessInfo = () => {
  return request.get('/system/monitor/process')
}
