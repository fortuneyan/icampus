/**
 * AI 学习诊断与个性化推荐 API
 * 路径: /api/v1/ai/learning/{diagnosis|ability|radar|knowledge-graph|report}
 *
 * 注意：baseURL = /api/v1，故路径前缀为 /ai/learning/
 */
import request from '@/utils/request'

// ==================== 能力画像 & 知识图谱（T11 新增） ====================

export interface AbilityDimension {
  name: string
  score: number
  level: string
  trend: 'up' | 'down' | 'stable'
  evidence?: string[]
}

export interface AbilityProfile {
  student_id: string
  overall_score: number
  dimensions: AbilityDimension[]
  strengths: string[]
  weaknesses: string[]
  improvement_suggestions: string[]
  generated_at: string
}

export interface RadarIndicator {
  name: string
  value: number
}

export interface AbilityRadarData {
  student_id: string
  indicators: RadarIndicator[]
  avg_score: number
  highest_dimension: string
  lowest_dimension: string
  comparison_with_class?: number
}

export interface KnowledgeNode {
  node_id: string
  name: string
  parent_id?: string
  mastery: number
  difficulty: number
  importance: number
  prerequisites: string[]
  tags: string[]
  exam_frequency?: number
}

export interface KnowledgeEdge {
  source: string
  target: string
  relation: string
}

export interface KnowledgeGraph {
  student_id: string
  course_id?: string
  course_name?: string
  nodes: KnowledgeNode[]
  edges: KnowledgeEdge[]
  weakest_nodes: string[]
  learning_frontier: string[]
  generated_at: string
}

export interface DiagnosisReport {
  student_id: string
  report_id: string
  ability_profile?: AbilityProfile
  knowledge_graph?: KnowledgeGraph
  radar_data?: AbilityRadarData
  recommendations: Array<{ type: string; text: string; priority: string }>
  report_date: string
}

// ==================== 原有诊断类型 ====================

export interface DiagnosisRequest {
  student_id: string
  course_id?: string
  course_name?: string
  recent_scores?: Array<{ course: string; score: number; exam_type?: string }>
  learning_records?: Array<{ resource_name: string; action_type: string; duration: number }>
}

export interface DiagnosisResult {
  overall_evaluation: string
  knowledge_mastery: string
  learning_attitude: string
  time_management: string
  problems: string[]
  suggestions: string[]
  recommended_resources: Array<{ name: string; type: string; reason: string }>
  note?: string
}

// ==================== API 方法 ====================

/** T11：获取学生能力画像（多维度能力分析） */
export function getAbilityProfile(studentId: string, courseId?: string) {
  return request.get<AbilityProfile>('/ai/learning/ability/' + studentId, {
    params: courseId ? { course_id: courseId } : {},
  })
}

/** T11：获取能力雷达图数据（ECharts 渲染） */
export function getAbilityRadar(studentId: string, courseId?: string) {
  return request.get<AbilityRadarData>('/ai/learning/radar/' + studentId, {
    params: courseId ? { course_id: courseId } : {},
  })
}

/** T11：获取知识图谱（节点+边+前置依赖） */
export function getKnowledgeGraph(studentId: string, courseId?: string, courseName?: string) {
  return request.get<KnowledgeGraph>('/ai/learning/knowledge-graph/' + studentId, {
    params: { course_id: courseId, course_name: courseName },
  })
}

/** T11：生成综合诊断报告 */
export function generateDiagnosisReport(data: DiagnosisRequest) {
  return request.post<DiagnosisReport>('/ai/learning/report', data)
}

/** AI 学习诊断（文本分析） */
export function diagnoseStudent(data: DiagnosisRequest) {
  return request.post<DiagnosisResult>('/ai/learning/diagnosis', data)
}

/** 获取学生诊断历史与统计 */
export function getStudentDiagnosis(studentId: string) {
  return request.get('/ai/learning/diagnosis/student/' + studentId)
}

/** 获取学生个性化推荐 */
export function getStudentRecommendations(studentId: string, limit = 5) {
  return request.get('/ai/learning/recommendations/student/' + studentId, {
    params: { limit },
  })
}

/** 获取课程相关推荐 */
export function getCourseRecommendations(courseId: string, limit = 5) {
  return request.get('/ai/learning/recommendations/course/' + courseId, {
    params: { limit },
  })
}
