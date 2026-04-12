<template>
  <div class="monitor-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>服务监控面板</h2>
      <div class="header-actions">
        <el-button :icon="Refresh" @click="refreshAll" :loading="loading">
          刷新数据
        </el-button>
        <el-switch
          v-model="autoRefresh"
          active-text="自动刷新(30s)"
          inactive-text="手动刷新"
        />
      </div>
    </div>

    <!-- 健康状态概览 -->
    <el-row :gutter="20" class="status-overview">
      <el-col :span="6">
        <div class="status-card" :class="healthClass">
          <div class="status-icon">
            <el-icon v-if="healthStatus.overall === 'healthy'" :size="40" color="#67C23A">
              <CircleCheck />
            </el-icon>
            <el-icon v-else-if="healthStatus.overall === 'degraded'" :size="40" color="#E6A23C">
              <Warning />
            </el-icon>
            <el-icon v-else :size="40" color="#F56C6C">
              <CircleClose />
            </el-icon>
          </div>
          <div class="status-info">
            <div class="status-label">系统状态</div>
            <div class="status-value">{{ healthLabel }}</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="status-card cpu">
          <div class="status-icon">
            <el-icon :size="40" color="#409EFF"><Cpu /></el-icon>
          </div>
          <div class="status-info">
            <div class="status-label">CPU 使用率</div>
            <div class="status-value">{{ systemInfo.cpu?.percent || 0 }}%</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="status-card memory">
          <div class="status-icon">
            <el-icon :size="40" color="#9C27B0"><Monitor /></el-icon>
          </div>
          <div class="status-info">
            <div class="status-label">内存使用率</div>
            <div class="status-value">{{ systemInfo.memory?.percent || 0 }}%</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="status-card disk">
          <div class="status-icon">
            <el-icon :size="40" color="#FF9800"><Folder /></el-icon>
          </div>
          <div class="status-info">
            <div class="status-label">磁盘使用率</div>
            <div class="status-value">{{ systemInfo.disk?.percent || 0 }}%</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 详细监控数据 -->
    <el-row :gutter="20" class="monitor-details">
      <!-- CPU 详情 -->
      <el-col :span="12">
        <el-card class="monitor-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><Cpu /></el-icon> CPU 监控</span>
            </div>
          </template>
          <div class="metric-detail">
            <div class="metric-bar">
              <div class="metric-label">CPU 使用率</div>
              <div class="metric-value">{{ systemInfo.cpu?.percent || 0 }}%</div>
            </div>
            <el-progress
              :percentage="systemInfo.cpu?.percent || 0"
              :color="getProgressColor(systemInfo.cpu?.percent || 0)"
              :stroke-width="20"
            />
            <div class="metric-info">
              <span>核心数: {{ systemInfo.cpu?.count || 0 }}</span>
              <span v-if="systemInfo.cpu?.frequency">
                频率: {{ systemInfo.cpu?.frequency.toFixed(0) }} MHz
              </span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 内存详情 -->
      <el-col :span="12">
        <el-card class="monitor-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><Monitor /></el-icon> 内存监控</span>
            </div>
          </template>
          <div class="metric-detail">
            <div class="metric-bar">
              <div class="metric-label">内存使用率</div>
              <div class="metric-value">{{ systemInfo.memory?.percent || 0 }}%</div>
            </div>
            <el-progress
              :percentage="systemInfo.memory?.percent || 0"
              :color="getProgressColor(systemInfo.memory?.percent || 0)"
              :stroke-width="20"
            />
            <div class="metric-info">
              <span>已用: {{ systemInfo.memory?.used_gb || 0 }} GB</span>
              <span>总计: {{ systemInfo.memory?.total_gb || 0 }} GB</span>
              <span>可用: {{ systemInfo.memory?.available_gb || 0 }} GB</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="monitor-details">
      <!-- 磁盘详情 -->
      <el-col :span="12">
        <el-card class="monitor-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><Folder /></el-icon> 磁盘监控</span>
            </div>
          </template>
          <div class="metric-detail">
            <div class="metric-bar">
              <div class="metric-label">磁盘使用率</div>
              <div class="metric-value">{{ systemInfo.disk?.percent || 0 }}%</div>
            </div>
            <el-progress
              :percentage="systemInfo.disk?.percent || 0"
              :color="getProgressColor(systemInfo.disk?.percent || 0)"
              :stroke-width="20"
            />
            <div class="metric-info">
              <span>已用: {{ systemInfo.disk?.used_gb || 0 }} GB</span>
              <span>总计: {{ systemInfo.disk?.total_gb || 0 }} GB</span>
              <span>可用: {{ systemInfo.disk?.free_gb || 0 }} GB</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 数据库连接池 -->
      <el-col :span="12">
        <el-card class="monitor-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><Connection /></el-icon> 数据库连接池</span>
              <el-tag :type="getDbPoolStatusType()" size="small">
                {{ dbInfo.pool?.status || 'unknown' }}
              </el-tag>
            </div>
          </template>
          <div class="metric-detail">
            <div class="db-pool-info">
              <div class="pool-stat">
                <div class="pool-label">连接池大小</div>
                <div class="pool-value">{{ dbInfo.pool?.pool_size || 0 }}</div>
              </div>
              <div class="pool-stat">
                <div class="pool-label">已使用</div>
                <div class="pool-value used">{{ dbInfo.pool?.checked_out || 0 }}</div>
              </div>
              <div class="pool-stat">
                <div class="pool-label">可用</div>
                <div class="pool-value available">{{ dbInfo.pool?.checked_in || 0 }}</div>
              </div>
              <div class="pool-stat">
                <div class="pool-label">溢出</div>
                <div class="pool-value overflow">{{ dbInfo.pool?.overflow || 0 }}</div>
              </div>
            </div>
            <div class="pool-usage">
              <span>数据库: {{ dbInfo.database || 'N/A' }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 系统信息 -->
    <el-row :gutter="20" class="monitor-details">
      <!-- 系统信息 -->
      <el-col :span="12">
        <el-card class="monitor-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><InfoFilled /></el-icon> 系统信息</span>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="操作系统">
              {{ systemInfo.platform || 'N/A' }}
            </el-descriptions-item>
            <el-descriptions-item label="系统版本">
              {{ systemInfo.platform_version || 'N/A' }}
            </el-descriptions-item>
            <el-descriptions-item label="运行时长">
              {{ formatUptime(systemInfo.uptime_seconds) }}
            </el-descriptions-item>
            <el-descriptions-item label="更新时间">
              {{ formatTime(systemInfo.timestamp) }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <!-- 进程信息 -->
      <el-col :span="12">
        <el-card class="monitor-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><Document /></el-icon> 当前进程</span>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="进程 ID">
              {{ processInfo.pid || 'N/A' }}
            </el-descriptions-item>
            <el-descriptions-item label="进程状态">
              <el-tag size="small">{{ processInfo.status || 'N/A' }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="内存使用">
              {{ processInfo.memory_mb || 0 }} MB
            </el-descriptions-item>
            <el-descriptions-item label="线程数">
              {{ processInfo.num_threads || 0 }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <!-- 健康检查详情 -->
    <el-card class="health-checks">
      <template #header>
        <div class="card-header">
          <span><el-icon><CircleCheck /></el-icon> 健康检查详情</span>
        </div>
      </template>
      <el-table :data="healthCheckItems" style="width: 100%">
        <el-table-column prop="name" label="检查项" width="150" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.statusType" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="value" label="当前值" />
        <el-table-column label="描述">
          <template #default="{ row }">
            <span :class="row.statusClass">{{ row.description }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Refresh,
  Cpu,
  Monitor,
  Folder,
  Connection,
  InfoFilled,
  Document,
  CircleCheck,
  Warning,
  CircleClose
} from '@element-plus/icons-vue'
import request from '@/utils/request'

// 格式化时间戳
function formatTime(timestamp?: string): string {
  if (!timestamp) return 'N/A'
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN')
}

// ==================== 数据定义 ====================

interface CPUInfo {
  percent: number
  count: number
  frequency?: number
}

interface MemoryInfo {
  total_gb: number
  used_gb: number
  available_gb: number
  percent: number
}

interface DiskInfo {
  total_gb: number
  used_gb: number
  free_gb: number
  percent: number
}

interface SystemInfo {
  cpu?: CPUInfo
  memory?: MemoryInfo
  disk?: DiskInfo
  platform?: string
  platform_version?: string
  uptime_seconds?: number
  timestamp?: string
}

interface DatabasePoolInfo {
  pool_size: number
  checked_out: number
  overflow: number
  checked_in: number
  status: string
}

interface DatabaseInfo {
  pool?: DatabasePoolInfo
  database?: string
  status?: string
}

interface HealthStatus {
  overall?: string
  checks?: {
    cpu?: { status: string; value: string }
    memory?: { status: string; value: string }
    disk?: { status: string; value: string }
    database?: { status: string; value: string }
  }
  timestamp?: string
}

interface ProcessInfo {
  pid?: number
  memory_mb?: number
  cpu_percent?: number
  num_threads?: number
  create_time?: string
  status?: string
}

// ==================== 响应式数据 ====================

const loading = ref(false)
const autoRefresh = ref(false)
let refreshInterval: number | null = null

const systemInfo = ref<SystemInfo>({})
const dbInfo = ref<DatabaseInfo>({})
const healthStatus = ref<HealthStatus>({})
const processInfo = ref<ProcessInfo>({})

// ==================== 计算属性 ====================

const healthClass = computed(() => {
  switch (healthStatus.value.overall) {
    case 'healthy':
      return 'healthy'
    case 'degraded':
      return 'degraded'
    case 'unhealthy':
      return 'unhealthy'
    default:
      return ''
  }
})

const healthLabel = computed(() => {
  switch (healthStatus.value.overall) {
    case 'healthy':
      return '健康'
    case 'degraded':
      return '轻微异常'
    case 'unhealthy':
      return '异常'
    default:
      return '未知'
  }
})

const healthCheckItems = computed(() => {
  const checks = healthStatus.value.checks || {}
  return [
    {
      name: 'CPU',
      status: checks.cpu?.status === 'ok' ? '正常' : '警告',
      statusType: checks.cpu?.status === 'ok' ? 'success' : 'warning',
      value: checks.cpu?.value || 'N/A',
      description: checks.cpu?.status === 'ok' ? 'CPU 使用率正常' : 'CPU 使用率过高',
      statusClass: checks.cpu?.status === 'ok' ? 'text-success' : 'text-warning'
    },
    {
      name: '内存',
      status: checks.memory?.status === 'ok' ? '正常' : '警告',
      statusType: checks.memory?.status === 'ok' ? 'success' : 'warning',
      value: checks.memory?.value || 'N/A',
      description: checks.memory?.status === 'ok' ? '内存使用正常' : '内存使用率过高',
      statusClass: checks.memory?.status === 'ok' ? 'text-success' : 'text-warning'
    },
    {
      name: '磁盘',
      status: checks.disk?.status === 'ok' ? '正常' : '警告',
      statusType: checks.disk?.status === 'ok' ? 'success' : 'warning',
      value: checks.disk?.value || 'N/A',
      description: checks.disk?.status === 'ok' ? '磁盘空间充足' : '磁盘空间不足',
      statusClass: checks.disk?.status === 'ok' ? 'text-success' : 'text-warning'
    },
    {
      name: '数据库',
      status: checks.database?.status === 'healthy' ? '正常' : '警告',
      statusType: checks.database?.status === 'healthy' ? 'success' : 'warning',
      value: `${checks.database?.pool_size || 0} 连接`,
      description: checks.database?.status === 'healthy' ? '连接池状态正常' : '连接池压力较大',
      statusClass: checks.database?.status === 'healthy' ? 'text-success' : 'text-warning'
    }
  ]
})

// ==================== 方法 ====================

function getProgressColor(percent: number): string {
  if (percent < 60) return '#67C23A'
  if (percent < 80) return '#E6A23C'
  return '#F56C6C'
}

function getDbPoolStatusType(): string {
  switch (dbInfo.value.pool?.status) {
    case 'healthy':
      return 'success'
    case 'degraded':
      return 'warning'
    case 'unhealthy':
      return 'danger'
    default:
      return 'info'
  }
}

function formatUptime(seconds?: number): string {
  if (!seconds) return 'N/A'
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (days > 0) {
    return `${days} 天 ${hours} 小时`
  }
  if (hours > 0) {
    return `${hours} 小时 ${minutes} 分钟`
  }
  return `${minutes} 分钟`
}

async function fetchSystemInfo() {
  try {
    const res = await request.get('/system/monitor/system')
    systemInfo.value = res.data
  } catch (error) {
    console.error('获取系统信息失败:', error)
  }
}

async function fetchDatabaseInfo() {
  try {
    const res = await request.get('/system/monitor/database')
    dbInfo.value = res.data
  } catch (error) {
    console.error('获取数据库信息失败:', error)
  }
}

async function fetchHealthStatus() {
  try {
    const res = await request.get('/system/monitor/health')
    healthStatus.value = res.data
  } catch (error) {
    console.error('获取健康状态失败:', error)
  }
}

async function fetchProcessInfo() {
  try {
    const res = await request.get('/system/monitor/process')
    processInfo.value = res.data
  } catch (error) {
    console.error('获取进程信息失败:', error)
  }
}

async function refreshAll() {
  loading.value = true
  try {
    await Promise.all([
      fetchSystemInfo(),
      fetchDatabaseInfo(),
      fetchHealthStatus(),
      fetchProcessInfo()
    ])
  } finally {
    loading.value = false
  }
}

function startAutoRefresh() {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
  refreshInterval = window.setInterval(() => {
    refreshAll()
  }, 30000) // 30 秒
}

function stopAutoRefresh() {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
}

// ==================== 生命周期 ====================

onMounted(() => {
  refreshAll()
})

onUnmounted(() => {
  stopAutoRefresh()
})

// 监听自动刷新开关
import { watch } from 'vue'

watch(autoRefresh, (newVal) => {
  if (newVal) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
})
</script>

<style scoped>
.monitor-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 15px;
  align-items: center;
}

/* 状态概览卡片 */
.status-overview {
  margin-bottom: 20px;
}

.status-card {
  display: flex;
  align-items: center;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.status-card.healthy {
  background: linear-gradient(135deg, #f0f9eb 0%, #e8f5e1 100%);
  border-left: 4px solid #67c23a;
}

.status-card.degraded {
  background: linear-gradient(135deg, #fdf6ec 0%, #fef0e1 100%);
  border-left: 4px solid #e6a23c;
}

.status-card.unhealthy {
  background: linear-gradient(135deg, #fef0f0 0%, #fee 100%);
  border-left: 4px solid #f56c6c;
}

.status-icon {
  margin-right: 15px;
}

.status-info {
  flex: 1;
}

.status-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 5px;
}

.status-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

/* 监控详情卡片 */
.monitor-details {
  margin-bottom: 20px;
}

.monitor-card {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header span {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.metric-detail {
  padding: 10px 0;
}

.metric-bar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.metric-label {
  font-weight: 500;
  color: #606266;
}

.metric-value {
  font-weight: 600;
  color: #303133;
}

.metric-info {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  font-size: 12px;
  color: #909399;
}

/* 数据库连接池 */
.db-pool-info {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
  margin-bottom: 15px;
}

.pool-stat {
  text-align: center;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.pool-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.pool-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.pool-value.used {
  color: #409eff;
}

.pool-value.available {
  color: #67c23a;
}

.pool-value.overflow {
  color: #e6a23c;
}

.pool-usage {
  text-align: center;
  font-size: 12px;
  color: #909399;
}

/* 健康检查 */
.health-checks {
  margin-top: 20px;
}

.text-success {
  color: #67c23a;
}

.text-warning {
  color: #e6a23c;
}

.text-danger {
  color: #f56c6c;
}
</style>
