<template>
  <div class="online-users-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>在线用户</span>
          <el-button type="primary" @click="loadData">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>
      
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="user_id" label="用户ID" width="80" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="real_name" label="姓名" width="100" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag>{{ row.role || '用户' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP地址" width="140" />
        <el-table-column prop="login_time" label="登录时间" width="180" />
        <el-table-column prop="last_activity" label="最后活动" width="180" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '活跃' : '空闲' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="120">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="forceLogout(row)">
              强制下线
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </el-card>
    
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="当前在线" :value="stats.online_count">
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="活跃用户" :value="stats.active_count">
            <template #prefix>
              <el-icon><UserFilled /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="今日登录" :value="stats.today_login">
            <template #prefix>
              <el-icon><SwitchButton /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="峰值在线" :value="stats.peak_count">
            <template #prefix>
              <el-icon><TrendCharts /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, User, UserFilled, SwitchButton, TrendCharts } from '@element-plus/icons-vue'
import { getOnlineUsers, getOnlineUserStats, forceUserLogout } from '@/api/system/online_user'

// 数据列表
const tableData = ref<any[]>([])

// 统计数据
const stats = reactive({
  online_count: 0,
  active_count: 0,
  today_login: 0,
  peak_count: 0
})

// 分页
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const loading = ref(false)

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const [usersRes, statsRes] = await Promise.all([
      getOnlineUsers({ page: currentPage.value, page_size: pageSize.value }),
      getOnlineUserStats()
    ])
    
    if (usersRes.data.code === 200) {
      tableData.value = usersRes.data.data || []
      total.value = usersRes.data.total || 0
    }
    
    if (statsRes.data.code === 200) {
      const data = statsRes.data.data || {}
      stats.online_count = data.online_count || 0
      stats.active_count = data.active_count || 0
      stats.today_login = data.today_login || 0
      stats.peak_count = data.peak_count || 0
    }
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 强制下线
const forceLogout = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要强制下线用户 "${row.real_name}" 吗？`,
      '确认操作',
      { type: 'warning' }
    )
    const res = await forceUserLogout(row.user_id)
    if (res.data.code === 200) {
      ElMessage.success(`用户 ${row.real_name} 已强制下线`)
      loadData()
    } else {
      ElMessage.error(res.data.message || '操作失败')
    }
  } catch {
    // 取消操作
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.online-users-container {
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
  
  .stats-row {
    margin-top: 20px;
    
    .stat-card {
      text-align: center;
    }
  }
}
</style>
