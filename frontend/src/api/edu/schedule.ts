import request from '@/utils/request'

export interface ScheduleForm {
  course_id: string
  class_id: string
  teacher_id: string
  room_id?: string
  weekday: number
  period_start: number
  period_end: number
  semester: string
  week_range?: string
}

export function getScheduleList(params?: { class_id?: string; teacher_id?: string; course_id?: string; weekday?: number; week?: number; semester?: string; page?: number; page_size?: number }) {
  return request.get('/edu/schedules', { params })
}

export function getClassSchedule(classId: string, semester?: string) {
  return request.get(`/edu/schedules/class/${classId}`, { params: { semester } })
}

export function getTeacherSchedule(teacherId: string, semester?: string) {
  return request.get(`/edu/schedules/teacher/${teacherId}`, { params: { semester } })
}

export function getScheduleDetail(id: string) {
  return request.get(`/edu/schedules/${id}`)
}

export function createSchedule(data: ScheduleForm) {
  return request.post('/edu/schedules', data)
}

export function updateSchedule(id: string, data: ScheduleForm) {
  return request.put(`/edu/schedules/${id}`, data)
}

export function deleteSchedule(id: string) {
  return request.delete(`/edu/schedules/${id}`)
}