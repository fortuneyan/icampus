/**
 * 毕业管理API
 */
import request from '@/utils/request'

// ==================== 类型定义 ====================

export interface GraduationAudit {
  id: number
  student_id: number
  academic_year: string
  semester: number
  audit_type: 'preliminary' | 'formal' | 'appeal'
  status: 'pending' | 'in_progress' | 'approved' | 'rejected' | 'graduated' | 'deferred'
  total_credits: number
  major_credits: number
  elective_credits: number
  practice_credits: number
  completed_courses: number
  gpa: number
  is_eligible: boolean
  completion_rate: number
  audit_comment?: string
  auditor_id?: number
  audit_time?: string
}

export interface GraduationCertificate {
  id: number
  student_id: number
  student_name: string
  certificate_number: string
  academic_year: string
  graduation_year: number
  graduation_month: number
  major: string
  major_code: string
  degree_type: string
  status: 'pending' | 'printed' | 'issued' | 'archived' | 'revoked'
  gpa: number
  completion_rate: number
  is_valid: boolean
}

export interface LeaveSchoolCheckpoint {
  type: string
  name: string
  status: 'pending' | 'in_progress' | 'completed' | 'exempted'
  required: boolean
  result: string
  remarks?: string
  checked_at?: string
  checked_by?: number
}

export interface LeaveSchoolRecord {
  id: number
  student_id: number
  student_name: string
  leave_type: string
  status: 'pending' | 'in_progress' | 'completed' | 'exempted'
  academic_year: string
  semester: number
  completion_rate: number
  graduation_date?: string
  checkpoints: LeaveSchoolCheckpoint[]
}

export interface AlumniRecord {
  id: number
  student_id: number
  name: string
  gender?: string
  phone?: string
  email?: string
  wechat?: string
  id_card?: string
  admission_year: number
  graduation_year: number
  major: string
  degree?: string
  student_class?: string
  employer?: string
  position?: string
  industry?: string
  employment_status: string
  alumni_association: boolean
  alumni_level: 'normal' | 'silver' | 'gold' | 'platinum'
  contributions: number
  created_at: string
  updated_at: string
}

export interface GraduationReport {
  audit_id: number
  student_id: number
  student_name: string
  total_credits: number
  major_credits: number
  elective_credits: number
  practice_credits: number
  gpa: number
  is_eligible: boolean
  completion_rate: number
  missing_requirements: string[]
  suggestions: string[]
  generated_at: string
}

export interface GraduationStatistics {
  academic_year: string
  semester: number
  total_students: number
  graduated_count: number
  pending_count: number
  deferred_count: number
  average_gpa: number
  highest_gpa: number
  lowest_gpa: number
  graduation_rate: number
}

export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

// ==================== 毕业审核API ====================

/**
 * 创建毕业审核记录
 */
export function createAudit(data: {
  student_id: number
  academic_year: string
  semester?: number
  audit_type?: string
}) {
  return request<ApiResponse<GraduationAudit>>({
    url: '/student/graduation/audits',
    method: 'post',
    data
  })
}

/**
 * 更新学业信息
 */
export function updateAcademicInfo(
  auditId: number,
  data: {
    total_credits: number
    major_credits: number
    elective_credits: number
    practice_credits: number
    completed_courses: number
    gpa: number
    passed_required?: number[]
    failed_required?: number[]
  }
) {
  return request<ApiResponse<GraduationAudit>>({
    url: `/student/graduation/audits/${auditId}/academic`,
    method: 'put',
    data
  })
}

/**
 * 检查毕业资格
 */
export function checkEligibility(auditId: number) {
  return request<ApiResponse<{
    is_eligible: boolean
    reasons: string[]
    completion_rate: number
  }>>({
    url: `/student/graduation/audits/${auditId}/eligibility`,
    method: 'post'
  })
}

/**
 * 提交审核
 */
export function submitAudit(
  auditId: number,
  auditorId: number,
  comment?: string
) {
  return request<ApiResponse<GraduationAudit>>({
    url: `/student/graduation/audits/${auditId}/submit`,
    method: 'post',
    data: { comment },
    params: { auditor_id: auditorId }
  })
}

/**
 * 批量审核
 */
export function batchAudit(data: {
  audit_ids: number[]
  approved: boolean
  comment?: string
}, auditorId: number) {
  return request<ApiResponse<{
    total: number
    approved: number
    rejected: number
    failed: number
    details: any[]
  }>>({
    url: '/student/graduation/audits/batch',
    method: 'post',
    data,
    params: { auditor_id: auditorId }
  })
}

/**
 * 获取审核列表
 */
export function getAuditList(params: {
  student_id?: number
  academic_year?: string
  status?: string
  page?: number
  page_size?: number
}) {
  return request<ApiResponse<{
    total: number
    page: number
    page_size: number
    items: GraduationAudit[]
  }>>({
    url: '/student/graduation/audits',
    method: 'get',
    params
  })
}

/**
 * 获取审核详情
 */
export function getAuditDetail(auditId: number) {
  return request<ApiResponse<GraduationAudit>>({
    url: `/student/graduation/audits/${auditId}`,
    method: 'get'
  })
}

// ==================== 毕业证书API ====================

/**
 * 创建毕业证书
 */
export function createCertificate(data: {
  student_id: number
  student_name: string
  academic_year: string
  major?: string
  major_code?: string
}) {
  return request<ApiResponse<GraduationCertificate>>({
    url: '/student/graduation/certificates',
    method: 'post',
    data
  })
}

/**
 * 打印证书
 */
export function printCertificate(certificateId: number, printedBy: number) {
  return request<ApiResponse<GraduationCertificate>>({
    url: `/student/graduation/certificates/${certificateId}/print`,
    method: 'post',
    data: { printed_by: printedBy }
  })
}

/**
 * 发放证书
 */
export function issueCertificate(certificateId: number, issuedBy: number) {
  return request<ApiResponse<GraduationCertificate>>({
    url: `/student/graduation/certificates/${certificateId}/issue`,
    method: 'post',
    data: { issued_by: issuedBy }
  })
}

/**
 * 吊销证书
 */
export function revokeCertificate(certificateId: number, reason?: string) {
  return request<ApiResponse<GraduationCertificate>>({
    url: `/student/graduation/certificates/${certificateId}/revoke`,
    method: 'post',
    data: { reason }
  })
}

/**
 * 验证证书
 */
export function verifyCertificate(certificateNumber: string) {
  return request<ApiResponse<{
    is_valid: boolean
    result: string
  }>>({
    url: `/student/graduation/certificates/verify/${certificateNumber}`,
    method: 'get'
  })
}

/**
 * 获取证书详情
 */
export function getCertificate(certificateId: number) {
  return request<ApiResponse<GraduationCertificate>>({
    url: `/student/graduation/certificates/${certificateId}`,
    method: 'get'
  })
}

/**
 * 获取学生证书
 */
export function getStudentCertificate(studentId: number) {
  return request<ApiResponse<GraduationCertificate | null>>({
    url: `/student/graduation/certificates/student/${studentId}`,
    method: 'get'
  })
}

// ==================== 离校手续API ====================

/**
 * 创建离校记录
 */
export function createLeaveRecord(data: {
  student_id: number
  student_name: string
  academic_year: string
  semester?: number
  leave_type?: string
}) {
  return request<ApiResponse<LeaveSchoolRecord>>({
    url: '/student/graduation/leave-records',
    method: 'post',
    data
  })
}

/**
 * 完成检查点
 */
export function completeCheckpoint(
  leaveId: number,
  checkpointType: string,
  checkedBy: number,
  result?: string
) {
  return request<ApiResponse<LeaveSchoolRecord>>({
    url: `/student/graduation/leave-records/${leaveId}/checkpoints/${checkpointType}/complete`,
    method: 'post',
    data: { checkpoint_type: checkpointType, checked_by: checkedBy, result }
  })
}

/**
 * 豁免检查点
 */
export function exemptCheckpoint(
  leaveId: number,
  checkpointType: string,
  reason: string,
  exemptedBy: number
) {
  return request<ApiResponse<LeaveSchoolRecord>>({
    url: `/student/graduation/leave-records/${leaveId}/checkpoints/${checkpointType}/exempt`,
    method: 'post',
    data: { checkpoint_type: checkpointType, reason, exempted_by: exemptedBy }
  })
}

/**
 * 获取离校记录详情
 */
export function getLeaveRecord(leaveId: number) {
  return request<ApiResponse<LeaveSchoolRecord>>({
    url: `/student/graduation/leave-records/${leaveId}`,
    method: 'get'
  })
}

/**
 * 获取待办理离校记录
 */
export function getPendingLeaveRecords() {
  return request<ApiResponse<LeaveSchoolRecord[]>>({
    url: '/student/graduation/leave-records/pending',
    method: 'get'
  })
}

// ==================== 校友管理API ====================

/**
 * 创建校友记录
 */
export function createAlumni(data: {
  student_id: number
  name: string
  admission_year: number
  graduation_year: number
  major?: string
  degree?: string
}) {
  return request<ApiResponse<AlumniRecord>>({
    url: '/student/graduation/alumni',
    method: 'post',
    data
  })
}

/**
 * 毕业生转校友
 */
export function convertToAlumni(data: {
  student_id: number
  name: string
  admission_year: number
  graduation_year: number
  major?: string
  student_class?: string
}) {
  return request<ApiResponse<AlumniRecord>>({
    url: '/student/graduation/alumni/convert',
    method: 'post',
    data
  })
}

/**
 * 更新校友信息
 */
export function updateAlumni(
  alumniId: number,
  data: {
    employer?: string
    position?: string
    industry?: string
    phone?: string
    email?: string
  }
) {
  return request<ApiResponse<AlumniRecord>>({
    url: `/student/graduation/alumni/${alumniId}`,
    method: 'put',
    data
  })
}

/**
 * 获取校友详情
 */
export function getAlumni(alumniId: number) {
  return request<ApiResponse<AlumniRecord>>({
    url: `/student/graduation/alumni/${alumniId}`,
    method: 'get'
  })
}

/**
 * 搜索校友
 */
export function searchAlumni(params: {
  major?: string
  graduation_year?: number
  industry?: string
  employer?: string
  page?: number
  page_size?: number
}) {
  return request<ApiResponse<{
    total: number
    page: number
    page_size: number
    items: AlumniRecord[]
  }>>({
    url: '/student/graduation/alumni/search',
    method: 'get',
    params
  })
}

/**
 * 获取校友统计
 */
export function getAlumniStatistics(graduationYear?: number) {
  return request<ApiResponse<{
    total: number
    by_industry: Record<string, number>
    by_level: Record<string, number>
    employment_rate: number
    alumni_association_rate: number
  }>>({
    url: '/student/graduation/alumni/statistics',
    method: 'get',
    params: { graduation_year: graduationYear }
  })
}

// ==================== 统计报表API ====================

/**
 * 生成毕业报告
 */
export function generateGraduationReport(auditId: number) {
  return request<ApiResponse<GraduationReport>>({
    url: `/student/graduation/reports/${auditId}`,
    method: 'get'
  })
}

/**
 * 获取毕业统计
 */
export function getGraduationStatistics(academicYear: string) {
  return request<ApiResponse<GraduationStatistics>>({
    url: `/student/graduation/statistics/${academicYear}`,
    method: 'get'
  })
}

// ==================== 枚举映射 ====================

export const GraduationStatusMap = {
  pending: { text: '待审核', color: 'warning' },
  in_progress: { text: '审核中', color: 'processing' },
  approved: { text: '已通过', color: 'success' },
  rejected: { text: '已拒绝', color: 'error' },
  graduated: { text: '已毕业', color: 'success' },
  deferred: { text: '延期毕业', color: 'default' }
}

export const CertificateStatusMap = {
  pending: { text: '待制作', color: 'warning' },
  printed: { text: '已打印', color: 'processing' },
  issued: { text: '已发放', color: 'success' },
  archived: { text: '已归档', color: 'default' },
  revoked: { text: '已吊销', color: 'error' }
}

export const LeaveStatusMap = {
  pending: { text: '待办理', color: 'warning' },
  in_progress: { text: '办理中', color: 'processing' },
  completed: { text: '已完成', color: 'success' },
  exempted: { text: '已豁免', color: 'default' }
}

export const AlumniLevelMap = {
  normal: { text: '普通校友', color: 'default' },
  silver: { text: '银牌校友', color: 'default' },
  gold: { text: '金牌校友', color: 'gold' },
  platinum: { text: '铂金校友', color: 'purple' }
}
