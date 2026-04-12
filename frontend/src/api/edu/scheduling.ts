// -*- coding: utf-8 -*-
/**
 * T5: 智能排课
 * 前端API调用模块
 */

import request from '@/utils/request';

// ============== Type Definitions ==============

export interface TimeSlot {
  day_of_week: number;
  period: number;
  start_time?: string;
  end_time?: string;
}

export interface CourseAssignment {
  id: number;
  course_id: number;
  course_name: string;
  teacher_id: number;
  teacher_name: string;
  class_id: number;
  class_name: string;
  classroom_id?: number;
  classroom_name?: string;
  time_slot?: TimeSlot;
  duration: number;
  status: 'pending' | 'assigned' | 'conflict' | 'optimized' | 'manual_adjusted';
  assignment_score?: number;
  is_locked: boolean;
  note?: string;
}

export interface SchedulingPlan {
  id: number;
  name: string;
  academic_year: string;
  semester: string;
  start_date: string;
  end_date: string;
  status: 'draft' | 'optimizing' | 'optimized' | 'reviewing' | 'published' | 'archived';
  score: number;
  optimization_iterations: number;
  assignments: CourseAssignment[];
  conflicts?: Conflict[];
  created_at?: string;
  updated_at?: string;
}

export interface Conflict {
  type: 'teacher_conflict' | 'class_conflict' | 'classroom_conflict' | 'availability_conflict';
  severity: number;
  description: string;
  involved: number[];
  suggestion?: string;
}

export interface ScheduleTable {
  plan_id: number;
  plan_name: string;
  days: number;
  periods: number;
  grid: Record<number, Record<number, CourseAssignment[]>>;
}

export interface ScheduleSummary {
  plan: {
    id: number;
    name: string;
    status: string;
    score: number;
  };
  total_assignments: number;
  assigned_count: number;
  unassigned_count: number;
  by_class: Record<string, {
    total: number;
    assigned: number;
    unassigned: number;
  }>;
  by_teacher: Record<string, {
    total: number;
    hours: number;
  }>;
}

export interface ClassInfo {
  id: number;
  name: string;
  grade: number;
  student_count: number;
}

export interface CourseInfo {
  id: number;
  name: string;
  subject: string;
  required_hours: number;
}

export interface TeacherInfo {
  id: number;
  name: string;
  subject: string;
  max_hours: number;
}

export interface ClassroomInfo {
  id: number;
  name: string;
  type: string;
  capacity: number;
  equipment: string[];
}

export interface OptimizationResult {
  plan_id: number;
  status: string;
  score: number;
  iterations: number;
  conflicts_resolved: number;
}

export interface ConflictCheckResult {
  total_conflicts: number;
  conflicts: Conflict[];
  can_publish: boolean;
}

export interface Pagination {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
}

// ============== API Functions ==============

/**
 * 获取排课计划列表
 */
export function getPlans(params: {
  academic_year?: string;
  semester?: string;
  status?: string;
  page?: number;
  page_size?: number;
}) {
  return request<ApiResponse<{
    plans: SchedulingPlan[];
    pagination: Pagination;
  }>>({
    url: '/scheduling/plans',
    method: 'get',
    params,
  });
}

/**
 * 获取排课计划详情
 */
export function getPlan(planId: number) {
  return request<ApiResponse<SchedulingPlan>>({
    url: `/scheduling/plans/${planId}`,
    method: 'get',
  });
}

/**
 * 创建排课计划
 */
export function createPlan(data: {
  name: string;
  academic_year: string;
  semester: string;
  start_date: string;
  end_date: string;
  assignments?: CourseAssignment[];
}) {
  return request<ApiResponse<SchedulingPlan>>({
    url: '/scheduling/plans',
    method: 'post',
    data,
  });
}

/**
 * 优化排课计划
 */
export function optimizePlan(planId: number, params?: {
  max_iterations?: number;
  time_limit?: number;
}) {
  return request<ApiResponse<OptimizationResult>>({
    url: `/scheduling/plans/${planId}/optimize`,
    method: 'post',
    params,
  });
}

/**
 * 检测排课冲突
 */
export function detectConflicts(planId: number) {
  return request<ApiResponse<ConflictCheckResult>>({
    url: `/scheduling/plans/${planId}/conflicts`,
    method: 'get',
  });
}

/**
 * 手动调整课程分配
 */
export function adjustAssignment(planId: number, data: {
  assignment_id: number;
  new_day: number;
  new_period: number;
  new_classroom_id?: number;
}) {
  return request<ApiResponse<CourseAssignment>>({
    url: `/scheduling/plans/${planId}/adjust`,
    method: 'post',
    data,
  });
}

/**
 * 发布排课计划
 */
export function publishPlan(planId: number) {
  return request<ApiResponse<SchedulingPlan>>({
    url: `/scheduling/plans/${planId}/publish`,
    method: 'post',
  });
}

/**
 * 获取课表
 */
export function getScheduleTable(planId: number, params?: {
  class_id?: number;
  teacher_id?: number;
}) {
  return request<ApiResponse<ScheduleTable>>({
    url: `/scheduling/plans/${planId}/table`,
    method: 'get',
    params,
  });
}

/**
 * 获取排课汇总
 */
export function getScheduleSummary(planId: number) {
  return request<ApiResponse<ScheduleSummary>>({
    url: `/scheduling/plans/${planId}/summary`,
    method: 'get',
  });
}

/**
 * 获取班级列表
 */
export function getClasses() {
  return request<ApiResponse<ClassInfo[]>>({
    url: '/scheduling/classes',
    method: 'get',
  });
}

/**
 * 获取课程列表
 */
export function getCourses() {
  return request<ApiResponse<CourseInfo[]>>({
    url: '/scheduling/courses',
    method: 'get',
  });
}

/**
 * 获取教师列表
 */
export function getTeachers() {
  return request<ApiResponse<TeacherInfo[]>>({
    url: '/scheduling/teachers',
    method: 'get',
  });
}

/**
 * 获取教室列表
 */
export function getClassrooms() {
  return request<ApiResponse<ClassroomInfo[]>>({
    url: '/scheduling/classrooms',
    method: 'get',
  });
}

// ============== Utility Functions ==============

/**
 * 获取星期标签
 */
export function getDayLabel(dayOfWeek: number): string {
  const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
  return days[dayOfWeek - 1] || '未知';
}

/**
 * 获取课程节次标签
 */
export function getPeriodLabel(period: number): string {
  return `第${period}节`;
}

/**
 * 获取状态标签
 */
export function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: '草稿',
    optimizing: '优化中',
    optimized: '已优化',
    reviewing: '审核中',
    published: '已发布',
    archived: '已归档',
  };
  return labels[status] || status;
}

/**
 * 获取状态颜色
 */
export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    draft: 'default',
    optimizing: 'processing',
    optimized: 'success',
    reviewing: 'warning',
    published: 'success',
    archived: 'default',
  };
  return colors[status] || 'default';
}

/**
 * 获取冲突严重程度标签
 */
export function getSeverityLabel(severity: number): string {
  if (severity >= 4) return '严重';
  if (severity >= 3) return '中等';
  return '轻微';
}

/**
 * 获取冲突严重程度颜色
 */
export function getSeverityColor(severity: number): string {
  if (severity >= 4) return 'red';
  if (severity >= 3) return 'orange';
  return 'gold';
}

/**
 * 获取冲突类型标签
 */
export function getConflictTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    teacher_conflict: '教师冲突',
    class_conflict: '班级冲突',
    classroom_conflict: '教室冲突',
    availability_conflict: '可用性冲突',
  };
  return labels[type] || type;
}

/**
 * 获取冲突类型颜色
 */
export function getConflictTypeColor(type: string): string {
  const colors: Record<string, string> = {
    teacher_conflict: 'purple',
    class_conflict: 'red',
    classroom_conflict: 'orange',
    availability_conflict: 'blue',
  };
  return colors[type] || 'default';
}

/**
 * 格式化时间段
 */
export function formatTimeSlot(slot: TimeSlot): string {
  return `${getDayLabel(slot.day_of_week)} ${getPeriodLabel(slot.period)}`;
}

/**
 * 格式化课程时长
 */
export function formatDuration(duration: number): string {
  if (duration === 1) return '1节课';
  return `${duration}节课`;
}

// ============== Constants ==============

/**
 * 星期选项
 */
export const DAY_OPTIONS = [
  { value: 1, label: '周一' },
  { value: 2, label: '周二' },
  { value: 3, label: '周三' },
  { value: 4, label: '周四' },
  { value: 5, label: '周五' },
  { value: 6, label: '周六' },
  { value: 7, label: '周日' },
];

/**
 * 课程节次选项
 */
export const PERIOD_OPTIONS = Array.from({ length: 10 }, (_, i) => ({
  value: i + 1,
  label: `第${i + 1}节`,
}));

/**
 * 排课状态选项
 */
export const STATUS_OPTIONS = [
  { value: 'draft', label: '草稿' },
  { value: 'optimizing', label: '优化中' },
  { value: 'optimized', label: '已优化' },
  { value: 'reviewing', label: '审核中' },
  { value: 'published', label: '已发布' },
  { value: 'archived', label: '已归档' },
];

/**
 * 学年选项
 */
export const ACADEMIC_YEAR_OPTIONS = [
  { value: '2024-2025', label: '2024-2025学年' },
  { value: '2025-2026', label: '2025-2026学年' },
  { value: '2026-2027', label: '2026-2027学年' },
];

/**
 * 学期选项
 */
export const SEMESTER_OPTIONS = [
  { value: '第一学期', label: '第一学期' },
  { value: '第二学期', label: '第二学期' },
];
