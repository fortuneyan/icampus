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
import {
  getCacheStats,
  getCacheKeys,
  getCacheKey,
  deleteCacheKey,
  clearExpiredKeys,
  getCacheTypes,
  getMemoryTrend,
  type CacheStats,
  type CacheKeyInfo,
  type CacheTypeStat
} from '@/api/system/cache'

// 统计数据
const stats = reactive<Partial<CacheStats>>({
  total_keys: 0,
  hit_rate: 0,
  memory_usage: 0,
  expired_keys: 0
})

// 表格数据
const tableData = ref<CacheKeyInfo[]>([])

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
const currentCache = ref<Partial<CacheKeyInfo> & { value?: string }>({})
const currentCacheValue = ref('')

// 缓存类型分布数据
const typeStats = ref<CacheTypeStat[]>([])

// 格式化大小
const formatSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

// 加载统计数据
const loadStats = async () => {
  try {
    const res = await getCacheStats()
    if (res.data.code === 200) {
      const data = res.data.data || {}
      stats.total_keys = data.total_keys || 0
      stats.hit_rate = data.hit_rate || 0
      stats.memory_usage = data.memory_usage || 0
      stats.expired_keys = data.expired_keys || 0
    }
  } catch (error) {
    console.error('加载统计失败', error)
  }
}

// 加载缓存键列表
const loadKeys = async () => {
  loading.value = true
  try {
    const res = await getCacheKeys({
      page: currentPage.value,
      page_size: pageSize.value
    })
    if (res.data.code === 200) {
      tableData.value = res.data.data || []
      total.value = res.data.total || 0
    }
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 加载缓存类型分布
const loadTypeStats = async () => {
  try {
    const res = await getCacheTypes()
    if (res.data.code === 200) {
      typeStats.value = res.data.data || []
    }
  } catch (error) {
    console.error('加载类型分布失败', error)
  }
}

// 加载内存趋势
const loadMemoryTrend = async () => {
  try {
    const res = await getMemoryTrend(24)
    if (res.data.code === 200) {
      return res.data.data
    }
  } catch (error) {
    console.error('加载内存趋势失败', error)
  }
  return null
}

// 加载所有数据
const loadData = async () => {
  await Promise.all([
    loadStats(),
    loadKeys(),
    loadTypeStats()
  ])
  initCharts()
}

// 初始化图表
const initCharts = async () => {
  await nextTick()
  
  // 类型分布饼图
  if (typeChartRef.value && typeStats.value.length > 0) {
    typeChart = echarts.init(typeChartRef.value)
    const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272']
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
        data: typeStats.value.map((t, i) => ({
          value: t.count,
          name: t.type,
          itemStyle: { color: colors[i % colors.length] }
        }))
      }]
    })
  }
  
  // 内存趋势图
  const trendData = await loadMemoryTrend()
  if (memoryChartRef.value && trendData) {
    memoryChart = echarts.init(memoryChartRef.value)
    memoryChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { 
        type: 'category', 
        data: trendData.data.map((d: any) => d.time)
      },
      yAxis: { type: 'value', name: 'MB' },
      series: [{
        name: '内存使用',
        type: 'line',
        smooth: true,
        areaStyle: { opacity: 0.3 },
        data: trendData.data.map((d: any) => d.memory_mb),
        lineStyle: { color: '#5470c6' },
        itemStyle: { color: '#5470c6' }
      }]
    })
  }
}

// 查看详情
const viewDetail = async (row: CacheKeyInfo) => {
  try {
    const res = await getCacheKey(row.key)
    if (res.data.code === 200) {
      const data = res.data.data || {}
      currentCache.value = { ...row, ...data }
      currentCacheValue.value = data.value || ''
      detailVisible.value = true
    }
  } catch (error) {
    ElMessage.error('获取详情失败')
  }
}

// 删除键
const deleteKey = async (row: CacheKeyInfo) => {
  try {
    await ElMessageBox.confirm(`确定要删除缓存键 "${row.key}" 吗？`, '确认删除')
    const res = await deleteCacheKey(row.key)
    if (res.data.code === 200) {
      ElMessage.success('删除成功')
      loadData()
    }
  } catch {
    // 取消操作
  }
}

// 清理过期
const clearExpired = async () => {
  try {
    await ElMessageBox.confirm('确定要清理所有过期缓存吗？', '确认操作')
    const res = await clearExpiredKeys()
    if (res.data.code === 200) {
      const count = res.data.data?.cleared_count || 0
      ElMessage.success(`清理完成，共清理 ${count} 条过期缓存`)
      loadData()
    }
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
