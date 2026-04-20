import request from '@/utils/request'

export interface NotificationForm {
  title: string
  content: string
  notification_type?: string
  scope_type?: string
  scope_ids?: string[]
  is_urgent?: boolean
}

export function getNotificationList(params?: { page?: number; page_size?: number }) {
  return request.get('/notification', { params })
}

export function getNotificationAdminList(params?: { page?: number; page_size?: number; status?: string }) {
  return request.get('/notification/admin', { params })
}

export function getNotificationDetail(id: string) {
  return request.get(`/notification/${id}`)
}

export function createNotification(data: NotificationForm) {
  return request.post('/notification', data)
}

export function updateNotification(id: string, data: NotificationForm) {
  return request.put(`/notification/${id}`, data)
}

export function deleteNotification(id: string) {
  return request.delete(`/notification/${id}`)
}

export function sendNotification(id: string) {
  return request.post(`/notification/${id}/send`)
}

export function markAsRead(id: string) {
  return request.post(`/notification/${id}/read`)
}

export function getReadStatus(id: string) {
  return request.get(`/notification/${id}/reads`)
}