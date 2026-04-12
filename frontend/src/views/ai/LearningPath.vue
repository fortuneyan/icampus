<template>
  <div class="learning-path">
    <!-- 头部信息 -->
    <div class="path-header">
      <div class="path-info">
        <h3>🛤️ {{ pathData?.subjectName || '学习路径' }}</h3>
        <div class="path-stats">
          <span class="stat">
            <span class="stat-icon">📚</span>
            {{ completedNodes.length }}/{{ pathData?.totalNodes || 0 }} 已完成
          </span>
          <span class="stat">
            <span class="stat-icon">⏱️</span>
            预计 {{ formatDuration(pathData?.estimatedDuration || 0) }}
          </span>
          <span class="stat">
            <span class="stat-icon">📍</span>
            当前: {{ currentNodeTitle }}
          </span>
          <span class="stat progress-stat">
            <span class="stat-icon">📊</span>
            完成度 {{ completionRate }}%
          </span>
        </div>
      </div>
      <div class="path-actions">
        <el-button @click="regeneratePath" :loading="isGenerating">🔄 重新生成路径</el-button>
        <el-button type="primary" @click="startLearning">▶️ 开始学习</el-button>
      </div>
    </div>

    <!-- 视图切换 -->
    <div class="view-toggle">
      <el-radio-group v-model="viewMode" size="small">
        <el-radio-button label="graph">图谱视图</el-radio-button>
        <el-radio-button label="list">列表视图</el-radio-button>
        <el-radio-button label="stats">统计视图</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 路径图谱视图 (ECharts) -->
    <div v-show="viewMode === 'graph'" class="path-visualization">
      <div class="chart-container" ref="chartContainerRef"></div>
    </div>

    <!-- 节点列表视图 -->
    <div v-show="viewMode === 'list'" class="path-list-view">
      <div class="timeline">
        <div v-for="(node, index) in sortedNodes" :key="node.id" class="timeline-item" :class="node.status">
          <div class="timeline-marker">
            <span class="timeline-number">{{ index + 1 }}</span>
            <span class="timeline-line" v-if="index < sortedNodes.length - 1"></span>
          </div>
          <el-card class="timeline-card" @click="selectNode(node)">
            <div class="timeline-card-header">
              <span class="node-icon">{{ getNodeIcon(node.type) }}</span>
              <span class="node-title">{{ node.title }}</span>
              <el-tag :type="getStatusType(node.status)" size="small">{{ getStatusText(node.status) }}</el-tag>
            </div>
            <div class="timeline-card-meta">
              <span><el-icon><Clock /></el-icon> {{ node.duration }}分钟</span>
              <span><el-icon><Star /></el-icon> 难度 {{ getDifficultyText(node.difficulty) }}</span>
              <span v-if="node.prerequisites.length"><el-icon><Connection /></el-icon> 前置: {{ node.prerequisites.length }}个</span>
            </div>
            <div class="timeline-card-desc">{{ node.description }}</div>
          </el-card>
        </div>
      </div>
    </div>

    <!-- 统计视图 -->
    <div v-show="viewMode === 'stats'" class="path-stats-view">
      <el-row :gutter="16">
        <el-col :span="12">
          <el-card class="stats-card">
            <template #header>
              <div class="card-header">
                <span>📈 学习进度</span>
              </div>
            </template>
            <div ref="progressChartRef" class="chart-wrapper"></div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card class="stats-card">
            <template #header>
              <div class="card-header">
                <span>🎯 节点分布</span>
              </div>
            </template>
            <div ref="pieChartRef" class="chart-wrapper"></div>
          </el-card>
        </el-col>
      </el-row>
      <el-row :gutter="16" style="margin-top: 16px;">
        <el-col :span="24">
          <el-card class="stats-card">
            <template #header>
              <div class="card-header">
                <span>📊 学习时长分布</span>
              </div>
            </template>
            <div ref="barChartRef" class="chart-wrapper bar-chart"></div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 原有 SVG 视图（保留作为备选） -->
    <div v-show="viewMode === 'svg'" class="path-visualization">
      <div class="path-container" ref="pathContainerRef">
        <svg class="path-svg" :viewBox="`0 0 ${svgWidth} ${svgHeight}`">
          <g class="edges">
            <path v-for="edge in pathData?.edges" :key="edge.id" :d="getEdgePath(edge)" class="path-edge" :class="edge.type" />
          </g>
          <g class="nodes">
            <g v-for="node in pathData?.nodes" :key="node.id" :transform="`translate(${node.position.x}, ${node.position.y})`" class="node-group" :class="node.status" @click="selectNode(node)">
              <circle v-if="node.type === 'milestone'" r="30" class="node-shape milestone" />
              <rect v-else x="-40" y="-25" width="80" height="50" rx="8" class="node-shape" />
              <text class="node-icon" text-anchor="middle" dy="-5" y="0">{{ getNodeIcon(node.type) }}</text>
              <text class="node-title" text-anchor="middle" y="40" x="0">{{ truncateTitle(node.title) }}</text>
              <circle v-if="node.status === 'in_progress'" r="8" cx="30" cy="-20" class="status-indicator pulse" />
              <circle v-if="node.status === 'completed'" r="8" cx="30" cy="-20" class="status-indicator completed" />
              <circle v-if="node.status === 'locked'" r="8" cx="30" cy="-20" class="status-indicator locked" />
              <text v-if="node.status === 'locked'" x="0" y="5" text-anchor="middle" font-size="14">🔒</text>
            </g>
          </g>
        </svg>
      </div>
    </div>

    <!-- 节点详情 -->
    <div v-if="selectedNode" class="node-detail">
      <div class="detail-header">
        <div class="detail-title">
          <span class="detail-icon">{{ getNodeIcon(selectedNode.type) }}</span>
          <h4>{{ selectedNode.title }}</h4>
          <el-tag :type="getStatusType(selectedNode.status)" size="small">{{ getStatusText(selectedNode.status) }}</el-tag>
        </div>
        <el-button text @click="selectedNode = null">✕</el-button>
      </div>

      <div class="detail-content">
        <p class="detail-desc">{{ selectedNode.description }}</p>

        <div class="detail-meta">
          <div class="meta-item">
            <span class="meta-label">难度</span>
            <el-tag :type="getDifficultyType(selectedNode.difficulty)" size="small">{{ selectedNode.difficulty }}</el-tag>
          </div>
          <div class="meta-item">
            <span class="meta-label">预计时长</span>
            <span>{{ selectedNode.duration }}分钟</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">前置知识</span>
            <span>{{ selectedNode.prerequisites.length ? selectedNode.prerequisites.join(', ') : '无' }}</span>
          </div>
        </div>

        <div v-if="selectedNode.content" class="detail-content-preview">
          <h5>内容预览</h5>
          <div class="content-body" v-html="formatContent(selectedNode.content)"></div>
        </div>

        <div class="detail-actions">
          <el-button v-if="selectedNode.status === 'available' || selectedNode.status === 'in_progress'" type="primary" @click="startNode(selectedNode)">
            {{ selectedNode.status === 'in_progress' ? '继续学习' : '开始学习' }}
          </el-button>
          <el-button v-if="selectedNode.status === 'completed'" @click="reviewNode(selectedNode)">复习</el-button>
          <el-button v-if="selectedNode.status === 'locked'" disabled>需要先完成前置内容</el-button>
        </div>
      </div>
    </div>

    <!-- 节点列表（备用视图） -->
    <div v-else class="node-list">
      <el-card v-for="node in sortedNodes" :key="node.id" class="node-card" :class="node.status" @click="selectNode(node)">
        <div class="node-card-header">
          <span class="node-icon">{{ getNodeIcon(node.type) }}</span>
          <span class="node-title">{{ node.title }}</span>
          <el-tag :type="getStatusType(node.status)" size="small">{{ getStatusText(node.status) }}</el-tag>
        </div>
        <div class="node-card-meta">
          <span>难度: {{ node.difficulty }}</span>
          <span>时长: {{ node.duration }}分钟</span>
        </div>
      </el-card>
    </div>

    <!-- 学习弹窗 -->
    <el-dialog v-model="showLearningDialog" :title="learningNode?.title" width="800px" class="learning-dialog">
      <div class="learning-content">
        <div class="learning-progress">
          <span>进度 {{ learningProgress }}%</span>
          <el-progress :percentage="learningProgress" :show-text="false" />
        </div>

        <div class="learning-body" v-if="learningNode">
          <div v-html="formatContent(learningNode.content || '暂无内容')"></div>
        </div>

        <div class="learning-actions">
          <el-button @click="completeNode">标记完成</el-button>
          <el-button type="primary" @click="showPracticeDialog = true">开始练习</el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 练习弹窗 -->
    <el-dialog v-model="showPracticeDialog" title="随堂练习" width="600px">
      <div class="practice-content">
        <div v-for="(question, idx) in practiceQuestions" :key="idx" class="practice-question">
          <h5>题目 {{ idx + 1 }}</h5>
          <p>{{ question.text }}</p>
          <el-radio-group v-model="question.answer">
            <el-radio v-for="(opt, oIdx) in question.options" :key="oIdx" :label="oIdx">{{ opt }}</el-radio>
          </el-radio-group>
        </div>
      </div>
      <template #footer>
        <el-button @click="showPracticeDialog = false">取消</el-button>
        <el-button type="primary" @click="submitPractice">提交答案</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { Clock, Star, Connection } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import type { LearningPath, PathNode, PathEdge } from '@/api/ai/learning'
import learningAgentAPI from '@/api/ai/learning'

const props = defineProps<{
  studentId: string
  subjectId?: number
}>()

// 状态
const pathData = ref<LearningPath | null>(null)
const selectedNode = ref<PathNode | null>(null)
const isGenerating = ref(false)
const showLearningDialog = ref(false)
const showPracticeDialog = ref(false)
const learningNode = ref<PathNode | null>(null)
const learningProgress = ref(0)
const viewMode = ref<'graph' | 'list' | 'stats' | 'svg'>('graph')

// Chart refs
const chartContainerRef = ref<HTMLElement>()
const progressChartRef = ref<HTMLElement>()
const pieChartRef = ref<HTMLElement>()
const barChartRef = ref<HTMLElement>()
const pathContainerRef = ref<HTMLElement>()

let chartInstance: echarts.ECharts | null = null
let progressChart: echarts.ECharts | null = null
let pieChart: echarts.ECharts | null = null
let barChart: echarts.ECharts | null = null

// SVG尺寸
const svgWidth = 900
const svgHeight = 500

// 模拟练习题
const practiceQuestions = ref([
  {
    text: '二次函数y=ax²+bx+c的顶点坐标公式是什么？',
    options: ['(-b/2a, 4ac-b²/4a)', '(b/2a, 4ac-b²/4a)', '(-b/a, c/a)', '(b/a, c/a)'],
    answer: undefined
  },
  {
    text: '已知二次函数开口向上，则a的取值范围是？',
    options: ['a > 0', 'a < 0', 'a = 0', 'a ≠ 0'],
    answer: undefined
  }
])

// 计算属性
const completedNodes = computed(() => {
  return pathData.value?.nodes.filter(n => n.status === 'completed') || []
})

const currentNodeTitle = computed(() => {
  const current = pathData.value?.nodes.find(n => n.id === pathData.value?.currentNodeId)
  return current?.title || '无'
})

const completionRate = computed(() => {
  if (!pathData.value?.totalNodes) return 0
  return Math.round((completedNodes.value.length / pathData.value.totalNodes) * 100)
})

const sortedNodes = computed(() => {
  return [...(pathData.value?.nodes || [])].sort((a, b) => {
    const order = ['concept', 'lesson', 'exercise', 'quiz', 'milestone']
    return order.indexOf(a.type) - order.indexOf(b.type)
  })
})

// 初始化
onMounted(async () => {
  await loadLearningPath()
  await nextTick()
  initChart()
})

watch(() => props.subjectId, async () => {
  await loadLearningPath()
  await nextTick()
  if (viewMode.value === 'graph') {
    updateChart()
  }
})

watch(viewMode, async (newMode) => {
  await nextTick()
  if (newMode === 'graph') {
    initChart()
  } else if (newMode === 'stats') {
    initStatsCharts()
  }
})

onBeforeUnmount(() => {
  chartInstance?.dispose()
  progressChart?.dispose()
  pieChart?.dispose()
  barChart?.dispose()
})

// 加载学习路径
const loadLearningPath = async () => {
  try {
    if (props.subjectId) {
      const path = await learningAgentAPI.getLearningPath(props.studentId, props.subjectId)
      pathData.value = path
    } else {
      // 模拟数据
      pathData.value = generateMockPath()
    }
  } catch {
    pathData.value = generateMockPath()
  }
}

// 初始化 ECharts 图谱
const initChart = () => {
  if (!chartContainerRef.value || !pathData.value) return
  
  chartInstance = echarts.init(chartContainerRef.value)
  updateChart()
}

// 更新图谱
const updateChart = () => {
  if (!chartInstance || !pathData.value) return
  
  const nodes = pathData.value.nodes.map(node => ({
    name: node.title,
    id: node.id,
    type: node.type,
    status: node.status,
    description: node.description,
    duration: node.duration,
    value: [
      node.position?.x || 0,
      node.position?.y || 0
    ]
  }))
  
  const edges = pathData.value.edges.map(edge => ({
    source: pathData.value!.nodes.find(n => n.id === edge.source)?.title,
    target: pathData.value!.nodes.find(n => n.id === edge.target)?.title
  }))
  
  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        if (params.dataType === 'node') {
          const node = pathData.value?.nodes.find(n => n.title === params.name)
          return `<div style="font-size: 12px;">
            <strong>${params.name}</strong><br/>
            类型: ${getNodeIcon(node?.type || '')} ${node?.type}<br/>
            状态: ${getStatusText(node?.status || '')}<br/>
            时长: ${node?.duration || 0}分钟<br/>
            描述: ${node?.description || ''}
          </div>`
        }
        return params.name
      }
    },
    series: [{
      type: 'graph',
      layout: 'none',
      coordinateSystem: 'cartesian2d',
      symbolSize: 50,
      roam: true,
      label: {
        show: true,
        position: 'bottom',
        fontSize: 11,
        formatter: (params: any) => {
          const name = params.name
          return name.length > 8 ? name.substring(0, 8) + '...' : name
        }
      },
      itemStyle: {
        color: (params: any) => {
          const status = (params.data as any).status
          const colors: Record<string, string> = {
            completed: '#67c23a',
            in_progress: '#409eff',
            available: '#e6a23c',
            locked: '#c0c4cc'
          }
          return colors[status] || '#409eff'
        },
        borderColor: (params: any) => {
          const status = (params.data as any).status
          const colors: Record<string, string> = {
            completed: '#529b2e',
            in_progress: '#337ecc',
            available: '#c08620',
            locked: '#9fa6ad'
          }
          return colors[status] || '#337ecc'
        },
        borderWidth: 2,
        shadowBlur: 10,
        shadowColor: 'rgba(0, 0, 0, 0.2)'
      },
      lineStyle: {
        color: '#409eff',
        width: 2,
        curveness: 0.1
      },
      data: nodes,
      links: edges,
      edgeSymbol: ['circle', 'arrow'],
      edgeSymbolSize: [6, 10]
    }],
    xAxis: {
      show: false,
      min: 0,
      max: svgWidth
    },
    yAxis: {
      show: false,
      min: 0,
      max: svgHeight
    }
  }
  
  chartInstance.setOption(option)
  
  // 点击事件
  chartInstance.on('click', (params: any) => {
    if (params.dataType === 'node') {
      const node = pathData.value?.nodes.find(n => n.title === params.name)
      if (node) {
        selectNode(node)
      }
    }
  })
}

// 初始化统计图表
const initStatsCharts = () => {
  if (!pathData.value) return
  
  // 进度饼图
  if (progressChartRef.value) {
    progressChart = echarts.init(progressChartRef.value)
    const completed = completedNodes.value.length
    const remaining = (pathData.value.totalNodes || 0) - completed
    
    progressChart.setOption({
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}: {c}个 ({d}%)'
        },
        data: [
          { value: completed, name: '已完成', itemStyle: { color: '#67c23a' } },
          { value: remaining, name: '未完成', itemStyle: { color: '#e6a23c' } }
        ]
      }]
    })
  }
  
  // 节点分布饼图
  if (pieChartRef.value) {
    pieChart = echarts.init(pieChartRef.value)
    const typeCount: Record<string, number> = {}
    pathData.value.nodes.forEach(node => {
      typeCount[node.type] = (typeCount[node.type] || 0) + 1
    })
    
    const typeColors: Record<string, string> = {
      concept: '#409eff',
      lesson: '#67c23a',
      exercise: '#e6a23c',
      quiz: '#f56c6c',
      milestone: '#909399'
    }
    
    pieChart.setOption({
      series: [{
        type: 'pie',
        radius: '65%',
        center: ['50%', '50%'],
        data: Object.entries(typeCount).map(([type, count]) => ({
          name: getNodeIcon(type) + ' ' + type,
          value: count,
          itemStyle: { color: typeColors[type] || '#409eff' }
        })),
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    })
  }
  
  // 时长分布柱状图
  if (barChartRef.value) {
    barChart = echarts.init(barChartRef.value)
    const nodeTitles = pathData.value.nodes.map(n => 
      n.title.length > 6 ? n.title.substring(0, 6) + '...' : n.title
    )
    const durations = pathData.value.nodes.map(n => n.duration)
    const statusColors = pathData.value.nodes.map(n => {
      const colors: Record<string, string> = {
        completed: '#67c23a',
        in_progress: '#409eff',
        available: '#e6a23c',
        locked: '#c0c4cc'
      }
      return colors[n.status] || '#409eff'
    })
    
    barChart.setOption({
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: nodeTitles,
        axisLabel: { rotate: 30, fontSize: 10 }
      },
      yAxis: {
        type: 'value',
        name: '分钟'
      },
      series: [{
        type: 'bar',
        data: durations.map((d, i) => ({
          value: d,
          itemStyle: { color: statusColors[i] }
        })),
        barWidth: '50%',
        label: {
          show: true,
          position: 'top',
          formatter: '{c}m'
        }
      }]
    })
  }
}

// 生成模拟路径
const generateMockPath = (): LearningPath => {
  const nodes: PathNode[] = [
    {
      id: 'n1',
      type: 'concept',
      title: '二次函数基础',
      description: '学习二次函数的基本概念、定义域和值域',
      duration: 20,
      difficulty: 'easy',
      status: 'completed',
      position: { x: 100, y: 250 },
      prerequisites: []
    },
    {
      id: 'n2',
      type: 'lesson',
      title: '顶点公式推导',
      description: '掌握配方法和顶点公式的推导过程',
      duration: 30,
      difficulty: 'medium',
      status: 'completed',
      position: { x: 250, y: 150 },
      prerequisites: ['n1']
    },
    {
      id: 'n3',
      type: 'exercise',
      title: '顶点求解练习',
      description: '通过练习熟练掌握顶点坐标的求法',
      duration: 25,
      difficulty: 'medium',
      status: 'in_progress',
      position: { x: 400, y: 250 },
      prerequisites: ['n2']
    },
    {
      id: 'n4',
      type: 'quiz',
      title: '阶段测验',
      description: '检验前三个知识点的掌握情况',
      duration: 15,
      difficulty: 'hard',
      status: 'available',
      position: { x: 550, y: 150 },
      prerequisites: ['n3']
    },
    {
      id: 'n5',
      type: 'milestone',
      title: '第一阶段完成',
      description: '恭喜完成二次函数基础阶段学习！',
      duration: 0,
      difficulty: 'easy',
      status: 'locked',
      position: { x: 700, y: 250 },
      prerequisites: ['n4']
    },
    {
      id: 'n6',
      type: 'concept',
      title: '图像变换',
      description: '学习二次函数的平移、伸缩、翻折变换',
      duration: 25,
      difficulty: 'medium',
      status: 'locked',
      position: { x: 700, y: 350 },
      prerequisites: ['n5']
    }
  ]

  const edges: PathEdge[] = [
    { id: 'e1', source: 'n1', target: 'n2', type: 'sequence' },
    { id: 'e2', source: 'n2', target: 'n3', type: 'sequence' },
    { id: 'e3', source: 'n3', target: 'n4', type: 'sequence' },
    { id: 'e4', source: 'n4', target: 'n5', type: 'sequence' },
    { id: 'e5', source: 'n5', target: 'n6', type: 'sequence' }
  ]

  return {
    id: 'path-001',
    studentId: props.studentId,
    subjectId: props.subjectId || 1,
    subjectName: '数学 - 二次函数',
    nodes,
    edges,
    currentNodeId: 'n3',
    completedNodes: ['n1', 'n2'],
    totalNodes: 6,
    estimatedDuration: 115
  }
}

// 获取边路径
const getEdgePath = (edge: PathEdge) => {
  const sourceNode = pathData.value?.nodes.find(n => n.id === edge.source)
  const targetNode = pathData.value?.nodes.find(n => n.id === edge.target)

  if (!sourceNode || !targetNode) return ''

  const sx = sourceNode.position.x + 40
  const sy = sourceNode.position.y
  const tx = targetNode.position.x - 40
  const ty = targetNode.position.y

  const midX = (sx + tx) / 2

  return `M ${sx} ${sy} Q ${midX} ${sy} ${midX} ${(sy + ty) / 2} Q ${midX} ${ty} ${tx} ${ty}`
}

// 获取节点图标
const getNodeIcon = (type: string) => {
  const icons: Record<string, string> = {
    concept: '📖',
    lesson: '🎓',
    exercise: '✏️',
    quiz: '📝',
    milestone: '🏆'
  }
  return icons[type] || '📌'
}

// 截断标题
const truncateTitle = (title: string) => {
  return title.length > 8 ? title.substring(0, 8) + '...' : title
}

// 格式化时长
const formatDuration = (minutes: number) => {
  if (minutes < 60) return `${minutes}分钟`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return mins > 0 ? `${hours}小时${mins}分钟` : `${hours}小时`
}

// 格式化内容
const formatContent = (content: string) => {
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
    .replace(/^• /gm, '• ')
}

// 获取状态类型
const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    completed: 'success',
    in_progress: 'primary',
    available: 'warning',
    locked: 'info'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    completed: '已完成',
    in_progress: '进行中',
    available: '可学习',
    locked: '已锁定'
  }
  return texts[status] || status
}

// 获取难度类型
const getDifficultyType = (difficulty: string) => {
  const types: Record<string, string> = {
    easy: 'success',
    medium: 'warning',
    hard: 'danger'
  }
  return types[difficulty] || 'info'
}

// 获取难度文本
const getDifficultyText = (difficulty: string) => {
  const texts: Record<string, string> = {
    easy: '简单',
    medium: '中等',
    hard: '困难'
  }
  return texts[difficulty] || difficulty
}

// 选择节点
const selectNode = (node: PathNode) => {
  selectedNode.value = node
}

// 重新生成路径
const regeneratePath = async () => {
  isGenerating.value = true
  try {
    if (props.subjectId) {
      const path = await learningAgentAPI.generateLearningPath({
        studentId: props.studentId,
        subjectId: props.subjectId,
        currentLevel: 1,
        targetLevel: 3
      })
      pathData.value = path
    } else {
      pathData.value = generateMockPath()
    }
    ElMessage.success('路径已重新生成')
  } catch {
    ElMessage.error('生成失败，请重试')
  } finally {
    isGenerating.value = false
  }
}

// 开始学习
const startLearning = () => {
  const availableNode = pathData.value?.nodes.find(n => n.status === 'available' || n.status === 'in_progress')
  if (availableNode) {
    selectNode(availableNode)
    startNode(availableNode)
  } else {
    ElMessage.info('当前没有可开始的学习内容')
  }
}

// 开始节点
const startNode = async (node: PathNode) => {
  learningNode.value = node
  learningProgress.value = node.status === 'in_progress' ? 50 : 0
  showLearningDialog.value = true

  // 更新节点状态
  if (node.status === 'available') {
    node.status = 'in_progress'
    if (pathData.value?.currentNodeId) {
      pathData.value.currentNodeId = node.id
    }
  }
}

// 复习节点
const reviewNode = (node: PathNode) => {
  learningNode.value = node
  learningProgress.value = 100
  showLearningDialog.value = true
}

// 完成节点
const completeNode = async () => {
  if (!learningNode.value || !pathData.value) return

  try {
    // 更新本地状态
    learningNode.value.status = 'completed'
    if (!pathData.value.completedNodes.includes(learningNode.value.id)) {
      pathData.value.completedNodes.push(learningNode.value.id)
    }

    // 解锁后续节点
    pathData.value.nodes.forEach(node => {
      if (node.prerequisites.includes(learningNode.value!.id)) {
        const allPrereqCompleted = node.prerequisites.every(pid =>
          pathData.value!.completedNodes.includes(pid)
        )
        if (allPrereqCompleted && node.status === 'locked') {
          node.status = 'available'
        }
      }
    })

    // 找到下一个可学习节点
    const nextNode = pathData.value.nodes.find(n => n.status === 'available')
    if (nextNode) {
      pathData.value.currentNodeId = nextNode.id
    }

    ElMessage.success('节点学习完成！')
    showLearningDialog.value = false
    selectedNode.value = null

    // 同步到服务器
    try {
      await learningAgentAPI.updatePathNode(pathData.value.id, learningNode.value.id, 'completed')
    } catch {
      // 忽略同步错误
    }
  } catch {
    ElMessage.error('操作失败，请重试')
  }
}

// 提交练习
const submitPractice = async () => {
  const correctAnswers = [0, 0] // 正确答案索引
  let correct = 0

  practiceQuestions.value.forEach((q, idx) => {
    if (q.answer === correctAnswers[idx]) {
      correct++
    }
  })

  const score = (correct / practiceQuestions.value.length) * 100
  ElMessage.success(`练习完成！得分：${score.toFixed(0)}分`)
  showPracticeDialog.value = false

  if (score >= 60) {
    await completeNode()
  }
}
</script>

<style scoped lang="scss">
.learning-path {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 16px;
  overflow: hidden;
}

.path-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;

  h3 {
    margin: 0 0 8px 0;
    font-size: 18px;
  }
}

.path-stats {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #606266;

  .stat {
    display: flex;
    align-items: center;
    gap: 4px;

    .stat-icon {
      font-size: 14px;
    }

    &.progress-stat {
      color: #409eff;
      font-weight: 600;
    }
  }
}

.path-actions {
  display: flex;
  gap: 8px;
}

.view-toggle {
  margin-bottom: 12px;
}

.path-visualization {
  flex: 1;
  background: #fafafa;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
  min-height: 400px;
}

.chart-container {
  width: 100%;
  height: 100%;
  min-height: 400px;
}

.path-container {
  min-width: 100%;
  min-height: 100%;
}

.path-svg {
  width: 100%;
  height: 100%;
  min-width: 900px;
  min-height: 500px;
}

// 列表视图样式
.path-list-view {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px;
}

.timeline {
  position: relative;
  padding-left: 40px;
  
  .timeline-item {
    position: relative;
    padding-bottom: 16px;
    
    &.completed {
      .timeline-marker {
        background: #e1f3d8;
        border-color: #67c23a;
      }
      .timeline-card {
        background: #f0f9eb;
        border-color: #67c23a;
      }
    }
    
    &.in_progress {
      .timeline-marker {
        background: #ecf5ff;
        border-color: #409eff;
      }
      .timeline-card {
        background: #ecf5ff;
        border-color: #409eff;
      }
    }
    
    &.locked {
      opacity: 0.6;
      .timeline-marker {
        background: #f4f4f5;
        border-color: #909399;
      }
    }
  }
  
  .timeline-marker {
    position: absolute;
    left: 0;
    top: 0;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: white;
    border: 2px solid #409eff;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1;
    
    .timeline-number {
      font-size: 12px;
      font-weight: 600;
      color: #409eff;
    }
    
    .timeline-line {
      position: absolute;
      left: 15px;
      top: 32px;
      width: 2px;
      height: calc(100% + 16px);
      background: #e4e7ed;
    }
  }
  
  .timeline-card {
    margin-left: 16px;
    cursor: pointer;
    transition: all 0.3s;
    
    &:hover {
      transform: translateX(4px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .timeline-card-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
      
      .node-icon {
        font-size: 18px;
      }
      
      .node-title {
        flex: 1;
        font-weight: 600;
      }
    }
    
    .timeline-card-meta {
      display: flex;
      gap: 16px;
      font-size: 12px;
      color: #909399;
      margin-bottom: 8px;
      
      span {
        display: flex;
        align-items: center;
        gap: 4px;
      }
    }
    
    .timeline-card-desc {
      font-size: 13px;
      color: #606266;
      line-height: 1.5;
    }
  }
}

// 统计视图样式
.path-stats-view {
  flex: 1;
  overflow-y: auto;
}

.stats-card {
  .card-header {
    font-weight: 600;
  }
  
  .chart-wrapper {
    height: 250px;
    
    &.bar-chart {
      height: 200px;
    }
  }
}

.path-edge {
  fill: none;
  stroke: #dcdfe6;
  stroke-width: 2;
  stroke-dasharray: 5 3;

  &.sequence {
    stroke-dasharray: none;
    stroke: #409eff;
  }
}

.node-group {
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    transform: scale(1.05);

    .node-shape {
      stroke-width: 3;
    }
  }

  &.locked {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &.completed {
    .node-shape {
      fill: #e1f3d8;
      stroke: #67c23a;
    }
  }

  &.in_progress {
    .node-shape {
      fill: #ecf5ff;
      stroke: #409eff;
    }
  }
}

.node-shape {
  fill: white;
  stroke: #dcdfe6;
  stroke-width: 2;
  transition: all 0.3s;

  &.milestone {
    fill: #fef0f0;
    stroke: #f56c6c;
  }
}

.node-icon {
  font-size: 18px;
  fill: #303133;
}

.node-title {
  font-size: 11px;
  fill: #606266;
}

.status-indicator {
  fill: #409eff;

  &.completed {
    fill: #67c23a;

    &::after {
      content: '✓';
      font-size: 10px;
      fill: white;
    }
  }

  &.locked {
    fill: #909399;
  }

  &.pulse {
    animation: pulse 1.5s infinite;
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.node-detail {
  background: white;
  border-radius: 8px;
  padding: 16px;
  max-height: 300px;
  overflow-y: auto;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;

  .detail-title {
    display: flex;
    align-items: center;
    gap: 8px;

    h4 {
      margin: 0;
    }
  }
}

.detail-desc {
  color: #606266;
  margin-bottom: 12px;
}

.detail-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  font-size: 13px;

  .meta-item {
    display: flex;
    gap: 8px;
    align-items: center;

    .meta-label {
      color: #909399;
    }
  }
}

.detail-content-preview {
  margin-bottom: 12px;

  h5 {
    margin: 0 0 8px 0;
    font-size: 14px;
  }

  .content-body {
    background: #f5f7fa;
    padding: 12px;
    border-radius: 4px;
    font-size: 13px;
    max-height: 150px;
    overflow-y: auto;
  }
}

.detail-actions {
  display: flex;
  gap: 8px;
}

.node-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
  overflow-y: auto;
  max-height: 400px;
}

.node-card {
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  &.locked {
    opacity: 0.6;
  }

  &.completed {
    background: #f0f9eb;
  }

  &.in_progress {
    background: #ecf5ff;
    border-color: #409eff;
  }

  .node-card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;

    .node-icon {
      font-size: 18px;
    }

    .node-title {
      flex: 1;
      font-weight: 600;
    }
  }

  .node-card-meta {
    display: flex;
    gap: 16px;
    font-size: 12px;
    color: #909399;
  }
}

.learning-dialog {
  .learning-content {
    .learning-progress {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
      font-size: 14px;
      color: #606266;
    }

    .learning-body {
      background: #f5f7fa;
      padding: 16px;
      border-radius: 8px;
      max-height: 400px;
      overflow-y: auto;
      margin-bottom: 16px;
      line-height: 1.8;
    }

    .learning-actions {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
    }
  }
}

.practice-content {
  .practice-question {
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid #ebeef5;

    &:last-child {
      border-bottom: none;
    }

    h5 {
      margin: 0 0 8px 0;
      color: #303133;
    }

    p {
      margin: 0 0 12px 0;
      color: #606266;
    }
  }
}
</style>
