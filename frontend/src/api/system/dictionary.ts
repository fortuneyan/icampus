import request from '@/utils/request'

// ==================== 字典类型 ====================

export interface DictTypeForm {
  name: string
  code: string
  description?: string
  status?: string
}

export interface DictTypeItem {
  id: string
  name: string
  code: string
  description?: string
  status: string
  created_at?: string
}

export function getDictTypeList(params?: {
  keyword?: string
  status?: string
  page?: number
  page_size?: number
}) {
  return request.get('/system/dict-types', { params })
}

export function getDictTypeDetail(id: string) {
  return request.get(`/system/dict-types/${id}`)
}

export function createDictType(data: DictTypeForm) {
  return request.post('/system/dict-types', data)
}

export function updateDictType(id: string, data: DictTypeForm) {
  return request.put(`/system/dict-types/${id}`, data)
}

export function deleteDictType(id: string) {
  return request.delete(`/system/dict-types/${id}`)
}

// ==================== 字典项 ====================

export interface DictItemForm {
  type_id: string
  label: string
  value: string
  sort_order?: number
  status?: string
  remark?: string
}

export interface DictItem {
  id: string
  type_id: string
  label: string
  value: string
  sort_order: number
  status: string
  remark?: string
}

export function getDictItems(params?: {
  type_id?: string
  type_code?: string
  status?: string
}) {
  return request.get('/system/dict-items', { params })
}

export function getDictItemsByCode(typeCode: string, status: string = 'active') {
  return request.get(`/system/dict-items/by-code/${typeCode}`, { params: { status } })
}

export function createDictItem(data: DictItemForm) {
  return request.post('/system/dict-items', data)
}

export function updateDictItem(id: string, data: DictItemForm) {
  return request.put(`/system/dict-items/${id}`, data)
}

export function deleteDictItem(id: string) {
  return request.delete(`/system/dict-items/${id}`)
}
