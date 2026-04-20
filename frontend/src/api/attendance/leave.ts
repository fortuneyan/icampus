import request from '@/utils/request'

export interface LeaveForm {
  student_id: string
  leave_type: string
  start_date: string
  end_date: string
  reason?: string
}

export function getLeaveRequests(params?: { student_id?: string; status?: string; page?: number; page_size?: number }) {
  return request.get('/attendance/leaves', { params })
}

export function createLeaveRequest(data: LeaveForm) {
  return request.post('/attendance/leaves', data)
}

export function getLeaveDetail(id: string) {
  return request.get(`/attendance/leaves/${id}`)
}

export function approveLeave(id: string, data: { status: string; approver_comment?: string }) {
  return request.put(`/attendance/leaves/${id}/approve`, data)
}

export function getLeaveStats() {
  return request.get('/attendance/leaves/stats/summary')
}

export function getLeaveQuota(params?: { student_id?: string; class_id?: string; year?: number }) {
  return request.get('/attendance/leaves/quota', { params })
}

export function createLeaveQuota(data: any) {
  return request.post('/attendance/leaves/quota', data)
}