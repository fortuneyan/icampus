<template>
  <div class="cache-container">
    <!-- 缓存概览 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="总缓存键数" :value="stats.total_keys">
            <template #prefix>
              <el-icon><Key /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="缓存命中率" :value="stats.hit_rate" suffix="%">
            <template #prefix>
              <el-icon><Odometer /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="内存使用" :value="stats.memory_usage" suffix="MB">
            <template #prefix>
              <el-icon><Cpu /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="过期键数量" :value="stats.expired_keys">
            <template #prefix>
              <el-icon><Timer /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 缓存列表 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>缓存键列表</span>
          <div>
            <el-button @click="clearExpired">
              <el-icon><Delete /></el-icon>
              清理过期
            </el-button>
            <el-button type="primary" @click="loadData">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="key" label="缓存键" min-width="200" show-overflow-tooltip />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ttl" label="TTL(秒)" width="120">
          <template #default="{ row }">
            <span :class="{ 'ttl-warning': row.ttl < 60, 'ttl-danger': row.ttl < 10 }">
              {{ row.ttl > 0 ? row.ttl : '永久' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="size" label="大小" width="100">
          <template #default="{ row }">
            {{ formatSize(row.size) }}
          </template>
        </el-table-column>
        <el-table-column prop="access_count" label="访问次数" width="100" />
        <el-table-column prop="last_access" label="最后访问" width="180" />
        <el-table-column label="操作" fixed="right" width="150">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="viewDetail(row)">
              查看
            </el-button>
            <el-button type="danger" link size="small" @click="deleteKey(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </el-card>
    
    <!-- 缓存分布 -->
    <el-row :gutter="20" class="charts-row">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>缓存类型分布</span>
          </template>
          <div ref="typeChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>内存使用趋势</span>
          </template>
          <div ref="memoryChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 缓存详情对话框 -->
    <el-dialog v-model="detailVisible" title="缓存详情" width="600px">
      <el-descriptions :column="2" border v-if="currentCache">
        <el-descriptions-item label="缓存键">{{ currentCache.key }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ currentCache.type }}</el-descriptions-item>
        <el-descriptions-item label="TTL">{{ currentCache.ttl }}秒</el-descriptions-item>
        <el-descriptions-item label="大小">{{ formatSize(currentCache.size) }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ currentCache.created_at }}</el-descriptions-item>
        <el-descriptions-item label="最后访问">{{ currentCache.last_access }}</el-descriptions-item>
        <el-descriptions-item label="访问次数">{{ currentCache.access_count }}</el-descriptions-item>
        <el-descriptions-item label="创建者">{{ currentCache.creator }}</el-descriptions-item>
      </el-descriptions>
      <el-divider />
      <div class="cache-value">
        <h4>缓存值</h4>
        <el-input
          v-model="currentCacheValue"
          type="textarea"
          :rows="6"
          readonly
        />
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Key, Odometer, Cpu, Timer, Delete, Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

// 统计数据
const stats = reactive({
  total_keys: 1234,
  hit_rate: 85.6,
  memory_usage: 256,
  expired_keys: 45
})

// 表格数据
const tableData = ref([
  { key: 'user:profile:1001', type: 'hash', ttl: 3600, size: 2048, access_count: 156, last_access: '2026-04-12 16:30:00', created_at: '2026-04-10 08:00:00', creator: 'user_service' },
  { key: 'course:info:2001', type: 'string', ttl: 7200, size: 1024, access_count: 89, last_access: '2026-04-12 16:25:00', created_at: '2026-04-08 10:00:00', creator: 'course_service' },
  { key: 'session:abc123', type: 'string', ttl: 1800, size: 512, access_count: 234, last_access: '2026-04-12 16:28:00', created_at: '2026-04-12 12:00:00', creator: 'auth_service' },
  { key: 'ai:ability:3001', type: 'hash', ttl: -1, size: 4096, access_count: 45, last_access: '2026-04-12 16:20:00', created_at: '2026-04-01 00:00:00', creator: 'ai_service' },
  { key: 'exam:questions:4001', type: 'list', ttl: 86400, size: 8192, access_count: 12, last_access: '2026-04-12 14:00:00', created_at: '2026-04-12 08:00:00', creator: 'exam_service' },
])

const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 图表
const typeChartRef = ref<HTMLElement>()
const memoryChartRef = ref<HTMLElement>()
let typeChart: echarts.ECharts | null = null
let memoryChart: echarts.ECharts | null = null

// 详情
const detailVisible = ref(false)
const currentCache = ref<any>(null)
const currentCacheValue = ref('')

// 格式化大小
const formatSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    total.value = tableData.value.length
    initCharts()
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 初始化图表
const initCharts = async () => {
  await nextTick()
  
  // 类型分布饼图
  if (typeChartRef.value) {
    typeChart = echarts.init(typeChartRef.value)
    typeChart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: '5%', left: 'center' },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: false },
        emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
        data: [
          { value: 580, name: 'string', itemStyle: { color: '#5470c6' } },
          { value: 280, name: 'hash', itemStyle: { color: '#91cc75' } },
          { value: 180, name: 'list', itemStyle: { color: '#fac858' } },
          { value: 100, name: 'set', itemStyle: { color: '#ee6666' } },
          { value: 94, name: 'zset', itemStyle: { color: '#73c0de' } },
        ]
      }]
    })
  }
  
  // 内存趋势图
  if (memoryChartRef.value) {
    memoryChart = echarts.init(memoryChartRef.value)
    memoryChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00'] },
      yAxis: { type: 'value', name: 'MB', max: 512 },
      series: [{
        name: '内存使用',
        type: 'line',
        smooth: true,
        areaStyle: { opacity: 0.3 },
        data: [180, 200, 220, 256, 240, 220, 256],
        lineStyle: { color: '#5470c6' },
        itemStyle: { color: '#5470c6' }
      }]
    })
  }
}

// 查看详情
const viewDetail = (row: any) => {
  currentCache.value = row
  currentCacheValue.value = JSON.stringify({
    data: '示例缓存数据...',
    timestamp: Date.now()
  }, null, 2)
  detailVisible.value = true
}

// 删除键
const deleteKey = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确定要删除缓存键 "${row.key}" 吗？`, '确认删除')
    ElMessage.success('删除成功')
    loadData()
  } catch {
    // 取消操作
  }
}

// 清理过期
const clearExpired = async () => {
  try {
    await ElMessageBox.confirm('确定要清理所有过期缓存吗？', '确认操作')
    ElMessage.success('清理完成，共清理 45 条过期缓存')
    loadData()
  } catch {
    // 取消操作
  }
}

// 窗口大小变化时重绘图表
const handleResize = () => {
  typeChart?.resize()
  memoryChart?.resize()
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  typeChart?.dispose()
  memoryChart?.dispose()
})
</script>

<style scoped lang="scss">
.cache-container {
  .stats-row {
    margin-bottom: 20px;
    
    .stat-card {
      text-align: center;
    }
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
  
  .charts-row {
    margin-top: 20px;
    
    .chart-container {
      height: 250px;
    }
  }
  
  .cache-value {
    h4 {
      margin: 0 0 10px 0;
      font-size: 14px;
      color: #606266;
    }
  }
  
  .ttl-warning {
    color: #e6a23c;
  }
  
  .ttl-danger {
    color: #f56c6c;
  }
}
</style>
