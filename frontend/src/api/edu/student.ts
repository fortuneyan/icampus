import request from '@/utils/request'

export interface StudentParams {
  keyword?: string
  grade_id?: string
  class_id?: string
  status?: string
  page?: number
  page_size?: number
}

export interface StudentForm {
  student_no: string
  name: string
  gender?: string
  birth_date?: string
  id_card?: string
  nation?: string
  phone?: string
  guardian_name?: string
  guardian_phone?: string
  grade_id?: string
  class_id?: string
}

export function getStudentList(params: StudentParams) {
  return request.get('/edu/students', { params })
}

export function getStudentOptions(grade_id?: string, class_id?: string) {
  return request.get('/edu/students/options', { params: { grade_id, class_id } })
}

export function getStudentDetail(id: string) {
  return request.get(`/edu/students/${id}`)
}

export function createStudent(data: StudentForm) {
  return request.post('/edu/students', data)
}

export function updateStudent(id: string, data: StudentForm) {
  return request.put(`/edu/students/${id}`, data)
}

export function deleteStudent(id: string) {
  return request.delete(`/edu/students/${id}`)
}

export function assignClass(studentId: string, classId: string) {
  return request.put(`/edu/students/${studentId}/class`, { class_id: classId })
}