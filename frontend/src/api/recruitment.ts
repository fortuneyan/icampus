import request from '@/utils/request'

export interface RecruitmentPlanForm {
  name: string
  year: number
  grade_id?: string
  quota?: number
  start_date: string
  end_date: string
  description?: string
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
  source?: string
  recruitment_plan_id?: string
}

export interface FollowUpForm {
  follow_type: string
  content: string
  next_follow_date?: string
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

export function getApplicants(params?: { status?: string; recruitment_plan_id?: string; page?: number; page_size?: number }) {
  return request.get('/recruitment/applicants', { params })
}

export function createApplicant(data: ApplicantForm) {
  return request.post('/recruitment/applicants', data)
}

export function updateApplicantStatus(id: string, status: string) {
  return request.put(`/recruitment/applicants/${id}/status`, null, { params: { status } })
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