<template>
  <div class="dashboard">
    <el-card class="welcome-card">
      <h2>欢迎回来，{{ userStore.userInfo?.real_name || userStore.userInfo?.username }}</h2>
      <p>智慧校园管理平台</p>
    </el-card>
    
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <el-icon :size="40" color="#409eff"><User /></el-icon>
            <div class="stat-info">
              <span class="stat-value">{{ stats.student_count || 0 }}</span>
              <span class="stat-label">学生总数</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <el-icon :size="40" color="#67c23a"><Reading /></el-icon>
            <div class="stat-info">
              <span class="stat-value">{{ stats.teacher_count || 0 }}</span>
              <span class="stat-label">教师总数</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <el-icon :size="40" color="#e6a23c"><School /></el-icon>
            <div class="stat-info">
              <span class="stat-value">{{ stats.class_count || 0 }}</span>
              <span class="stat-label">班级总数</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <el-icon :size="40" color="#f56c6c"><Files /></el-icon>
            <div class="stat-info">
              <span class="stat-value">{{ stats.course_count || 0 }}</span>
              <span class="stat-label">课程总数</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { getDashboardStats } from '@/api/dashboard'
import { User, Reading, School, Files } from '@element-plus/icons-vue'

const userStore = useUserStore()

const stats = ref({
  student_count: 0,
  teacher_count: 0,
  class_count: 0,
  course_count: 0
})

const fetchStats = async () => {
  try {
    const res = await getDashboardStats()
    if (res.data) {
      stats.value = res.data
    }
  } catch (e) {
    console.error('获取统计数据失败', e)
  }
}

onMounted(() => {
  fetchStats()
})
</script>

<style scoped lang="scss">
.dashboard {
  padding: 20px;
}

.welcome-card {
  margin-bottom: 20px;
  
  h2 {
    margin-bottom: 10px;
    color: #333;
  }
  
  p {
    color: #666;
  }
}

.stats-row {
  margin-top: 20px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 20px;
  
  .stat-info {
    display: flex;
    flex-direction: column;
    
    .stat-value {
      font-size: 24px;
      font-weight: bold;
      color: #333;
    }
    
    .stat-label {
      font-size: 14px;
      color: #999;
    }
  }
}
</style>