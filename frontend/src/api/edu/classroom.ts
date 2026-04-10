import request from '@/utils/request'

export interface ClassroomForm {
  building: string
  room_no: string
  capacity?: number
  room_type?: string
  status?: string
}

export function getClassroomList(params?: { building?: string; room_type?: string; status?: string; page?: number; page_size?: number }) {
  return request.get('/edu/classrooms', { params })
}

export function getClassroomOptions(status?: string) {
  return request.get('/edu/classrooms/options', { params: { status } })
}

export function getBuildings() {
  return request.get('/edu/classrooms/buildings')
}

export function getClassroomDetail(id: string) {
  return request.get(`/edu/classrooms/${id}`)
}

export function createClassroom(data: ClassroomForm) {
  return request.post('/edu/classrooms', data)
}

export function updateClassroom(id: string, data: ClassroomForm) {
  return request.put(`/edu/classrooms/${id}`, data)
}

export function deleteClassroom(id: string) {
  return request.delete(`/edu/classrooms/${id}`)
}