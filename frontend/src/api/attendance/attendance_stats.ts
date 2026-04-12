// -*- coding: utf-8 -*-
/**
 * T4: 考勤统计报表
 * 前端API调用模块
 */

import request from '@/utils/request';

// ============== Type Definitions ==============

export interface StatQuery {
  stat_type: 'daily' | 'weekly' | 'monthly' | 'term' | 'yearly';
  dimension: 'student' | 'class' | 'teacher' | 'course' | 'department';
  start_date: string;
  end_date: string;
  dimension_id?: number;
  class_id?: number;
  teacher_id?: number;
  page?: number;
  page_size?: number;
}

export interface ReportQuery {
  report_type: 'summary' | 'detail' | 'abnormal' | 'comparison';
  start_date: string;
  end_date: string;
  dimension?: 'student' | 'class' | 'teacher' | 'course' | 'department';
  class_id?: number;
  teacher_id?: number;
  include_abnormal?: boolean;
  compare_with_previous?: boolean;
}

export interface AttendanceStatRecord {
  id: number;
  stat_type: string;
  dimension: string;
  dimension_id: number;
  dimension_name: string;
  stat_date: string;
  total_count: number;
  normal_count: number;
  late_count: number;
  early_leave_count: number;
  absent_count: number;
  leave_count: number;
  normal_rate: number;
  attendance_rate: number;
  avg_early_minutes: number;
  avg_late_minutes: number;
}

export interface AbnormalRecord {
  id: number;
  student_id: number;
  student_name: string;
  class_id: number;
  class_name: string;
  abnormal_type: 'late' | 'early_leave' | 'absent';
  course_id?: number;
  course_name?: string;
  teacher_id?: number;
  teacher_name?: string;
  record_date: string;
  late_minutes: number;
  early_minutes: number;
  severity: 'low' | 'medium' | 'high';
  status: 'pending' | 'handled';
  reason?: string;
  handled_by?: number;
  handled_at?: string;
  handle_result?: string;
}

export interface ReportSummary {
  total_students: number;
  total_normal: number;
  total_late: number;
  total_early_leave: number;
  total_absent: number;
  total_leave: number;
  overall_normal_rate: number;
  overall_attendance_rate: number;
}

export interface AttendanceReport {
  id: number;
  report_type: string;
  title: string;
  start_date: string;
  end_date: string;
  stat_dimension: string;
  stat_records: AttendanceStatRecord[];
  summary: ReportSummary;
  trend?: 'normal' | 'improving' | 'deteriorating';
  abnormal_records: AbnormalRecord[];
  comparison_data?: {
    period: { start_date: string; end_date: string };
    summary: { total_students: number; overall_normal_rate: number; overall_attendance_rate: number };
  };
  generated_by?: number;
  created_at: string;
}

export interface RankingItem {
  rank: number;
  dimension_id: number;
  dimension_name: string;
  normal_rate: number;
  attendance_rate: number;
  late_count: number;
  absent_count: number;
  trend?: 'normal' | 'improving' | 'deteriorating';
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
 * 获取考勤统计数据
 */
export function getAttendanceStats(params: StatQuery) {
  return request<ApiResponse<{
    records: AttendanceStatRecord[];
    pagination: Pagination;
  }>>({
    url: '/attendance/stats',
    method: 'get',
    params,
  });
}

/**
 * 获取考勤汇总
 */
export function getAttendanceSummary(params: {
  start_date: string;
  end_date: string;
  dimension?: 'student' | 'class' | 'teacher' | 'course' | 'department';
  class_id?: number;
  teacher_id?: number;
}) {
  return request<ApiResponse<{
    period: { start_date: string; end_date: string };
    summary: ReportSummary;
    dimension_stats: Array<{
      dimension_id: number;
      dimension_name: string;
      total_count: number;
      normal_count: number;
      late_count: number;
      early_leave_count: number;
      absent_count: number;
      leave_count: number;
      normal_rate: number;
      attendance_rate: number;
    }>;
  }>>({
    url: '/attendance/summary',
    method: 'get',
    params,
  });
}

/**
 * 获取考勤异常记录
 */
export function getAbnormalRecords(params: {
  start_date: string;
  end_date: string;
  class_id?: number;
  teacher_id?: number;
  abnormal_type?: 'late' | 'early_leave' | 'absent';
  severity?: 'low' | 'medium' | 'high';
  status?: 'pending' | 'handled';
  page?: number;
  page_size?: number;
}) {
  return request<ApiResponse<{
    records: AbnormalRecord[];
    statistics: {
      total: number;
      by_type: Record<string, number>;
      by_severity: { high: number; medium: number; low: number };
      by_status: { pending: number; handled: number };
    };
    pagination: Pagination;
  }>>({
    url: '/attendance/abnormal',
    method: 'get',
    params,
  });
}

/**
 * 生成考勤报表
 */
export function generateReport(params: ReportQuery) {
  return request<ApiResponse<AttendanceReport>>({
    url: '/attendance/report',
    method: 'get',
    params,
  });
}

/**
 * 获取考勤排名
 */
export function getAttendanceRanking(params: {
  dimension?: 'student' | 'class' | 'teacher' | 'course' | 'department';
  start_date: string;
  end_date: string;
  ranking_type?: 'attendance' | 'normal' | 'late' | 'absent';
  limit?: number;
}) {
  return request<ApiResponse<{
    dimension: string;
    ranking_type: string;
    period: { start_date: string; end_date: string };
    ranking: RankingItem[];
  }>>({
    url: '/attendance/ranking',
    method: 'get',
    params,
  });
}

/**
 * 导出考勤报表
 */
export function exportReport(params: { report_id: number; export_format?: 'excel' | 'pdf' | 'csv' }) {
  return request<ApiResponse<{
    report_id: number;
    export_format: string;
    download_url: string;
    expires_at: string;
  }>>({
    url: `/attendance/export/${params.report_id}`,
    method: 'get',
    params: { export_format: params.export_format || 'excel' },
  });
}

/**
 * 处理异常记录
 */
export function handleAbnormalRecord(params: {
  id: number;
  result: string;
  handler_id?: number;
}) {
  return request<ApiResponse>({
    url: `/attendance/abnormal/${params.id}/handle`,
    method: 'put',
    data: {
      handle_result: params.result,
      handled_by: params.handler_id,
    },
  });
}

// ============== Utility Functions ==============

/**
 * 格式化考勤率
 */
export function formatAttendanceRate(rate: number): string {
  return `${rate.toFixed(2)}%`;
}

/**
 * 获取趋势标签
 */
export function getTrendLabel(trend: string | undefined): string {
  const labels: Record<string, string> = {
    normal: '正常',
    improving: '改善中',
    deteriorating: '恶化中',
  };
  return labels[trend || 'normal'] || '未知';
}

/**
 * 获取趋势颜色
 */
export function getTrendColor(trend: string | undefined): string {
  const colors: Record<string, string> = {
    normal: '#52c41a',
    improving: '#1890ff',
    deteriorating: '#ff4d4f',
  };
  return colors[trend || 'normal'] || '#999';
}

/**
 * 获取异常类型标签
 */
export function getAbnormalTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    late: '迟到',
    early_leave: '早退',
    absent: '缺勤',
  };
  return labels[type] || type;
}

/**
 * 获取异常类型颜色
 */
export function getAbnormalTypeColor(type: string): string {
  const colors: Record<string, string> = {
    late: '#faad14',
    early_leave: '#fa8c16',
    absent: '#ff4d4f',
  };
  return colors[type] || '#999';
}

/**
 * 获取严重程度标签
 */
export function getSeverityLabel(severity: string): string {
  const labels: Record<string, string> = {
    low: '轻微',
    medium: '中等',
    high: '严重',
  };
  return labels[severity] || severity;
}

/**
 * 获取严重程度颜色
 */
export function getSeverityColor(severity: string): string {
  const colors: Record<string, string> = {
    low: '#52c41a',
    medium: '#faad14',
    high: '#ff4d4f',
  };
  return colors[severity] || '#999';
}

/**
 * 统计类型选项
 */
export const STAT_TYPE_OPTIONS = [
  { value: 'daily', label: '日统计' },
  { value: 'weekly', label: '周统计' },
  { value: 'monthly', label: '月统计' },
  { value: 'term', label: '学期统计' },
  { value: 'yearly', label: '年度统计' },
];

/**
 * 统计维度选项
 */
export const DIMENSION_OPTIONS = [
  { value: 'student', label: '按学生' },
  { value: 'class', label: '按班级' },
  { value: 'teacher', label: '按教师' },
  { value: 'course', label: '按课程' },
  { value: 'department', label: '按部门' },
];

/**
 * 报表类型选项
 */
export const REPORT_TYPE_OPTIONS = [
  { value: 'summary', label: '汇总报表' },
  { value: 'detail', label: '明细报表' },
  { value: 'abnormal', label: '异常报表' },
  { value: 'comparison', label: '对比报表' },
];

/**
 * 排名类型选项
 */
export const RANKING_TYPE_OPTIONS = [
  { value: 'attendance', label: '出勤率排名' },
  { value: 'normal', label: '正常率排名' },
  { value: 'late', label: '迟到最少排名' },
  { value: 'absent', label: '缺勤最少排名' },
];

/**
 * 异常类型选项
 */
export const ABNORMAL_TYPE_OPTIONS = [
  { value: 'late', label: '迟到' },
  { value: 'early_leave', label: '早退' },
  { value: 'absent', label: '缺勤' },
];

/**
 * 严重程度选项
 */
export const SEVERITY_OPTIONS = [
  { value: 'low', label: '轻微' },
  { value: 'medium', label: '中等' },
  { value: 'high', label: '严重' },
];

/**
 * 处理状态选项
 */
export const STATUS_OPTIONS = [
  { value: 'pending', label: '待处理' },
  { value: 'handled', label: '已处理' },
];
