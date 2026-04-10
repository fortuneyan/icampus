import request from '@/utils/request'

export function getStudentProfileList(params?: any) {
  return request.get('/edu/student-profiles', { params })
}

export function getStudentProfile(userId: string) {
  return request.get(`/edu/student-profiles/${userId}`)
}

export function createStudentProfile(data: any) {
  return request.post('/edu/student-profiles', data)
}

export function updateStudentProfile(userId: string, data: any) {
  return request.put(`/edu/student-profiles/${userId}`, data)
}

export function deleteStudentProfile(userId: string) {
  return request.delete(`/edu/student-profiles/${userId}`)
}