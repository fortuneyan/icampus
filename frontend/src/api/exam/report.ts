/**
 * 成绩报表API
 */
import request from '@/utils/request'

// ==================== 类型定义 ====================

export interface StudentScore {
  student_id: number
  student_name: string
  exam_id: number
  subject_id: number
  subject_name: string
  score: number
  full_score: number
  rank: number
  grade_level: 'A' | 'B' | 'C' | 'D' | 'F'
  percentile: number
  is_pass: boolean
}

export interface StudentReport {
  student_id: number
  student_name: string
  academic_year: string
  semester: number
  total_courses: number
  passed_courses: number
  failed_courses: number
  total_score: number
  average_score: number
  highest_score: number
  lowest_score: number
  gpa: number
  pass_rate: number
  completion_rate: number
  grades_distribution: {
    excellent: number
    good: number
    average: number
    pass: number
    fail: number
  }
  class_rank: number
  grade_rank: number
}

export interface ClassReport {
  class_id: number
  class_name: string
  academic_year: string
  semester: number
  total_students: number
  total_exams: number
  class_average: number
  highest_score: number
  lowest_score: number
  score_std: number
  pass_count: number
  pass_rate: number
  excellent_count: number
  excellent_rate: number
  subject_averages: Record<string, number>
  score_distribution: Record<string, number>
}

export interface SubjectReport {
  subject_id: number
  subject_name: string
  academic_year: string
  semester: number
  total_students: number
  subject_average: number
  highest_score: number
  lowest_score: number
  median_score: number
  score_std: number
  pass_count: number
  pass_rate: number
  excellent_rate: number
  good_rate: number
  average_rate: number
  score_distribution: Record<string, number>
}

export interface ExamReport {
  exam_id: number
  exam_name: string
  academic_year: string
  semester: number
  exam_date: string
  total_students: number
  total_subjects: number
  overall_average: number
  highest_score: number
  lowest_score: number
  score_std: number
  pass_count: number
  pass_rate: number
  score_distribution: Record<string, number>
  subject_analysis: Array<{
    subject_name: string
    average: number
    pass_rate: number
    total_students: number
  }>
  difficulty_index: number
  discrimination_index: number
}

export interface TrendReport {
  student_id: number
  student_name: string
  academic_year: string
  semester_scores: Array<{
    semester: number
    average: number
  }>
  subject_trends: Record<string, number[]>
  overall_trend: '上升' | '下降' | '稳定' | 'stable'
  improvement_rate: number
  volatility: number
  predicted_next: number
}

export interface RankingItem {
  student_id: number
  average_score: number
  total_exams: number
  rank: number
}

export interface StatisticsOverview {
  total_students: number
  total_exams: number
  total_subjects: number
  overall_average: number
  overall_pass_rate: number
  highest_score: number
  lowest_score: number
}

export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

// ==================== 成绩录入API ====================

/**
 * 录入学生成绩
 */
export function addStudentScore(data: {
  student_id: number
  student_name: string
  exam_id: number
  subject_id: number
  subject_name: string
  score: number
  full_score?: number
}) {
  return request<ApiResponse<StudentScore>>({
    url: '/exam/reports/scores',
    method: 'post',
    data
  })
}

/**
 * 获取学生成绩列表
 */
export function getStudentScores(studentId: number, academicYear?: string) {
  return request<ApiResponse<StudentScore[]>>({
    url: `/exam/reports/scores/${studentId}`,
    method: 'get',
    params: { academic_year: academicYear }
  })
}

// ==================== 学生报表API ====================

/**
 * 生成学生成绩报表
 */
export function generateStudentReport(data: {
  student_id: number
  student_name: string
  academic_year: string
  semester?: number
}) {
  return request<ApiResponse<StudentReport>>({
    url: '/exam/reports/student',
    method: 'post',
    data
  })
}

/**
 * 获取学生成绩摘要
 */
export function getStudentSummary(
  studentId: number,
  academicYear: string,
  semester?: number
) {
  return request<ApiResponse<{
    student_id: number
    average_score: number
    gpa: number
    pass_rate: number
    class_rank: number
    grade_rank: number
  }>>({
    url: `/exam/reports/student/${studentId}/summary`,
    method: 'get',
    params: {
      academic_year: academicYear,
      semester: semester || 1
    }
  })
}

// ==================== 班级报表API ====================

/**
 * 生成班级成绩报表
 */
export function generateClassReport(data: {
  class_id: number
  class_name: string
  academic_year: string
  semester?: number
  student_ids: number[]
}) {
  return request<ApiResponse<ClassReport>>({
    url: '/exam/reports/class',
    method: 'post',
    data
  })
}

/**
 * 获取班级报表
 */
export function getClassReport(classId: number) {
  return request<ApiResponse<ClassReport>>({
    url: `/exam/reports/class/${classId}`,
    method: 'get'
  })
}

// ==================== 科目报表API ====================

/**
 * 生成科目成绩报表
 */
export function generateSubjectReport(data: {
  subject_id: number
  subject_name: string
  academic_year: string
  semester?: number
}) {
  return request<ApiResponse<SubjectReport>>({
    url: '/exam/reports/subject',
    method: 'post',
    data
  })
}

// ==================== 考试报表API ====================

/**
 * 生成考试分析报表
 */
export function generateExamReport(data: {
  exam_id: number
  exam_name: string
  academic_year: string
  semester?: number
  exam_date?: string
}) {
  return request<ApiResponse<ExamReport>>({
    url: '/exam/reports/exam',
    method: 'post',
    data
  })
}

// ==================== 趋势分析API ====================

/**
 * 生成成绩趋势报表
 */
export function generateTrendReport(data: {
  student_id: number
  student_name: string
  academic_year: string
}) {
  return request<ApiResponse<TrendReport>>({
    url: '/exam/reports/trend',
    method: 'post',
    data
  })
}

// ==================== 对比分析API ====================

/**
 * 学生对比分析
 */
export function compareStudents(data: {
  student_ids: number[]
  academic_year: string
  semester?: number
}) {
  return request<ApiResponse<{
    total: number
    items: Array<{
      student_id: number
      average_score: number
      pass_rate: number
      total_courses: number
      rank: number
    }>
  }>>({
    url: '/exam/reports/compare/students',
    method: 'post',
    data
  })
}

/**
 * 班级对比分析
 */
export function compareClasses(data: {
  class_ids: number[]
  academic_year: string
  semester?: number
}) {
  return request<ApiResponse<{
    total: number
    items: Array<{
      class_id: number
      class_name: string
      average_score: number
      pass_rate: number
      excellent_rate: number
      total_students: number
      rank: number
    }>
  }>>({
    url: '/exam/reports/compare/classes',
    method: 'post',
    data
  })
}

// ==================== 数据导出API ====================

/**
 * 导出学生成绩报表
 */
export function exportStudentReport(
  studentId: number,
  academicYear: string,
  semester?: number,
  format?: string
) {
  return request<ApiResponse<any>>({
    url: `/exam/reports/export/${studentId}`,
    method: 'get',
    params: {
      academic_year: academicYear,
      semester: semester || 1,
      format: format || 'json'
    }
  })
}

// ==================== 统计API ====================

/**
 * 获取成绩统计概览
 */
export function getStatisticsOverview(academicYear: string, semester?: number) {
  return request<ApiResponse<StatisticsOverview>>({
    url: '/exam/reports/statistics/overview',
    method: 'get',
    params: {
      academic_year: academicYear,
      semester: semester || 1
    }
  })
}

/**
 * 获取成绩排名
 */
export function getRanking(
  academicYear: string,
  semester?: number,
  subjectId?: number,
  classId?: number,
  limit?: number
) {
  return request<ApiResponse<{
    total: number
    items: RankingItem[]
  }>>({
    url: '/exam/reports/statistics/ranking',
    method: 'get',
    params: {
      academic_year: academicYear,
      semester: semester || 1,
      subject_id: subjectId,
      class_id: classId,
      limit: limit || 50
    }
  })
}

// ==================== 枚举映射 ====================

export const GradeLevelMap = {
  A: { text: '优秀', color: 'green' },
  B: { text: '良好', color: 'cyan' },
  C: { text: '中等', color: 'blue' },
  D: { text: '及格', color: 'orange' },
  F: { text: '不及格', color: 'red' }
}

export const TrendMap = {
  '上升': { text: '上升 📈', color: 'green' },
  '下降': { text: '下降 📉', color: 'red' },
  '稳定': { text: '稳定 ➡️', color: 'blue' },
  'stable': { text: '稳定 ➡️', color: 'blue' }
}

export const ScoreDistributionLabels = {
  '0-59': '0-59分',
  '60-69': '60-69分',
  '70-79': '70-79分',
  '80-89': '80-89分',
  '90-100': '90-100分'
}
