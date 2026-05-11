import request from '@/utils/request'

export interface RoleForm {
  code: string
  name: string
  description?: string
  level?: number
  data_scope?: string
  status?: string
}

export function getRoleList(params?: { keyword?: string; status?: string; page?: number; page_size?: number }) {
  return request.get('/system/roles', { params })
}

export function getRoleDetail(id: string) {
  return request.get(`/system/roles/${id}`)
}

export function createRole(data: RoleForm) {
  return request.post('/system/roles', data)
}

export function updateRole(id: string, data: RoleForm) {
  return request.put(`/system/roles/${id}`, data)
}

export function deleteRole(id: string) {
  return request.delete(`/system/roles`)
}

// 角色下拉选项（用于工作流审批人选择）
export function getRoleOptions() {
  return request.get('/system/roles/options')
}

// 部门下拉选项（用于工作流部门选择）
export function getDepartmentOptions() {
  return request.get('/system/departments/options')
}

export function getPermissionTree(parentId?: string) {
  return request.get('/system/permissions', { params: { parent_id: parentId } })
}

export function getMenuTree(parentId?: string) {
  return request.get('/system/menus', { params: { parent_id: parentId } })
}

export function getUserMenus() {
  return request.get('/system/menus/user')
}

export function createMenu(data: any) {
  return request.post('/system/menus', data)
}

export function updateMenu(id: string, data: any) {
  return request.put(`/system/menus/${id}`, data)
}

export function deleteMenu(id: string) {
  return request.delete(`/system/menus/${id}`)
}