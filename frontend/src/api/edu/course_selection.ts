// -*- coding: utf-8 -*-
/**
 * 选课管理 API
 * T6: 选课管理
 */
import request from '@/utils/request'

// ==================== 类型定义 ====================

/** 选课状态 */
export type SelectionStatus =
  | 'pending'
  | 'approved'
  | 'rejected'
  | 'waitlisted'
  | 'withdrawn'
  | 'dropped'
  | 'failed'
  | 'lottery_pending'

/** 选课模式 */
export type SelectionMode = 'credit' | 'course' | 'lottery'

/** 选课策略 */
export type SelectionStrategy = 'fcfs' | 'priority' | 'random' | 'weighted'

/** 规则状态 */
export type RuleStatus = 'draft' | 'active' | 'suspended' | 'expired'

/** 选课时段类型 */
export type PeriodType = 'first' | 'second' | 'add' | 'drop'

/** 选课规则 */
export interface SelectionRule {
  id: number
  name: string
  academic_year: string
  semester: number
  period_type: PeriodType
  start_time: string
  end_time: string
  selection_mode: SelectionMode
  strategy: SelectionStrategy
  status: RuleStatus
  min_credits: number
  max_credits: number
  default_credits?: number
  min_courses?: number
  max_courses?: number
  current_count?: number
  is_active?: boolean
}

/** 选课记录 */
export interface SelectionRecord {
  id: number
  student_id: number
  student_name?: string
  student_class?: string
  course_id: number
  course_name?: string
  course_code?: string
  rule_id: number
  academic_year: string
  semester: number
  status: SelectionStatus
  lottery_status?: string
  credits: number
  selected_at?: string
  confirmed_at?: string
  dropped_at?: string
  waitlist_position?: number
  reject_reason?: string
}

/** 学生选课汇总 */
export interface StudentSummary {
  student_id: number
  academic_year: string
  semester: number
  total_courses: number
  approved_courses: number
  pending_courses: number
  waitlisted_courses: number
  withdrawn_courses?: number
  dropped_courses?: number
  total_credits: number
  approved_credits: number
  pending_credits?: number
  required_count?: number
  elective_count?: number
  selection_complete: boolean
  warnings: string[]
}

/** 课程选课名单 */
export interface CourseSelectionList {
  course_id: number
  course_name?: string
  total: number
  approved: number
  pending: number
  waitlisted: number
  rejected: number
  records: SelectionRecord[]
}

/** 选课报表 */
export interface SelectionReport {
  academic_year: string
  semester: number
  total_courses: number
  total_students: number
  total_selections: number
  total_approved: number
  course_stats?: CourseStat[]
  popular_courses: PopularCourse[]
  low_demand_courses: LowDemandCourse[]
  class_stats: ClassStat[]
  waitlist_total?: number
  converted_count?: number
  generated_at: string
}

/** 课程统计 */
export interface CourseStat {
  course_id: number
  course_name?: string
  total: number
  approved: number
  pending: number
  waitlisted: number
  rejected: number
}

/** 热门课程 */
export interface PopularCourse {
  course_id: number
  course_name?: string
  total: number
  approved: number
}

/** 低需求课程 */
export interface LowDemandCourse {
  course_id: number
  course_name?: string
  total: number
  approved: number
}

/** 班级统计 */
export interface ClassStat {
  class_name: string
  total: number
  approved: number
}

/** 选课响应 */
export interface SelectionResponse {
  success: boolean
  record_id?: number
  status: string
  message: string
  waitlist_position?: number
}

/** 批量选课响应 */
export interface BatchSelectionResponse {
  success: number
  failed: number
  waitlisted: number
  details: {
    success: number[]
    failed: Array<{ course_id: number; reason: string }>
    waitlisted: Array<{ course_id: number; position: number }>
  }
}

/** 抽签结果 */
export interface LotteryResult {
  lottery_id: string
  course_id: number
  course_name?: string
  total_participants: number
  winners_count: number
  losers_count: number
  winning_rate: number
  status: string
}

/** 验证结果 */
export interface ValidationResult {
  valid: boolean
  total_credits: number
  course_count: number
  has_conflicts: boolean
  warnings: string[]
  suggestions: string[]
}

/** 候补位置 */
export interface WaitlistPosition {
  course_id: number
  student_id: number
  position: number
}

// ==================== API 请求 ====================

/**
 * 创建选课规则
 */
export function createRule(data: {
  name: string
  description?: string
  academic_year: string
  semester: number
  period_type: PeriodType
  start_time: string
  end_time: string
  selection_mode?: SelectionMode
  strategy?: SelectionStrategy
  min_credits?: number
  max_credits?: number
  default_credits?: number
  min_courses?: number
  max_courses?: number
  exclusive_groups?: string[]
  required_course_ids?: number[]
  allowed_grades?: number[]
  allowed_class_ids?: number[]
  allow_conflicts?: boolean
  allow_overcapacity?: boolean
}) {
  return request<SelectionRule>({
    url: '/course-selection/rules',
    method: 'post',
    data
  })
}

/**
 * 获取选课规则列表
 */
export function listRules(params?: {
  academic_year?: string
  semester?: number
  status?: RuleStatus
}) {
  return request<SelectionRule[]>({
    url: '/course-selection/rules',
    method: 'get',
    params
  })
}

/**
 * 获取当前生效的选课规则
 */
export function getActiveRule(academic_year: string, semester: number) {
  return request<SelectionRule>({
    url: '/course-selection/rules/active',
    method: 'get',
    params: { academic_year, semester }
  })
}

/**
 * 获取选课规则详情
 */
export function getRule(rule_id: number) {
  return request<SelectionRule>({
    url: `/course-selection/rules/${rule_id}`,
    method: 'get'
  })
}

/**
 * 更新规则状态
 */
export function updateRuleStatus(rule_id: number, status: RuleStatus) {
  return request({
    url: `/course-selection/rules/${rule_id}/status`,
    method: 'put',
    data: { status }
  })
}

// ==================== 选课操作 ====================

/**
 * 选课
 */
export function selectCourse(data: {
  student_id: number
  course_id: number
  rule_id: number
  credits: number
}) {
  return request<SelectionResponse>({
    url: '/course-selection/select',
    method: 'post',
    data
  })
}

/**
 * 撤选课程
 */
export function withdrawCourse(data: {
  record_id: number
  student_id: number
}) {
  return request({
    url: '/course-selection/withdraw',
    method: 'post',
    data
  })
}

/**
 * 退选课程
 */
export function dropCourse(data: {
  record_id: number
  student_id: number
  reason?: string
}) {
  return request({
    url: '/course-selection/drop',
    method: 'post',
    data
  })
}

/**
 * 批量选课
 */
export function batchSelect(data: {
  student_id: number
  course_ids: Array<[number, number]>  // [course_id, credits]
  rule_id: number
}) {
  return request<BatchSelectionResponse>({
    url: '/course-selection/batch-select',
    method: 'post',
    data
  })
}

// ==================== 查询功能 ====================

/**
 * 获取学生选课记录
 */
export function getStudentRecords(student_id: number, params?: {
  academic_year?: string
  semester?: number
}) {
  return request<SelectionRecord[]>({
    url: `/course-selection/student/${student_id}`,
    method: 'get',
    params
  })
}

/**
 * 获取学生选课汇总
 */
export function getStudentSummary(student_id: number, academic_year: string, semester: number) {
  return request<StudentSummary>({
    url: `/course-selection/student/${student_id}/summary`,
    method: 'get',
    params: { academic_year, semester }
  })
}

/**
 * 获取课程选课名单
 */
export function getCourseSelectionList(course_id: number, params?: {
  status?: SelectionStatus
}) {
  return request<CourseSelectionList>({
    url: `/course-selection/course/${course_id}/students`,
    method: 'get',
    params
  })
}

// ==================== 候补管理 ====================

/**
 * 获取候补位置
 */
export function getWaitlistPosition(course_id: number, student_id: number) {
  return request<WaitlistPosition>({
    url: `/course-selection/waitlist/${course_id}/position`,
    method: 'get',
    params: { student_id }
  })
}

// ==================== 抽签系统 ====================

/**
 * 执行抽签
 */
export function conductLottery(data: {
  course_id: number
  max_capacity: number
}) {
  return request<LotteryResult>({
    url: '/course-selection/lottery',
    method: 'post',
    data
  })
}

// ==================== 报表 ====================

/**
 * 获取选课报表
 */
export function getSelectionReport(academic_year: string, semester: number) {
  return request<SelectionReport>({
    url: '/course-selection/report',
    method: 'get',
    params: { academic_year, semester }
  })
}

// ==================== 验证功能 ====================

/**
 * 验证选课计划
 */
export function validateSelectionPlan(
  student_id: number,
  course_ids: number[],
  rule_id: number
) {
  return request<ValidationResult>({
    url: '/course-selection/validate',
    method: 'post',
    params: { student_id, rule_id },
    data: { course_ids }
  })
}

// ==================== 辅助函数 ====================

/**
 * 状态文本映射
 */
export const statusTextMap: Record<SelectionStatus, string> = {
  pending: '待审核',
  approved: '已通过',
  rejected: '已拒绝',
  waitlisted: '候补中',
  withdrawn: '已撤选',
  dropped: '已退选',
  failed: '选课失败',
  lottery_pending: '等待抽签'
}

/**
 * 状态颜色映射
 */
export const statusColorMap: Record<SelectionStatus, string> = {
  pending: 'warning',
  approved: 'success',
  rejected: 'danger',
  waitlisted: 'info',
  withdrawn: 'info',
  dropped: 'warning',
  failed: 'danger',
  lottery_pending: 'warning'
}

/**
 * 获取状态文本
 */
export function getStatusText(status: SelectionStatus): string {
  return statusTextMap[status] || status
}

/**
 * 获取状态颜色
 */
export function getStatusColor(status: SelectionStatus): string {
  return statusColorMap[status] || 'info'
}
