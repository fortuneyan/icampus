import request from '@/utils/request'

export interface UserParams {
  keyword?: string
  status?: string
  department_id?: string
  page?: number
  page_size?: number
}

export interface RoleSimple {
  id: string
  code: string
  name: string
}

export interface UserForm {
  username: string
  email?: string
  phone?: string
  password?: string
  real_name?: string
  department_id?: string
  position?: string
  gender?: string
  status?: string
  role_ids?: string[]
}

export function getUserList(params: UserParams) {
  return request.get('/system/users', { params })
}

export function getUserOptions() {
  return request.get('/system/users/options')
}

export function getUserDetail(id: string) {
  return request.get(`/system/users/${id}`)
}

export function createUser(data: UserForm) {
  return request.post('/system/users', data)
}

export function updateUser(id: string, data: UserForm) {
  return request.put(`/system/users/${id}`, data)
}

export function deleteUser(id: string) {
  return request.delete(`/system/users/${id}`)
}

export function resetPassword(id: string, password: string) {
  return request.put(`/system/users/${id}/reset-password`, { password })
}

export function updateUserStatus(id: string, status: string) {
  return request.put(`/system/users/${id}/status`, { status })
}

export function changePassword(old_password: string, new_password: string) {
  return request.put('/system/users/change-password', { old_password, new_password })
}

export function getUserRoles(id: string) {
  return request.get(`/system/users/${id}/roles`)
}

export function assignUserRoles(id: string, roleIds: string[]) {
  return request.put(`/system/users/${id}/roles`, { role_ids: roleIds })
}
