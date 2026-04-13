import request from '@/utils/request'

export interface CacheStats {
  total_keys: number
  hit_rate: number
  memory_usage: number
  memory_usage_bytes: number
  expired_keys: number
  evicted_keys: number
  connected_clients: number
  total_commands_processed: number
  uptime_seconds: number
  timestamp: string
}

export interface CacheKeyInfo {
  key: string
  type: string
  ttl: number
  size: number
  access_count: number
  last_access: string
  created_at: string
  creator?: string
}

export interface CacheKeyDetail extends CacheKeyInfo {
  value: string
}

export interface CacheTypeStat {
  type: string
  count: number
  size: number
  size_formatted: string
}

export interface MemoryTrendPoint {
  time: string
  memory_mb: number
}

export interface MemoryTrend {
  hours: number
  data: MemoryTrendPoint[]
  current: number
  average: number
  max: number
  min: number
}

/**
 * 获取缓存统计信息
 */
export const getCacheStats = () => {
  return request.get('/system/cache/stats')
}

/**
 * 获取缓存键列表
 */
export const getCacheKeys = (params?: {
  keyword?: string
  key_type?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  page?: number
  page_size?: number
}) => {
  return request.get('/system/cache/keys', { params })
}

/**
 * 获取缓存键详情
 */
export const getCacheKey = (key: string) => {
  // 对key进行编码以处理特殊字符
  const encodedKey = encodeURIComponent(key)
  return request.get(`/system/cache/keys/${encodedKey}`)
}

/**
 * 删除缓存键
 */
export const deleteCacheKey = (key: string) => {
  const encodedKey = encodeURIComponent(key)
  return request.delete(`/system/cache/keys/${encodedKey}`)
}

/**
 * 更新缓存键TTL
 */
export const updateCacheTTL = (key: string, ttl: number) => {
  const encodedKey = encodeURIComponent(key)
  return request.post(`/system/cache/keys/${encodedKey}/ttl?ttl=${ttl}`)
}

/**
 * 清理过期缓存键
 */
export const clearExpiredKeys = () => {
  return request.post('/system/cache/clear-expired')
}

/**
 * 清空所有缓存
 */
export const clearAllCache = (confirm: boolean = false) => {
  return request.post(`/system/cache/clear-all?confirm=${confirm}`)
}

/**
 * 获取缓存类型分布
 */
export const getCacheTypes = () => {
  return request.get('/system/cache/types')
}

/**
 * 获取内存使用趋势
 */
export const getMemoryTrend = (hours: number = 24) => {
  return request.get('/system/cache/memory-trend', { params: { hours } })
}

/**
 * 刷新缓存数据库
 */
export const flushCacheDB = () => {
  return request.post('/system/cache/flushdb')
}
