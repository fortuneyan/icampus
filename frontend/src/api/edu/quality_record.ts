import request from '@/utils/request'

export function getQualityRecordList(params?: any) {
  return request.get('/edu/quality-records', { params })
}

export function getQualityRecord(id: string) {
  return request.get(`/edu/quality-records/${id}`)
}

export function createQualityRecord(data: any) {
  return request.post('/edu/quality-records', data)
}

export function updateQualityRecord(id: string, data: any) {
  return request.put(`/edu/quality-records/${id}`, data)
}

export function deleteQualityRecord(id: string) {
  return request.delete(`/edu/quality-records/${id}`)
}

export function submitQualityRecord(id: string) {
  return request.post(`/edu/quality-records/${id}/submit`)
}

export function confirmQualityRecord(id: string, data: any) {
  return request.post(`/edu/quality-records/${id}/confirm`, data)
}