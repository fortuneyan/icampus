import request from '@/utils/request'

export interface AttendanceForm {
  rule_id: string
  photo?: string
  location?: string
}

export interface LeaveForm {
  leave_type: string
  start_date: string
  end_date: string
  reason: string
}

export function getAttendanceList(params?: { date?: string; attendance_type?: string; page?: number; page_size?: number }) {
  return request.get('/attendance/records', { params })
}

export function checkIn(data: AttendanceForm) {
  return request.post('/attendance/check-in', data)
}

export function getAttendanceStats(params?: { start_date?: string; end_date?: string }) {
  return request.get('/attendance/statistics', { params })
}

export function createLeave(data: LeaveForm) {
  return request.post('/attendance/leave', data)
}

export function getLeaveList(params?: { status?: string; page?: number; page_size?: number }) {
  return request.get('/attendance/leave', { params })
}

export function approveLeave(id: string, data: { status: string; comment?: string }) {
  return request.put(`/attendance/leave/${id}/approve`, data)
}