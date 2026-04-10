import request from '@/utils/request'

export function getTeacherProfileList(params?: any) {
  return request.get('/system/teacher-profiles', { params })
}

export function getTeacherProfile(userId: string) {
  return request.get(`/system/teacher-profiles/${userId}`)
}

export function createTeacherProfile(data: any) {
  return request.post('/system/teacher-profiles', data)
}

export function updateTeacherProfile(userId: string, data: any) {
  return request.put(`/system/teacher-profiles/${userId}`, data)
}

export function deleteTeacherProfile(userId: string) {
  return request.delete(`/system/teacher-profiles/${userId}`)
}