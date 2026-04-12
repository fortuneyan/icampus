/**
 * 学习Agent API调用模块
 * AI驱动的个性化学习助手
 */

import request from '@/utils/request'

// ==================== 能力画像类型 ====================

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
  exam_analysis?: Record<string, unknown>
  recommendations: Array<{ type: string; text: string; priority: string }>
  report_date: string
}

export interface DiagnosisRequest {
  student_id: string
  course_id?: string
  course_name?: string
}

/** 学习对话消息 */
export interface LearningMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  attachments?: Attachment[]
  feedback?: MessageFeedback
}

/** 附件 */
export interface Attachment {
  id: string
  name: string
  type: 'image' | 'pdf' | 'document' | 'code'
  url: string
  size: number
}

/** 消息反馈 */
export interface MessageFeedback {
  rating: number
  comment?: string
  improved?: boolean
}

/** 学习会话 */
export interface LearningSession {
  id: string
  studentId: string
  subjectId?: number
  subjectName?: string
  status: 'active' | 'completed' | 'paused'
  startTime: Date
  endTime?: Date
  messages: LearningMessage[]
  context: SessionContext
}

/** 会话上下文 */
export interface SessionContext {
  currentTopic?: string
  learningGoal?: string
  difficulty?: 'easy' | 'medium' | 'hard'
  preferredStyle?: 'visual' | 'text' | 'practice'
  knowledgeLevel?: Record<string, number>
}

/** 学习计划 */
export interface LearningPlan {
  id: string
  studentId: string
  subjectId: number
  subjectName: string
  totalHours: number
  completedHours: number
  progress: number
  milestones: LearningMilestone[]
  recommendedTasks: Task[]
  startDate: Date
  targetDate: Date
  status: 'active' | 'completed' | 'paused'
}

/** 学习里程碑 */
export interface LearningMilestone {
  id: string
  title: string
  description: string
  targetDate: Date
  completed: boolean
  completedDate?: Date
  tasks: string[]
}

/** 推荐任务 */
export interface Task {
  id: string
  title: string
  description: string
  type: 'video' | 'reading' | 'practice' | 'quiz' | 'project'
  duration: number
  difficulty: 'easy' | 'medium' | 'hard'
  prerequisites: string[]
  estimatedTime: number
  resources: Resource[]
  completed: boolean
}

/** 学习资源 */
export interface Resource {
  id: string
  title: string
  type: 'video' | 'article' | 'exercise' | 'game'
  url: string
  duration?: number
  difficulty?: 'easy' | 'medium' | 'hard'
}

/** 学习路径 */
export interface LearningPath {
  id: string
  studentId: string
  subjectId: number
  subjectName: string
  nodes: PathNode[]
  edges: PathEdge[]
  currentNodeId: string
  completedNodes: string[]
  totalNodes: number
  estimatedDuration: number
}

/** 路径节点 */
export interface PathNode {
  id: string
  type: 'concept' | 'lesson' | 'exercise' | 'quiz' | 'milestone'
  title: string
  description: string
  content?: string
  prerequisites: string[]
  duration: number
  difficulty: 'easy' | 'medium' | 'hard'
  status: 'locked' | 'available' | 'in_progress' | 'completed'
  position: { x: number; y: number }
}

/** 路径边 */
export interface PathEdge {
  id: string
  source: string
  target: string
  type: 'sequence' | 'optional'
}

/** 知识图谱节点 */
export interface KnowledgeNode {
  id: string
  name: string
  category: string
  mastery: number
  connections: string[]
  importance: number
}

/** 知识掌握度 */
export interface KnowledgeMastery {
  nodeId: string
  nodeName: string
  mastery: number
  trend: 'up' | 'down' | 'stable'
  lastPracticed?: Date
  nextReview?: Date
}

/** AI推荐 */
export interface AIRecommendation {
  id: string
  type: 'content' | 'practice' | 'review' | 'break'
  title: string
  description: string
  reason: string
  priority: number
  estimatedMinutes: number
  confidence: number
  actionUrl?: string
}

/** 学习统计 */
export interface LearningStats {
  totalStudyTime: number
  weeklyStudyTime: number
  dailyAverage: number
  currentStreak: number
  longestStreak: number
  sessionsCompleted: number
  topicsLearned: number
  exercisesCompleted: number
  accuracyRate: number
  engagementScore: number
}

/** 性能分析 */
export interface PerformanceAnalysis {
  strengths: string[]
  weaknesses: string[]
  improvementAreas: ImprovementArea[]
  studyRecommendations: string[]
  predictedScores: Record<string, number>
}

/** 改进区域 */
export interface ImprovementArea {
  topic: string
  currentLevel: number
  targetLevel: number
  recommendedActions: string[]
  estimatedTime: number
}

/** 学习目标 */
export interface LearningGoal {
  id: string
  studentId: string
  title: string
  description: string
  targetDate: Date
  progress: number
  status: 'active' | 'achieved' | 'abandoned'
  milestones: GoalMilestone[]
}

/** 目标里程碑 */
export interface GoalMilestone {
  id: string
  title: string
  completed: boolean
  dueDate?: Date
}

/** 对话请求 */
export interface ChatRequest {
  message: string
  sessionId?: string
  context?: {
    subjectId?: number
    topic?: string
    difficulty?: string
  }
  attachments?: File[]
}

/** 对话响应 */
export interface ChatResponse {
  message: LearningMessage
  suggestions: string[]
  resources?: Resource[]
  nextSteps?: string[]
}

/** AI分析请求 */
export interface AnalysisRequest {
  studentId: string
  subjectId?: number
  dataRange: {
    start: Date
    end: Date
  }
}

/** 学习进度更新 */
export interface ProgressUpdate {
  studentId: string
  nodeId?: string
  taskId?: string
  completed: boolean
  score?: number
  timeSpent?: number
}

/** 学习Agent API */
export const learningAgentAPI = {
  // ==================== T11 新增：能力画像 & 知识图谱 ====================

  /** 获取学生能力画像（能力维度分析） */
  getAbilityProfile: (studentId: string, courseId?: string) => {
    return request.get<AbilityProfile>('/ai/learning/ability/' + studentId, {
      params: courseId ? { course_id: courseId } : {},
    })
  },

  /** 获取能力雷达图数据（ECharts 渲染用） */
  getAbilityRadar: (studentId: string, courseId?: string) => {
    return request.get<AbilityRadarData>('/ai/learning/radar/' + studentId, {
      params: courseId ? { course_id: courseId } : {},
    })
  },

  /** 获取知识图谱（知识点掌握度 + 前置依赖） */
  getKnowledgeGraph: (studentId: string, courseId?: string, courseName?: string) => {
    return request.get<KnowledgeGraph>('/ai/learning/knowledge-graph/' + studentId, {
      params: { course_id: courseId, course_name: courseName },
    })
  },

  /** 生成综合诊断报告 */
  generateDiagnosisReport: (data: DiagnosisRequest) => {
    return request.post<DiagnosisReport>('/ai/learning/report', data)
  },

  // ==================== 原有多模态 API（路径修复） ====================

  /** 开始新对话 */
  startSession: (params: {
    studentId: string
    subjectId?: number
    topic?: string
    difficulty?: string
  }) => {
    return request.post<LearningSession>('/ai/learning/session', params)
  },

  /** 继续对话 */
  continueSession: (sessionId: string) => {
    return request.get<LearningSession>(`/ai/learning/session/${sessionId}`)
  },

  /** 发送消息 */
  sendMessage: (sessionId: string, message: string, attachments?: File[]) => {
    const formData = new FormData()
    formData.append('message', message)
    if (attachments) {
      attachments.forEach(file => formData.append('attachments', file))
    }
    return request.post<ChatResponse>(`/ai/learning/session/${sessionId}/message`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  /** 获取学习计划 */
  getLearningPlan: (studentId: string, subjectId?: number) => {
    return request.get<LearningPlan>('/ai/learning/plan', {
      params: { studentId, subjectId }
    })
  },

  /** 生成学习计划 */
  generateLearningPlan: (params: {
    studentId: string
    subjectId: number
    targetHours: number
    targetDate: Date
    learningStyle?: string
  }) => {
    return request.post<LearningPlan>('/ai/learning/plan/generate', params)
  },

  /** 更新学习计划 */
  updateLearningPlan: (planId: string, updates: Partial<LearningPlan>) => {
    return request.put<LearningPlan>(`/ai/learning/plan/${planId}`, updates)
  },

  /** 获取学习路径 */
  getLearningPath: (studentId: string, subjectId: number) => {
    return request.get<LearningPath>(`/ai/learning/path/${studentId}/${subjectId}`)
  },

  /** 生成学习路径 */
  generateLearningPath: (params: {
    studentId: string
    subjectId: number
    currentLevel?: number
    targetLevel?: number
  }) => {
    return request.post<LearningPath>('/ai/learning/path/generate', params)
  },

  /** 更新路径节点 */
  updatePathNode: (pathId: string, nodeId: string, status: string) => {
    return request.put<PathNode>(`/ai/learning/path/${pathId}/node/${nodeId}`, { status })
  },

  /** 获取知识掌握度（简版） */
  getKnowledgeMastery: (studentId: string, subjectId?: number) => {
    return request.get<KnowledgeMastery[]>('/ai/learning/mastery/' + studentId, {
      params: subjectId ? { subjectId } : {},
    })
  },

  /** 获取AI推荐 */
  getRecommendations: (studentId: string, limit: number = 5) => {
    return request.get<AIRecommendation[]>('/ai/learning/recommendations/' + studentId, {
      params: { limit },
    })
  },

  /** 获取学习统计 */
  getLearningStats: (studentId: string) => {
    return request.get<LearningStats>('/ai/learning/stats/' + studentId)
  },

  /** 获取性能分析 */
  getPerformanceAnalysis: (studentId: string, subjectId?: number) => {
    return request.get<PerformanceAnalysis>('/ai/learning/analysis', {
      params: { studentId, subjectId }
    })
  },

  /** 获取学习目标 */
  getLearningGoals: (studentId: string) => {
    return request.get<LearningGoal[]>('/ai/learning/goals/' + studentId)
  },

  /** 创建学习目标 */
  createLearningGoal: (goal: Omit<LearningGoal, 'id'>) => {
    return request.post<LearningGoal>('/ai/learning/goals', goal)
  },

  /** 更新学习目标 */
  updateLearningGoal: (goalId: string, updates: Partial<LearningGoal>) => {
    return request.put<LearningGoal>(`/ai/learning/goals/${goalId}`, updates)
  },

  /** 删除学习目标 */
  deleteLearningGoal: (goalId: string) => {
    return request.delete<void>(`/ai/learning/goals/${goalId}`)
  },

  /** 更新学习进度 */
  updateProgress: (update: ProgressUpdate) => {
    return request.post<void>('/ai/learning/progress', update)
  },

  /** 获取会话历史 */
  getSessionHistory: (studentId: string, params?: {
    subjectId?: number
    limit?: number
    offset?: number
  }) => {
    return request.get<LearningSession[]>('/ai/learning/sessions/' + studentId, { params })
  },

  /** 结束会话 */
  endSession: (sessionId: string) => {
    return request.post<LearningSession>(`/ai/learning/session/${sessionId}/end`)
  },

  /** 评价消息 */
  rateMessage: (messageId: string, rating: number, comment?: string) => {
    return request.post<MessageFeedback>(`/ai/learning/message/${messageId}/feedback`, {
      rating,
      comment
    })
  },

  /** 同步学习数据 */
  syncLearningData: (studentId: string) => {
    return request.post<void>('/ai/learning/sync', { studentId })
  },

  /** 获取学习助手状态 */
  getAssistantStatus: (studentId: string) => {
    return request.get<{
      online: boolean
      currentSession?: LearningSession
      pendingRecommendations: number
      streakInfo: { current: number; longest: number }
    }>('/ai/learning/status/' + studentId)
  }
}

export default learningAgentAPI
