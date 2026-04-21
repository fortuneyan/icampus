import request from '@/utils/request'

export interface RecruitmentPlanForm {
  name: string
  year: number
  grade_id?: string
  quota?: number
  tuition?: number
  start_date: string
  end_date: string
  description?: string
  requirements?: string
}

export interface ApplicantForm {
  student_name: string
  gender?: string
  birth_date?: string
  phone: string
  guardian_name?: string
  guardian_phone?: string
  id_card?: string
  address?: string
  current_school?: string
  source?: string
  recruitment_plan_id?: string
  application_year?: number
}

export interface FollowUpForm {
  follow_type: string
  content: string
  next_follow_date?: string
}

export interface ApplicantBatchUpdate {
  ids: string[]
  status?: string
  enrollment_batch?: string
  recruitment_plan_id?: string
}

export function getRecruitmentPlans(params?: { year?: number; status?: string; page?: number; page_size?: number }) {
  return request.get('/recruitment/plans', { params })
}

export function createRecruitmentPlan(data: RecruitmentPlanForm) {
  return request.post('/recruitment/plans', data)
}

export function updateRecruitmentPlan(id: string, data: Partial<RecruitmentPlanForm>) {
  return request.put(`/recruitment/plans/${id}`, data)
}

export function getPublicPlan(planId: string) {
  return request.get(`/recruitment/plans/${planId}/public`)
}

export function getApplicants(params?: { status?: string; recruitment_plan_id?: string; page?: number; page_size?: number }) {
  return request.get('/recruitment/applicants', { params })
}

export function createApplicant(data: ApplicantForm) {
  return request.post('/recruitment/applicants', data)
}

export function updateApplicantStatus(id: string, status: string) {
  return request.put(`/recruitment/applicants/${id}/status`, null, { params: { status } })
}

export function batchUpdateApplicants(data: ApplicantBatchUpdate) {
  return request.put('/recruitment/applicants/batch', data)
}

export function importApplicants(file: File, recruitmentPlanId?: string) {
  const formData = new FormData()
  formData.append('file', file)
  if (recruitmentPlanId) {
    formData.append('recruitment_plan_id', recruitmentPlanId)
  }
  return request.post('/recruitment/applicants/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function downloadTemplate() {
  return request.get('/recruitment/applicants/template', {
    responseType: 'blob'
  })
}

export function addFollowUp(applicantId: string, data: FollowUpForm) {
  return request.post(`/recruitment/applicants/${applicantId}/follow-up`, data)
}

export function getFollowUps(applicantId: string) {
  return request.get(`/recruitment/applicants/${applicantId}/follow-ups`)
}

export function getRecruitmentStats() {
  return request.get('/recruitment/stats')
}

export function publicApply(data: ApplicantForm) {
  return request.post('/recruitment/apply/public', data)
}

export function checkApplicationStatus(phone: string) {
  return request.get('/recruitment/apply/status', { params: { phone } })
}