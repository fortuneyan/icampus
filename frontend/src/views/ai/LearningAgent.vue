<template>
  <div class="learning-agent">
    <!-- 头部 -->
    <div class="agent-header">
      <div class="header-left">
        <h2>🤖 学习Agent</h2>
        <span class="status-badge" :class="statusClass">
          {{ statusText }}
        </span>
      </div>
      <div class="header-actions">
        <el-select v-model="selectedSubject" placeholder="选择科目" size="small" @change="onSubjectChange">
          <el-option label="全部科目" :value="undefined" />
          <el-option v-for="subject in subjects" :key="subject.id" :label="subject.name" :value="subject.id" />
        </el-select>
        <el-button @click="showStatsDialog = true" size="small">学习统计</el-button>
        <el-button @click="showGoalsDialog = true" size="small">学习目标</el-button>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="agent-content">
      <!-- 左侧边栏 -->
      <div class="sidebar">
        <!-- 学习概览 -->
        <el-card class="overview-card">
          <template #header>
            <span>今日学习</span>
          </template>
          <div class="stats-grid">
            <div class="stat-item">
              <span class="stat-value">{{ todayStats.studyTime }}</span>
              <span class="stat-label">学习时长</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ todayStats.exercises }}</span>
              <span class="stat-label">完成练习</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ todayStats.accuracy }}%</span>
              <span class="stat-label">正确率</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ todayStats.streak }}</span>
              <span class="stat-label">连续天数</span>
            </div>
          </div>
        </el-card>

        <!-- AI推荐 -->
        <el-card class="recommendations-card">
          <template #header>
            <span>🎯 AI推荐</span>
          </template>
          <div class="recommendation-list">
            <div v-for="rec in recommendations" :key="rec.id" class="recommendation-item" @click="handleRecommendation(rec)">
              <div class="rec-icon" :class="rec.type">{{ getRecIcon(rec.type) }}</div>
              <div class="rec-content">
                <div class="rec-title">{{ rec.title }}</div>
                <div class="rec-desc">{{ rec.description }}</div>
                <div class="rec-meta">
                  <span class="rec-time">{{ rec.estimatedMinutes }}分钟</span>
                  <span class="rec-confidence">{{ Math.round(rec.confidence * 100) }}%置信</span>
                </div>
              </div>
            </div>
            <el-empty v-if="!recommendations.length" description="暂无推荐" :image-size="60" />
          </div>
        </el-card>

        <!-- 知识掌握度 -->
        <el-card class="mastery-card">
          <template #header>
            <span>📊 知识掌握</span>
          </template>
          <div class="mastery-list">
            <div v-for="item in knowledgeMastery" :key="item.nodeId" class="mastery-item">
              <div class="mastery-header">
                <span class="mastery-name">{{ item.nodeName }}</span>
                <span class="mastery-trend" :class="item.trend">
                  {{ getTrendIcon(item.trend) }}
                </span>
              </div>
              <el-progress :percentage="item.mastery" :color="getMasteryColor(item.mastery)" :show-text="true" />
            </div>
          </div>
        </el-card>
      </div>

      <!-- 右侧主区域 -->
      <div class="main-area">
        <!-- Tab页签 -->
        <el-tabs v-model="activeTab" class="main-tabs">
          <!-- 对话模式 -->
          <el-tab-pane label="💬 对话学习" name="chat">
            <div class="chat-container">
              <!-- 消息列表 -->
              <div ref="messageListRef" class="message-list">
                <div v-for="msg in messages" :key="msg.id" class="message" :class="msg.role">
                  <div class="message-avatar">
                    <span v-if="msg.role === 'user'">👤</span>
                    <span v-else>🤖</span>
                  </div>
                  <div class="message-content">
                    <div class="message-bubble" v-html="formatMessage(msg.content)"></div>
                    <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
                    <div v-if="msg.role === 'assistant' && msg.feedback" class="message-feedback">
                      <span>你的评价: {{ msg.feedback.rating }}⭐</span>
                    </div>
                    <div v-if="msg.role === 'assistant'" class="message-actions">
                      <el-button size="small" text @click="showFeedbackDialog(msg.id)">评价</el-button>
                      <el-button size="small" text @click="copyMessage(msg.content)">复制</el-button>
                    </div>
                  </div>
                </div>
                <div v-if="isTyping" class="message assistant">
                  <div class="message-avatar">🤖</div>
                  <div class="message-content">
                    <div class="typing-indicator">
                      <span></span><span></span><span></span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 建议快捷回复 -->
              <div v-if="suggestions.length && !isTyping" class="suggestions">
                <span class="suggestions-label">快捷回复：</span>
                <el-tag v-for="sug in suggestions" :key="sug" class="suggestion-tag" @click="sendSuggestion(sug)">
                  {{ sug }}
                </el-tag>
              </div>

              <!-- 输入区域 -->
              <div class="input-area">
                <div class="input-tools">
                  <el-button size="small" @click="showFileUpload = true">📎 附件</el-button>
                  <el-button size="small" @click="showQuickActions = !showQuickActions">⚡ 快捷操作</el-button>
                  <div v-if="showQuickActions" class="quick-actions">
                    <el-button size="small" @click="sendQuickAction('解释这个概念')">解释</el-button>
                    <el-button size="small" @click="sendQuickAction('出几道练习题')">练习题</el-button>
                    <el-button size="small" @click="sendQuickAction('总结本周学习内容')">总结</el-button>
                    <el-button size="small" @click="sendQuickAction('给我一些学习建议')">建议</el-button>
                  </div>
                </div>
                <el-input v-model="inputMessage" type="textarea" :rows="2" placeholder="输入你的问题..." @keydown.enter.ctrl="sendMessage" />
                <div class="input-actions">
                  <span class="input-hint">Ctrl+Enter 发送</span>
                  <el-button type="primary" :loading="isTyping" @click="sendMessage">发送</el-button>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 学习路径 -->
          <el-tab-pane label="🛤️ 学习路径" name="path">
            <div class="learning-path-container">
              <LearningPath v-if="currentStudentId" :subject-id="selectedSubject" :student-id="currentStudentId" />
            </div>
          </el-tab-pane>

          <!-- 学习计划 -->
          <el-tab-pane label="📅 学习计划" name="plan">
            <div class="plan-container">
              <div class="plan-header">
                <h3>个性化学习计划</h3>
                <el-button type="primary" @click="generatePlan">重新生成计划</el-button>
              </div>
              <el-timeline v-if="learningPlan">
                <el-timeline-item v-for="milestone in learningPlan.milestones" :key="milestone.id" :color="milestone.completed ? '#67C23A' : '#409EFF'">
                  <div class="milestone-card" :class="{ completed: milestone.completed }">
                    <div class="milestone-header">
                      <h4>{{ milestone.title }}</h4>
                      <el-tag v-if="milestone.completed" type="success" size="small">已完成</el-tag>
                      <el-tag v-else size="small">进行中</el-tag>
                    </div>
                    <p>{{ milestone.description }}</p>
                    <div class="milestone-meta">
                      <span>目标日期: {{ formatDate(milestone.targetDate) }}</span>
                      <span>任务数: {{ milestone.tasks.length }}</span>
                    </div>
                    <div class="milestone-progress">
                      <span>{{ milestone.tasks.filter(t => completedTasks.includes(t)).length }}/{{ milestone.tasks.length }}</span>
                      <el-progress :percentage="(milestone.tasks.filter(t => completedTasks.includes(t)).length / milestone.tasks.length) * 100" :show-text="false" />
                    </div>
                  </div>
                </el-timeline-item>
              </el-timeline>
              <el-empty v-else description="暂无学习计划" />
            </div>
          </el-tab-pane>

          <!-- 性能分析 -->
          <el-tab-pane label="📈 性能分析" name="analysis">
            <div class="analysis-container">
              <!-- T11 ECharts 雷达图 -->
              <el-card class="radar-card">
                <template #header>
                  <span>能力雷达图</span>
                  <span v-if="abilityRadarData" class="radar-meta">
                    平均 {{ abilityRadarData.avg_score }}分 |
                    最强：{{ abilityRadarData.highest_dimension }} |
                    最弱：{{ abilityRadarData.lowest_dimension }}
                  </span>
                </template>
                <div ref="radarChartRef" class="radar-echarts" />
              </el-card>

              <!-- 优劣势 -->
              <div class="analysis-grid">
                <el-card class="strengths-card">
                  <template #header>
                    <span>💪 优势领域</span>
                  </template>
                  <el-tag v-for="s in performanceAnalysis.strengths" :key="s" type="success" class="analysis-tag">{{ s }}</el-tag>
                </el-card>
                <el-card class="weaknesses-card">
                  <template #header>
                    <span>📚 待提升领域</span>
                  </template>
                  <el-tag v-for="w in performanceAnalysis.weaknesses" :key="w" type="warning" class="analysis-tag">{{ w }}</el-tag>
                </el-card>
              </div>

              <!-- 改进建议 -->
              <el-card class="suggestions-card">
                <template #header>
                  <span>💡 个性化建议</span>
                </template>
                <el-steps direction="vertical" :space="60">
                  <el-step v-for="(rec, idx) in performanceAnalysis.studyRecommendations" :key="idx" :title="`建议 ${idx + 1}`" :description="rec" />
                </el-steps>
              </el-card>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <!-- 统计对话框 -->
    <el-dialog v-model="showStatsDialog" title="学习统计" width="600px">
      <div class="stats-dialog">
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="stat-card">
              <div class="stat-icon">⏱️</div>
              <div class="stat-info">
                <div class="stat-value">{{ learningStats.totalStudyTime }}</div>
                <div class="stat-label">总学习时长</div>
              </div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="stat-card">
              <div class="stat-icon">📅</div>
              <div class="stat-info">
                <div class="stat-value">{{ learningStats.weeklyStudyTime }}</div>
                <div class="stat-label">本周学习</div>
              </div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="stat-card">
              <div class="stat-icon">🔥</div>
              <div class="stat-info">
                <div class="stat-value">{{ learningStats.currentStreak }}天</div>
                <div class="stat-label">当前连续</div>
              </div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="stat-card">
              <div class="stat-icon">🏆</div>
              <div class="stat-info">
                <div class="stat-value">{{ learningStats.longestStreak }}天</div>
                <div class="stat-label">最长连续</div>
              </div>
            </div>
          </el-col>
        </el-row>
        <div class="stats-chart">
          <div class="chart-placeholder">学习时长趋势图</div>
        </div>
      </div>
    </el-dialog>

    <!-- 目标对话框 -->
    <el-dialog v-model="showGoalsDialog" title="学习目标" width="500px">
      <div class="goals-dialog">
        <el-button type="primary" class="add-goal-btn" @click="showAddGoal = true">+ 添加目标</el-button>
        <el-list>
          <el-list-item v-for="goal in learningGoals" :key="goal.id">
            <div class="goal-item">
              <div class="goal-header">
                <span class="goal-title">{{ goal.title }}</span>
                <el-tag v-if="goal.status === 'achieved'" type="success" size="small">已达成</el-tag>
                <el-tag v-else-if="goal.status === 'active'" type="primary" size="small">进行中</el-tag>
              </div>
              <p class="goal-desc">{{ goal.description }}</p>
              <div class="goal-progress">
                <span>进度 {{ goal.progress }}%</span>
                <el-progress :percentage="goal.progress" :show-text="true" />
              </div>
              <div class="goal-meta">目标日期: {{ formatDate(goal.targetDate) }}</div>
            </div>
          </el-list-item>
        </el-list>
      </div>
    </el-dialog>

    <!-- 反馈对话框 -->
    <el-dialog v-model="showFeedbackDialog" title="评价回复" width="400px">
      <el-form>
        <el-form-item label="评分">
          <el-rate v-model="feedbackRating" />
        </el-form-item>
        <el-form-item label="反馈">
          <el-input v-model="feedbackComment" type="textarea" :rows="3" placeholder="可选：提供改进建议" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFeedbackDialog = false">取消</el-button>
        <el-button type="primary" @click="submitFeedback">提交</el-button>
      </template>
    </el-dialog>

    <!-- 添加目标对话框 -->
    <el-dialog v-model="showAddGoal" title="添加学习目标" width="500px">
      <el-form :model="newGoal" label-width="100px">
        <el-form-item label="目标名称">
          <el-input v-model="newGoal.title" placeholder="例如：掌握二次函数" />
        </el-form-item>
        <el-form-item label="目标描述">
          <el-input v-model="newGoal.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="目标日期">
          <el-date-picker v-model="newGoal.targetDate" type="date" placeholder="选择日期" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddGoal = false">取消</el-button>
        <el-button type="primary" @click="createGoal">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'
import type { LearningMessage, LearningSession, LearningPlan, LearningStats, LearningGoal, AIRecommendation, KnowledgeMastery, PerformanceAnalysis } from '@/api/ai/learning'
import learningAgentAPI from '@/api/ai/learning'
import { getAbilityRadar, type AbilityRadarData, type AbilityProfile } from '@/api/ai/diagnosis'
import { useUserStore } from '@/stores/user'
import LearningPath from './LearningPath.vue'

const userStore = useUserStore()

// 学生ID（取自登录用户）
const currentStudentId = computed(() => {
  const id = userStore.userInfo?.id
  return id || 'STU001'
})

// 状态
const activeTab = ref('chat')
const selectedSubject = ref<number | undefined>(undefined)
const isTyping = ref(false)
const showStatsDialog = ref(false)
const showGoalsDialog = ref(false)
const showFeedbackDialog = ref(false)
const showAddGoal = ref(false)
const showFileUpload = ref(false)
const showQuickActions = ref(false)

// 输入
const inputMessage = ref('')
const feedbackRating = ref(5)
const feedbackComment = ref('')
const feedbackMessageId = ref('')

// 新目标
const newGoal = reactive({
  title: '',
  description: '',
  targetDate: new Date()
})

// 科目列表
const subjects = [
  { id: 1, name: '数学' },
  { id: 2, name: '语文' },
  { id: 3, name: '英语' },
  { id: 4, name: '物理' },
  { id: 5, name: '化学' }
]

// 会话
const currentSession = ref<LearningSession | null>(null)
const messages = ref<LearningMessage[]>([])
const suggestions = ref<string[]>([])
const messageListRef = ref<HTMLElement>()

// 今日统计
const todayStats = reactive({
  studyTime: '2h30m',
  exercises: 12,
  accuracy: 85,
  streak: 7
})

// 推荐
const recommendations = ref<AIRecommendation[]>([])

// 知识掌握度
const knowledgeMastery = ref<KnowledgeMastery[]>([])

// 学习计划
const learningPlan = ref<LearningPlan | null>(null)
const completedTasks = ref<string[]>([])

// 学习统计
const learningStats = reactive<LearningStats>({
  totalStudyTime: '45h',
  weeklyStudyTime: '8h',
  dailyAverage: '1.2h',
  currentStreak: 7,
  longestStreak: 14,
  sessionsCompleted: 28,
  topicsLearned: 15,
  exercisesCompleted: 120,
  accuracyRate: 82,
  engagementScore: 88
})

// 性能分析
const performanceAnalysis = reactive<PerformanceAnalysis>({
  strengths: ['计算能力', '逻辑思维', '概念理解'],
  weaknesses: ['应用题', '证明题'],
  improvementAreas: [],
  studyRecommendations: [
    '建议每天花30分钟练习应用题',
    '加强证明题的步骤训练',
    '保持现有优势领域的学习节奏'
  ],
  predictedScores: {}
})

// T11：能力雷达图
const radarChartRef = ref<HTMLElement>()
let radarChart: ECharts | null = null
const abilityRadarData = ref<AbilityRadarData | null>(null)
const abilityProfileData = ref<AbilityProfile | null>(null)

// 学习目标
const learningGoals = ref<LearningGoal[]>([])

// 计算属性
const statusClass = computed(() => {
  return currentSession.value?.status === 'active' ? 'online' : 'offline'
})

const statusText = computed(() => {
  return currentSession.value?.status === 'active' ? '在线' : '离线'
})

// 初始化
onMounted(async () => {
  await startSession()
  await loadRecommendations()
  await loadKnowledgeMastery()
  await loadLearningStats()
  await loadLearningGoals()
  await loadAbilityData()  // T11：加载能力雷达图数据
  window.addEventListener('resize', handleResize)
})

// 清理
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  radarChart?.dispose()
  radarChart = null
})

// 开始会话
const startSession = async () => {
  try {
    const session = await learningAgentAPI.startSession({
      studentId: currentStudentId.value,
      subjectId: selectedSubject.value,
      difficulty: 'medium'
    })
    currentSession.value = session
    messages.value = session.messages || []
  } catch {
    // 模拟数据
    currentSession.value = {
      id: 'session-001',
      studentId: currentStudentId.value,
      status: 'active',
      startTime: new Date(),
      messages: [],
      context: {}
    }
  }
}

// 加载推荐
const loadRecommendations = async () => {
  try {
    const recs = await learningAgentAPI.getRecommendations(currentStudentId.value as string, 5)
    recommendations.value = recs
  } catch {
    // 模拟数据
    recommendations.value = [
      {
        id: '1',
        type: 'practice',
        title: '二次函数专项练习',
        description: '针对你的薄弱环节',
        reason: '最近正确率有所下降',
        priority: 1,
        estimatedMinutes: 20,
        confidence: 0.85
      },
      {
        id: '2',
        type: 'review',
        title: '复习上周知识点',
        description: '根据遗忘曲线安排',
        reason: '临近遗忘高峰期',
        priority: 2,
        estimatedMinutes: 15,
        confidence: 0.92
      }
    ]
  }
}

// 加载知识掌握度
const loadKnowledgeMastery = async () => {
  try {
    const mastery = await learningAgentAPI.getKnowledgeMastery(currentStudentId.value as string, selectedSubject.value)
    knowledgeMastery.value = mastery
  } catch {
    // 模拟数据
    knowledgeMastery.value = [
      { nodeId: '1', nodeName: '代数基础', mastery: 85, trend: 'up' },
      { nodeId: '2', nodeName: '函数概念', mastery: 72, trend: 'stable' },
      { nodeId: '3', nodeName: '几何证明', mastery: 58, trend: 'down' },
      { nodeId: '4', nodeName: '应用题', mastery: 45, trend: 'down' }
    ]
  }
}

// 加载学习统计
const loadLearningStats = async () => {
  try {
    const stats = await learningAgentAPI.getLearningStats(currentStudentId.value as string)
    Object.assign(learningStats, stats)
  } catch {
    // 使用模拟数据
  }
}

// 加载学习目标
const loadLearningGoals = async () => {
  try {
    const goals = await learningAgentAPI.getLearningGoals(currentStudentId.value as string)
    learningGoals.value = goals
  } catch {
    // 模拟数据
    learningGoals.value = [
      {
        id: '1',
        studentId: currentStudentId.value as string,
        title: '掌握二次函数',
        description: '能够熟练解决二次函数相关问题',
        targetDate: new Date('2026-05-01'),
        progress: 65,
        status: 'active',
        milestones: []
      }
    ]
  }
}

// T11：加载能力雷达图 & 画像数据
const loadAbilityData = async () => {
  try {
    // 加载雷达图数据
    const radarRes = await getAbilityRadar(currentStudentId.value as string)
    const radar = radarRes?.data ?? null
    abilityRadarData.value = radar
    if (radar) {
      performanceAnalysis.strengths = (radar.indicators || [])
        .filter((i: any) => i.value >= 75)
        .map((i: any) => i.name)
      performanceAnalysis.weaknesses = (radar.indicators || [])
        .filter((i: any) => i.value < 65)
        .map((i: any) => i.name)
    }

    // 加载能力画像
    try {
      const profileRes = await learningAgentAPI.getAbilityProfile(currentStudentId.value as string)
      const profile = (profileRes as any).data?.data || (profileRes as any).data || null
      abilityProfileData.value = profile
      if (profile?.improvement_suggestions?.length) {
        performanceAnalysis.studyRecommendations = profile.improvement_suggestions.slice(0, 5)
      }
    } catch(e) { /* AI 未配置，使用默认 */ 
      console.error(e)
    }

    // 渲染雷达图
    nextTick(() => renderRadarChart())
  } catch(e) { /* API 不可用，使用默认 */ 
    console.error(e)
  }
}

// T11：渲染 ECharts 雷达图
const renderRadarChart = () => {
  // NEXT DEBUG line should be removed.
  if (abilityRadarData.value) return
  if (!radarChartRef.value || !abilityRadarData.value) return
  if (!radarChart) radarChart = echarts.init(radarChartRef.value)
  const indicators = abilityRadarData.value.indicators || []
  radarChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(50,50,50,0.9)',
      borderColor: '#333',
      textStyle: { color: '#fff' }
    },
    radar: {
      indicator: indicators.map(i => ({ name: i.name, max: 100 })),
      shape: 'polygon',
      splitNumber: 4,
      axisName: { color: '#606266', fontSize: 12 },
      splitLine: { lineStyle: { color: '#e4e7ed' } },
      splitArea: { areaStyle: { color: ['#fafafa', '#f4f4f5'] } },
      axisLine: { lineStyle: { color: '#dcdfe6' } }
    },
    series: [{
      type: 'radar',
      data: [{
        value: indicators.map(i => i.value),
        name: '能力得分',
        areaStyle: { color: 'rgba(64,158,255,0.25)' },
        lineStyle: { color: '#409eff', width: 2 },
        itemStyle: { color: '#409eff' }
      }]
    }]
  })
}

// 窗口调整时重绘雷达图
const handleResize = () => { radarChart?.resize() }

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim()) return

  const userMessage: LearningMessage = {
    id: 'msg-' + Date.now(),
    role: 'user',
    content: inputMessage.value,
    timestamp: new Date()
  }
  messages.value.push(userMessage)
  const content = inputMessage.value
  inputMessage.value = ''

  await scrollToBottom()
  isTyping.value = true

  // 模拟AI回复
  setTimeout(async () => {
    const aiResponse = generateAIResponse(content)
    messages.value.push(aiResponse)
    suggestions.value = aiResponse.suggestions || []
    isTyping.value = false
    await scrollToBottom()
  }, 1500)
}

// 发送建议
const sendSuggestion = async (text: string) => {
  inputMessage.value = text
  await sendMessage()
}

// 发送快捷操作
const sendQuickAction = async (action: string) => {
  showQuickActions.value = false
  await sendSuggestion(action)
}

// 生成AI响应
const generateAIResponse = (question: string): LearningMessage => {
  const responses: Record<string, { content: string; suggestions: string[] }> = {
    '解释这个概念': {
      content: '好的，让我为你详细解释这个概念。\n\n**核心要点：**\n1. 理解基本定义\n2. 掌握关键特征\n3. 学会实际应用\n\n需要我举例说明吗？',
      suggestions: ['举个例题', '做练习题', '总结要点']
    },
    '出几道练习题': {
      content: '好的，为你准备了几道练习题：\n\n**基础题：**\n1. 计算下列各式...\n2. 判断下列说法...\n\n**提高题：**\n3. 应用题...\n\n需要答案解析吗？',
      suggestions: ['查看答案', '详细解析', '下一组题目']
    },
    '总结本周学习内容': {
      content: '本周学习总结：\n\n**已完成：**\n- 第一章 基础概念\n- 第二章 核心定理\n\n**重点回顾：**\n- 定理1的应用\n- 常见题型解法\n\n**下周计划：**\n- 继续深入第三章\n\n继续保持！💪',
      suggestions: ['详细查看', '导出笔记', '制定下周计划']
    },
    '给我一些学习建议': {
      content: '根据你的学习数据，我有以下建议：\n\n**📈 优势：**\n- 计算能力强\n- 课堂参与积极\n\n**📚 建议改进：**\n- 加强应用题训练\n- 定期复习巩固\n\n**💡 行动建议：**\n1. 每天做3道应用题\n2. 周末复习本周知识点',
      suggestions: ['制定计划', '开始练习', '查看详情']
    }
  }

  return {
    id: 'msg-' + Date.now(),
    role: 'assistant',
    content: responses[question]?.content || '好的，我来帮你分析这个问题。\n\n首先，让我了解一下你的具体情况...',
    timestamp: new Date(),
    suggestions: responses[question]?.suggestions || ['继续提问', '换个话题', '查看更多']
  }
}

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

// 格式化消息
const formatMessage = (content: string) => {
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
    .replace(/^- /g, '• ')
}

// 格式化时间
const formatTime = (date: Date | string) => {
  const d = new Date(date)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 格式化日期
const formatDate = (date: Date | string) => {
  const d = new Date(date)
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

// 获取推荐图标
const getRecIcon = (type: string) => {
  const icons: Record<string, string> = {
    content: '📖',
    practice: '✏️',
    review: '🔄',
    break: '☕'
  }
  return icons[type] || '📌'
}

// 获取趋势图标
const getTrendIcon = (trend: string) => {
  const icons: Record<string, string> = {
    up: '📈',
    down: '📉',
    stable: '➡️'
  }
  return icons[trend] || '➡️'
}

// 获取掌握度颜色
const getMasteryColor = (percentage: number) => {
  if (percentage >= 80) return '#67C23A'
  if (percentage >= 60) return '#409EFF'
  if (percentage >= 40) return '#E6A23C'
  return '#F56C6C'
}

// 科目变化
const onSubjectChange = async () => {
  await startSession()
  await loadRecommendations()
  await loadKnowledgeMastery()
}

// 处理推荐点击
const handleRecommendation = (rec: AIRecommendation) => {
  activeTab.value = 'chat'
  inputMessage.value = `我想学习：${rec.title}`
  ElMessage.info(`已选择：${rec.title}`)
}

// 评价消息
const showFeedbackDialogFn = (messageId: string) => {
  feedbackMessageId.value = messageId
  feedbackRating.value = 5
  feedbackComment.value = ''
  showFeedbackDialog.value = true
}

// 提交反馈
const submitFeedback = async () => {
  try {
    await learningAgentAPI.rateMessage(feedbackMessageId.value, feedbackRating.value, feedbackComment.value)
    ElMessage.success('反馈已提交，感谢你的评价！')
    showFeedbackDialog.value = false
  } catch {
    ElMessage.error('提交失败，请重试')
  }
}

// 复制消息
const copyMessage = (content: string) => {
  navigator.clipboard.writeText(content)
  ElMessage.success('已复制到剪贴板')
}

// 生成学习计划
const generatePlan = async () => {
  if (!selectedSubject.value) {
    ElMessage.warning('请先选择科目')
    return
  }
  try {
    const plan = await learningAgentAPI.generateLearningPlan({
      studentId: currentStudentId,
      subjectId: selectedSubject.value,
      targetHours: 20,
      targetDate: new Date('2026-06-01')
    })
    learningPlan.value = plan
    ElMessage.success('学习计划已生成')
  } catch {
    ElMessage.error('生成失败，请重试')
  }
}

// 创建目标
const createGoal = async () => {
  try {
    const goal = await learningAgentAPI.createLearningGoal({
      studentId: currentStudentId,
      title: newGoal.title,
      description: newGoal.description,
      targetDate: newGoal.targetDate,
      progress: 0,
      status: 'active',
      milestones: []
    })
    learningGoals.value.push(goal)
    showAddGoal.value = false
    ElMessage.success('目标创建成功')
    Object.assign(newGoal, { title: '', description: '', targetDate: new Date() })
  } catch {
    ElMessage.error('创建失败，请重试')
  }
}
</script>

<style scoped lang="scss">
.learning-agent {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.agent-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;

  h2 {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
  }
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;

  &.online {
    background: #e7f7e7;
    color: #67c23a;
  }

  &.offline {
    background: #f4f4f5;
    color: #909399;
  }
}

.header-actions {
  display: flex;
  gap: 12px;
}

.agent-content {
  flex: 1;
  display: flex;
  gap: 16px;
  padding: 16px;
  overflow: hidden;
}

.sidebar {
  width: 300px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.overview-card,
.recommendations-card,
.mastery-card {
  flex-shrink: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 8px;

  .stat-value {
    font-size: 18px;
    font-weight: 600;
    color: #303133;
  }

  .stat-label {
    font-size: 12px;
    color: #909399;
  }
}

.recommendation-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recommendation-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    background: #ecf5ff;
    transform: translateX(4px);
  }

  .rec-icon {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: white;
    border-radius: 8px;
    font-size: 20px;
  }

  .rec-content {
    flex: 1;
    min-width: 0;

    .rec-title {
      font-weight: 600;
      font-size: 14px;
      color: #303133;
    }

    .rec-desc {
      font-size: 12px;
      color: #909399;
      margin: 4px 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .rec-meta {
      display: flex;
      gap: 8px;
      font-size: 11px;
      color: #c0c4cc;

      .rec-confidence {
        color: #67c23a;
      }
    }
  }
}

.mastery-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mastery-item {
  .mastery-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 4px;

    .mastery-name {
      font-size: 13px;
      color: #606266;
    }

    .mastery-trend {
      font-size: 12px;
    }
  }
}

.main-area {
  flex: 1;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.main-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;

  :deep(.el-tabs__header) {
    margin: 0;
  }

  :deep(.el-tabs__content) {
    flex: 1;
    overflow: hidden;
    padding: 0;
  }
}

.learning-path-container {
  height: 100%;
  min-height: 400px;
}

.chat-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  gap: 12px;

  &.user {
    flex-direction: row-reverse;

    .message-content {
      align-items: flex-end;
    }

    .message-bubble {
      background: #409eff;
      color: white;
    }
  }

  &.assistant {
    .message-bubble {
      background: #f4f4f5;
      color: #303133;
    }
  }
}

.message-avatar {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ecf5ff;
  border-radius: 50%;
  font-size: 18px;
  flex-shrink: 0;
}

.message-content {
  display: flex;
  flex-direction: column;
  max-width: 70%;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.message-time {
  font-size: 11px;
  color: #c0c4cc;
  margin-top: 4px;
}

.message-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
  opacity: 0;
  transition: opacity 0.3s;

  .message:hover & {
    opacity: 1;
  }
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;

  span {
    width: 8px;
    height: 8px;
    background: #c0c4cc;
    border-radius: 50%;
    animation: typing 1.4s infinite;

    &:nth-child(2) {
      animation-delay: 0.2s;
    }

    &:nth-child(3) {
      animation-delay: 0.4s;
    }
  }
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-4px);
  }
}

.suggestions {
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;

  .suggestions-label {
    font-size: 12px;
    color: #909399;
  }

  .suggestion-tag {
    cursor: pointer;
  }
}

.input-area {
  padding: 16px;
  border-top: 1px solid #e4e7ed;
  background: #fafafa;
}

.input-tools {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  position: relative;
}

.quick-actions {
  position: absolute;
  top: 100%;
  left: 0;
  background: white;
  padding: 8px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  gap: 8px;
  z-index: 10;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;

  .input-hint {
    font-size: 12px;
    color: #c0c4cc;
  }
}

.plan-container,
.analysis-container {
  padding: 16px;
  overflow-y: auto;
  height: 100%;
}

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;

  h3 {
    margin: 0;
  }
}

.milestone-card {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;

  &.completed {
    background: #f0f9eb;
  }

  .milestone-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    h4 {
      margin: 0;
    }
  }

  p {
    margin: 8px 0;
    color: #606266;
  }

  .milestone-meta {
    display: flex;
    gap: 16px;
    font-size: 12px;
    color: #909399;
    margin-bottom: 8px;
  }

  .milestone-progress {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: #606266;
  }
}

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin: 16px 0;
}

.analysis-tag {
  margin: 4px;
}

.stats-dialog {
  .stat-card {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px;
    background: #f5f7fa;
    border-radius: 8px;
    margin-bottom: 12px;

    .stat-icon {
      font-size: 32px;
    }

    .stat-info {
      .stat-value {
        font-size: 24px;
        font-weight: 600;
        color: #303133;
      }

      .stat-label {
        font-size: 12px;
        color: #909399;
      }
    }
  }
}

.goal-item {
  width: 100%;

  .goal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .goal-title {
      font-weight: 600;
    }
  }

  .goal-desc {
    color: #909399;
    font-size: 13px;
    margin: 8px 0;
  }

  .goal-progress {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: #606266;
    margin: 8px 0;
  }

  .goal-meta {
    font-size: 12px;
    color: #c0c4cc;
  }
}

.radar-echarts {
  width: 100%;
  height: 320px;
}

.radar-meta {
  font-size: 12px;
  color: #909399;
  font-weight: normal;
  margin-left: 12px;
}
</style>
