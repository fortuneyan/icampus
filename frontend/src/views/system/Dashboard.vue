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
              <span class="stat-value">1,234</span>
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
              <span class="stat-value">56</span>
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
              <span class="stat-value">12</span>
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
              <span class="stat-value">89</span>
              <span class="stat-label">课程总数</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
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