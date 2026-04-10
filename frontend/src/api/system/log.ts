import request from '@/utils/request'

export function getOperationLogs(params?: any) {
  return request.get('/system/logs/operation', { params })
}

export function getLoginLogs(params?: any) {
  return request.get('/system/logs/login', { params })
}

export function getDataAccessLogs(params?: any) {
  return request.get('/system/logs/access', { params })
}