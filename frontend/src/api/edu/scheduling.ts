// -*- coding: utf-8 -*-
/**
 * T5: 智能排课
 * 前端API调用模块 - 数据库持久化版本
 */

import request from '@/utils/request';

// ============== Type Definitions ==============

// 学期相关
export interface Semester {
  id: string;
  name: string;
  academic_year: string;
  semester: number;
  start_date: string;
  end_date: string;
  status: string;
  created_at: string;
}

// 周次组合
export interface Cycle {
  id: string;
  semester_id: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
  cycle_type: string;
  remark?: string;
  created_at: string;
}

// 日历映射
export interface CalendarMap {
  id: string;
  natural_date: string;
  cycle_id: string;
  exec_day: number;
  is_workday: boolean;
  is_holiday: boolean;
  remark?: string;
  created_at: string;
}

// 课表模板
export interface Template {
  id: string;
  semester_id: string;
  name: string;
  template_type: string;
  start_date?: string;
  end_date?: string;
  priority: number;
  is_active: boolean;
  remark?: string;
  created_at: string;
}

// 节次
export interface Period {
  id: string;
  template_id: string;
  period_index: number;
  start_time: string;
  end_time: string;
  period_type: string;
  duration: number;
  remark?: string;
}

// 课程规划
export interface Plan {
  id: string;
  cycle_id: string;
  class_id: string;
  teacher_id: string;
  course_id: string;
  total_hours: number;
  is_continuous: boolean;
  continuous_length: number;
  priority: number;
  remark?: string;
  created_at: string;
}

// 排课结果
export interface Result {
  id: string;
  cycle_id: string;
  class_id: string;
  teacher_id: string;
  course_id: string;
  room_id?: string;
  day_index: number;
  period_index: number;
  week_start?: number;
  week_end?: number;
  is_locked: boolean;
  create_type: string;
  template_id?: string;
  remark?: string;
  created_at: string;
}

// 调课补丁
export interface Patch {
  id: string;
  natural_date: string;
  class_id: string;
  day_index: number;
  period_index: number;
  original_teacher_id?: string;
  patch_teacher_id?: string;
  original_course_id?: string;
  patch_course_id?: string;
  original_room_id?: string;
  patch_room_id?: string;
  patch_type: string;
  status: string;
  reason?: string;
  applicant_id?: string;
  approver_id?: string;
  approved_at?: string;
  remark?: string;
  created_at: string;
}

// 约束
export interface Constraint {
  id: string;
  semester_id?: string;
  constraint_type: 'HARD' | 'SOFT';
  name: string;
  description?: string;
  target_type?: string;
  target_id?: string;
  day_index?: number;
  period_start?: number;
  period_end?: number;
  is_active: boolean;
  priority: number;
  created_at: string;
}

// 事件
export interface Event {
  id: string;
  semester_id: string;
  name: string;
  event_type: string;
  start_date: string;
  end_date: string;
  scope: string;
  target_grade_id?: string;
  target_class_id?: string;
  affect_schedule: boolean;
  status: string;
  remark?: string;
  created_at: string;
}

// 长期代课
export interface Replace {
  id: string;
  original_teacher_id: string;
  replace_teacher_id: string;
  course_id?: string;
  semester_id?: string;
  start_date: string;
  end_date: string;
  reason?: string;
  status: string;
  created_at: string;
}

// 课表单元格
export interface ScheduleCell {
  result_id?: string;
  course_id?: string;
  course_name: string;
  teacher_id?: string;
  teacher_name: string;
  room_id?: string;
  room_name: string;
  is_locked: boolean;
  create_type: string;
}

// 一天的课表
export interface DaySchedule {
  day_index: number;
  day_name: string;
  periods: ScheduleCell[];
}

// 班级课表
export interface ClassSchedule {
  class_id: string;
  class_name: string;
  cycle_id: string;
  days: DaySchedule[];
}

// 教师课表
export interface TeacherSchedule {
  teacher_id: string;
  teacher_name: string;
  cycle_id: string;
  days: DaySchedule[];
}

// 冲突信息
export interface Conflict {
  conflict_type: string;
  severity: number;
  message: string;
  related_ids: string[];
}

// 冲突检测结果
export interface ConflictCheckResult {
  has_conflicts: boolean;
  conflicts: Conflict[];
  total: number;
}

// 拖拽调整请求
export interface DragAdjustRequest {
  result_id: string;
  new_day_index: number;
  new_period_index: number;
  check_conflict: boolean;
}

// 拖拽调整响应
export interface DragAdjustResult {
  success: boolean;
  message: string;
  has_conflict: boolean;
  conflicts: Conflict[];
}

// 基础信息
export interface ClassInfo {
  id: string;
  name: string;
  grade_level: number | null;  // 班级所属年级（7=初一, 8=初二, 9=初三, 10=高一, 11=高二, 12=高三）
}

// 排课辅助接口的类型定义
export interface CourseInfo {
  id: string;
  name: string;
  code: string;
  teacher_id: string | null;
  teacher_ids: string[];
  grade_id: string | null;
  grade_levels: number[];  // 适用年级级别，如 [10, 11, 12] 表示高一、高二、高三
  semester: string | null;
  course_type: string;
}

export interface TeacherInfo {
  id: string;
  name: string;
}

export interface ClassroomInfo {
  id: string;
  name: string;
  capacity?: number;
}

// ============== API Functions ==============

// 学期管理
export function getSemesters(status?: string) {
  return request({
    url: '/edu/scheduling/semesters',
    method: 'get',
    params: { status },
  });
}

export function getSemester(semesterId: string) {
  return request({
    url: `/edu/scheduling/semesters/${semesterId}`,
    method: 'get',
  });
}

export function createSemester(data: {
  name: string;
  academic_year: string;
  semester: number;
  start_date: string;
  end_date: string;
}) {
  return request({
    url: '/edu/scheduling/semesters',
    method: 'post',
    data,
  });
}

// 周次组合管理
export function getCycles(semesterId?: string) {
  return request({
    url: '/edu/scheduling/cycles',
    method: 'get',
    params: { semester_id: semesterId },
  });
}

export function createCycle(data: {
  id: string;
  semester_id: string;
  start_date: string;
  end_date: string;
  cycle_type?: string;
}) {
  return request({
    url: '/edu/scheduling/cycles',
    method: 'post',
    data,
  });
}

export function setCurrentCycle(cycleId: string) {
  return request({
    url: `/edu/scheduling/cycles/${cycleId}/set-current`,
    method: 'put',
  });
}

// 日历映射管理
export function getCalendarMaps(params: {
  start_date?: string;
  end_date?: string;
  is_holiday?: boolean;
}) {
  return request({
    url: '/edu/scheduling/calendar-maps',
    method: 'get',
    params,
  });
}

export function getCalendarMap(naturalDate: string) {
  return request({
    url: `/edu/scheduling/calendar-maps/${naturalDate}`,
    method: 'get',
  });
}

export function createCalendarMap(data: {
  natural_date: string;
  cycle_id: string;
  exec_day: number;
  is_workday?: boolean;
  is_holiday?: boolean;
}) {
  return request({
    url: '/edu/scheduling/calendar-maps',
    method: 'post',
    data,
  });
}

export function batchCreateCalendarMaps(items: Array<{
  natural_date: string;
  cycle_id: string;
  exec_day: number;
  is_workday?: boolean;
  is_holiday?: boolean;
}>) {
  return request({
    url: '/edu/scheduling/calendar-maps/batch',
    method: 'post',
    data: items,
  });
}

// 课表模板管理
export function getTemplates(semesterId: string) {
  return request({
    url: '/edu/scheduling/templates',
    method: 'get',
    params: { semester_id: semesterId },
  });
}

export function createTemplate(data: {
  semester_id: string;
  name: string;
  template_type?: string;
  start_date?: string;
  end_date?: string;
  priority?: number;
}) {
  return request({
    url: '/edu/scheduling/templates',
    method: 'post',
    data,
  });
}

export function getPeriods(templateId: string) {
  return request({
    url: `/edu/scheduling/templates/${templateId}/periods`,
    method: 'get',
  });
}

export function createPeriod(data: {
  template_id: string;
  period_index: number;
  start_time: string;
  end_time: string;
  period_type?: string;
  duration?: number;
}) {
  return request({
    url: `/edu/scheduling/templates/${data.template_id}/periods`,
    method: 'post',
    data,
  });
}

// 课程规划管理
export function getPlans(params: {
  cycle_id?: string;
  class_id?: string;
  teacher_id?: string;
}) {
  return request({
    url: '/edu/scheduling/plans',
    method: 'get',
    params,
  });
}

export function createPlan(data: {
  cycle_id: string;
  class_id: string;
  teacher_id: string;
  course_id: string;
  total_hours: number;
  is_continuous?: boolean;
  continuous_length?: number;
  priority?: number;
}) {
  return request({
    url: '/edu/scheduling/plans',
    method: 'post',
    data,
  });
}

export function batchCreatePlans(items: Array<{
  cycle_id: string;
  class_id: string;
  teacher_id: string;
  course_id: string;
  total_hours: number;
  is_continuous?: boolean;
  continuous_length?: number;
  priority?: number;
}>) {
  return request({
    url: '/edu/scheduling/plans/batch',
    method: 'post',
    data: items,
  });
}

// 排课结果管理
export function getResults(params: {
  cycle_id?: string;
  class_id?: string;
  teacher_id?: string;
  day_index?: number;
}) {
  return request({
    url: '/edu/scheduling/results',
    method: 'get',
    params,
  });
}

export function createResult(data: {
  cycle_id: string;
  class_id: string;
  teacher_id: string;
  course_id: string;
  day_index: number;
  period_index: number;
  room_id?: string;
  week_start?: number;
  week_end?: number;
  is_locked?: boolean;
  create_type?: string;
}) {
  return request({
    url: '/edu/scheduling/results',
    method: 'post',
    data,
  });
}

export function updateResult(
  resultId: string,
  data: {
    day_index?: number;
    period_index?: number;
    is_locked?: boolean;
  }
) {
  return request({
    url: `/edu/scheduling/results/${resultId}`,
    method: 'put',
    data,
  });
}

export function deleteResults(cycleId: string, lockedOnly?: boolean) {
  return request({
    url: `/edu/scheduling/results/${cycleId}`,
    method: 'delete',
    params: { locked_only: lockedOnly },
  });
}

// 调课补丁管理
export function getPatches(params: {
  natural_date?: string;
  class_id?: string;
  status?: string;
}) {
  return request({
    url: '/edu/scheduling/patches',
    method: 'get',
    params,
  });
}

export function createPatch(data: {
  natural_date: string;
  class_id: string;
  day_index: number;
  period_index: number;
  original_teacher_id?: string;
  patch_teacher_id?: string;
  original_course_id?: string;
  patch_course_id?: string;
  patch_type?: string;
  reason?: string;
}) {
  return request({
    url: '/edu/scheduling/patches',
    method: 'post',
    data,
  });
}

export function cancelPatch(patchId: string) {
  return request({
    url: `/edu/scheduling/patches/${patchId}/cancel`,
    method: 'put',
  });
}

// 冲突检测
export function checkConflicts(params: {
  cycle_id: string;
  class_id?: string;
  teacher_id?: string;
}) {
  return request({
    url: '/edu/scheduling/conflicts',
    method: 'get',
    params,
  });
}

// 课表查询
export function getClassSchedule(params: {
  class_id: string;
  cycle_id?: string;
  natural_date?: string;
}) {
  return request({
    url: `/edu/scheduling/schedule/class/${params.class_id}`,
    method: 'get',
    params: { cycle_id: params.cycle_id, natural_date: params.natural_date },
  });
}

export function getTeacherSchedule(params: {
  teacher_id: string;
  cycle_id?: string;
  natural_date?: string;
}) {
  return request({
    url: `/edu/scheduling/schedule/teacher/${params.teacher_id}`,
    method: 'get',
    params: { cycle_id: params.cycle_id, natural_date: params.natural_date },
  });
}

// 拖拽调整
export function dragAdjust(data: DragAdjustRequest) {
  return request({
    url: '/edu/scheduling/drag-adjust',
    method: 'post',
    data,
  });
}

// 事件管理
export function getEvents(params: {
  semester_id: string;
  start_date?: string;
  end_date?: string;
}) {
  return request({
    url: '/edu/scheduling/events',
    method: 'get',
    params,
  });
}

export function createEvent(data: {
  semester_id: string;
  name: string;
  event_type: string;
  start_date: string;
  end_date: string;
  scope?: string;
  target_class_id?: string;
  affect_schedule?: boolean;
}) {
  return request({
    url: '/edu/scheduling/events',
    method: 'post',
    data,
  });
}

// 长期代课管理
export function createReplace(data: {
  original_teacher_id: string;
  replace_teacher_id: string;
  start_date: string;
  end_date: string;
  course_id?: string;
  semester_id?: string;
  reason?: string;
}) {
  return request({
    url: '/edu/scheduling/replaces',
    method: 'post',
    data,
  });
}

// 约束管理
export function getConstraints(params: {
  semester_id?: string;
  constraint_type?: string;
}) {
  return request({
    url: '/edu/scheduling/constraints',
    method: 'get',
    params,
  });
}

export function createConstraint(data: {
  semester_id?: string;
  constraint_type: 'HARD' | 'SOFT';
  name: string;
  description?: string;
  target_type?: string;
  target_id?: string;
  day_index?: number;
  period_start?: number;
  period_end?: number;
  priority?: number;
}) {
  return request({
    url: '/edu/scheduling/constraints',
    method: 'post',
    data,
  });
}

// 辅助接口
export function getClassesForScheduling() {
  return request({
    url: '/edu/scheduling/classes',
    method: 'get',
  });
}

export function getCoursesForScheduling() {
  return request({
    url: '/edu/scheduling/courses',
    method: 'get',
  });
}

export function getTeachersForScheduling() {
  return request({
    url: '/edu/scheduling/teachers',
    method: 'get',
  });
}

export function getClassroomsForScheduling() {
  return request({
    url: '/edu/scheduling/classrooms',
    method: 'get',
  });
}

// ============== Utility Functions ==============

export function getDayLabel(dayOfWeek: number): string {
  const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
  return days[dayOfWeek - 1] || '未知';
}

export function getPeriodLabel(period: number): string {
  return `第${period}节`;
}

export function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: '草稿',
    optimizing: '优化中',
    optimized: '已优化',
    reviewing: '审核中',
    published: '已发布',
    archived: '已归档',
    active: '生效中',
    cancelled: '已取消',
    completed: '已完成',
  };
  return labels[status] || status;
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    draft: 'info',
    optimizing: 'warning',
    optimized: 'success',
    reviewing: 'warning',
    published: 'success',
    archived: 'info',
    active: 'success',
    cancelled: 'danger',
    completed: 'info',
  };
  return colors[status] || 'info';
}

export function getSeverityLabel(severity: number): string {
  if (severity >= 4) return '严重';
  if (severity >= 3) return '中等';
  return '轻微';
}

export function getSeverityColor(severity: number): string {
  if (severity >= 4) return 'danger';
  if (severity >= 3) return 'warning';
  return 'info';
}

export function getConflictTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    teacher_conflict: '教师冲突',
    class_conflict: '班级冲突',
    room_conflict: '教室冲突',
    classroom_conflict: '教室冲突',
    availability_conflict: '可用性冲突',
  };
  return labels[type] || type;
}

// ============== Constants ==============

export const DAY_OPTIONS = [
  { value: 1, label: '周一' },
  { value: 2, label: '周二' },
  { value: 3, label: '周三' },
  { value: 4, label: '周四' },
  { value: 5, label: '周五' },
  { value: 6, label: '周六' },
  { value: 7, label: '周日' },
];

export const PERIOD_OPTIONS = Array.from({ length: 10 }, (_, i) => ({
  value: i + 1,
  label: `第${i + 1}节`,
}));

export const STATUS_OPTIONS = [
  { value: 'draft', label: '草稿' },
  { value: 'optimizing', label: '优化中' },
  { value: 'optimized', label: '已优化' },
  { value: 'reviewing', label: '审核中' },
  { value: 'published', label: '已发布' },
  { value: 'archived', label: '已归档' },
];

export const ACADEMIC_YEAR_OPTIONS = [
  { value: '2024-2025', label: '2024-2025学年' },
  { value: '2025-2026', label: '2025-2026学年' },
  { value: '2026-2027', label: '2026-2027学年' },
];

export const SEMESTER_OPTIONS = [
  { value: 1, label: '第一学期' },
  { value: 2, label: '第二学期' },
];

export const CONSTRAINT_TYPE_OPTIONS = [
  { value: 'HARD', label: '硬约束' },
  { value: 'SOFT', label: '软约束' },
];

export const EVENT_TYPE_OPTIONS = [
  { value: 'sports_meet', label: '运动会' },
  { value: 'excursion', label: '春游/研学' },
  { value: 'exam', label: '考试' },
  { value: 'orientation', label: '入学教育' },
  { value: 'custom', label: '自定义' },
];

export const PATCH_TYPE_OPTIONS = [
  { value: 'swap', label: '换课' },
  { value: 'substitute', label: '代课' },
  { value: 'cancel', label: '停课' },
  { value: 'self_study', label: '转自习' },
];
