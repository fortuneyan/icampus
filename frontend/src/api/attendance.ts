import request from '@/utils/request'

export interface AttendanceForm {
  attendance_type?: string
  check_in_time?: string
  check_out_time?: string
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

export function createAttendance(data: AttendanceForm) {
  return request.post('/attendance/records', data)
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