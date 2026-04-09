import request from '@/utils/request'

export interface DepartmentForm {
  name: string
  code?: string
  parent_id?: string
  sort_order?: number
  leader_id?: string
  phone?: string
  email?: string
  status?: string
  description?: string
}

export function getDepartmentTree(parentId?: string) {
  return request.get('/system/departments', { params: { parent_id: parentId } })
}

export function getAllDepartments() {
  return request.get('/system/departments/all')
}

export function getDepartmentDetail(id: string) {
  return request.get(`/system/departments/${id}`)
}

export function createDepartment(data: DepartmentForm) {
  return request.post('/system/departments', data)
}

export function updateDepartment(id: string, data: DepartmentForm) {
  return request.put(`/system/departments/${id}`, data)
}

export function deleteDepartment(id: string) {
  return request.delete(`/system/departments/${id}`)
}