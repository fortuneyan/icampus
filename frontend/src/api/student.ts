import request from '@/utils/request'

// ==================== 成长记录 ====================

export interface GrowthRecordForm {
  student_id: string
  record_type: string
  title: string
  content?: string
  attachment_url?: string
  attachment_urls?: string
  tags?: string
  record_date?: string
  academic_year?: string
  semester?: string
  is_public?: boolean
  is_featured?: boolean
  status?: string
}

export interface GrowthRecord {
  id: string
  student_id: string
  record_type: string
  title: string
  content?: string
  attachment_url?: string
  tags?: string
  academic_year?: string
  semester?: string
  is_public: boolean
  is_featured: boolean
  status: string
  record_date?: string
  created_at?: string
}

export function getGrowthRecordList(params?: {
  student_id?: string
  record_type?: string
  academic_year?: string
  semester?: string
  is_public?: boolean
  page?: number
  page_size?: number
}) {
  return request.get('/student/growth-records', { params })
}

export function getGrowthRecordDetail(id: string) {
  return request.get(`/student/growth-records/${id}`)
}

export function createGrowthRecord(data: GrowthRecordForm) {
  return request.post('/student/growth-records', data)
}

export function updateGrowthRecord(id: string, data: Partial<GrowthRecordForm>) {
  return request.put(`/student/growth-records/${id}`, data)
}

export function deleteGrowthRecord(id: string) {
  return request.delete(`/student/growth-records/${id}`)
}

export function getStudentGrowthTimeline(studentId: string, academicYear?: string) {
  return request.get(`/student/growth-records/student/${studentId}/timeline`, {
    params: { academic_year: academicYear }
  })
}
