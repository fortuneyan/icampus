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
import { getOnlineUsers, forceUserLogout } from '@/api/system/online_user'

// 数据列表
const tableData = ref([
  { user_id: 1, username: 'admin', real_name: '管理员', role: '管理员', ip_address: '192.168.1.100', login_time: '2026-04-12 08:30:00', last_activity: '2026-04-12 16:30:00', status: 'active' },
  { user_id: 2, username: 'teacher1', real_name: '张老师', role: '教师', ip_address: '192.168.1.101', login_time: '2026-04-12 08:00:00', last_activity: '2026-04-12 16:25:00', status: 'active' },
  { user_id: 3, username: 'student1', real_name: '李同学', role: '学生', ip_address: '192.168.1.102', login_time: '2026-04-12 09:00:00', last_activity: '2026-04-12 16:20:00', status: 'idle' },
])

// 统计数据
const stats = reactive({
  online_count: 3,
  active_count: 2,
  today_login: 45,
  peak_count: 12
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
    // TODO: 替换为真实 API 调用
    // const res = await getOnlineUsers({ page: currentPage.value, page_size: pageSize.value })
    // tableData.value = res.data
    // total.value = res.total
    total.value = tableData.value.length
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
    // TODO: 替换为真实 API 调用
    // await forceUserLogout(row.user_id)
    ElMessage.success(`用户 ${row.real_name} 已强制下线`)
    loadData()
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
