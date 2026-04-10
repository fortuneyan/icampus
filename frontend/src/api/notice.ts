import request from '@/utils/request'

export interface NoticeForm {
  title: string
  notice_type?: string
  priority?: string
  content: string
}

export function getNoticeList(params?: { keyword?: string; notice_type?: string; page?: number; page_size?: number }) {
  return request.get('/notice/notices', { params })
}

export function getNoticeDetail(id: string) {
  return request.get(`/notice/notices/${id}`)
}

export function createNotice(data: NoticeForm) {
  return request.post('/notice/notices', data)
}

export function updateNotice(id: string, data: NoticeForm) {
  return request.put(`/notice/notices/${id}`, data)
}

export function deleteNotice(id: string) {
  return request.delete(`/notice/notices/${id}`)
}

export function markRead(id: string) {
  return request.put(`/notice/notices/${id}/read`)
}

export function getUnreadCount() {
  return request.get('/notice/unread-count')
}