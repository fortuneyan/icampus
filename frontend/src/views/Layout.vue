<template>
  <el-container class="app-layout">
    <el-aside width="220px">
      <div class="logo">
        <el-icon size="24"><School /></el-icon>
        <span>智慧校园</span>
      </div>
      <el-menu
        :default-active="route.path"
        router
        class="menu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>首页</span>
        </el-menu-item>
        
        <!-- ==================== 系统管理 ==================== -->
        <el-sub-menu index="system">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统管理</span>
          </template>
          <el-menu-item index="/system/users">用户管理</el-menu-item>
          <el-menu-item index="/system/roles">角色管理</el-menu-item>
          <el-menu-item index="/system/departments">部门管理</el-menu-item>
          <el-menu-item index="/system/logs/operation">操作日志</el-menu-item>
          <el-menu-item index="/system/logs/login">登录日志</el-menu-item>
          <el-menu-item index="/system/monitor">
            服务监控
            <el-tag size="small" type="success" effect="dark" class="menu-tag">NEW</el-tag>
          </el-menu-item>
          <el-menu-item index="/system/online-users">
            在线用户
            <el-tag size="small" type="success" effect="dark" class="menu-tag">NEW</el-tag>
          </el-menu-item>
          <el-menu-item index="/system/scheduler">
            定时任务
            <el-tag size="small" type="success" effect="dark" class="menu-tag">NEW</el-tag>
          </el-menu-item>
          <el-menu-item index="/system/cache">
            缓存监控
            <el-tag size="small" type="success" effect="dark" class="menu-tag">NEW</el-tag>
          </el-menu-item>
        </el-sub-menu>
        
        <!-- ==================== 教务管理 ==================== -->
        <el-sub-menu index="edu">
          <template #title>
            <el-icon><Reading /></el-icon>
            <span>教务管理</span>
          </template>
          <el-menu-item index="/edu/grades">年级管理</el-menu-item>
          <el-menu-item index="/edu/classes">班级管理</el-menu-item>
          <el-menu-item index="/edu/students">学生管理</el-menu-item>
          <el-menu-item index="/edu/courses">课程管理</el-menu-item>
          <el-menu-item index="/edu/scores">成绩管理</el-menu-item>
          <el-menu-item index="/edu/schedules">课表管理</el-menu-item>
          <el-menu-item index="/edu/classrooms">教室管理</el-menu-item>
        </el-sub-menu>
        
        <!-- ==================== 资源管理 ==================== -->
        <el-sub-menu index="resource">
          <template #title>
            <el-icon><Document /></el-icon>
            <span>资源管理</span>
          </template>
          <el-menu-item index="/resource/list">资源库</el-menu-item>
          <el-menu-item index="/resource/favorites">我的收藏</el-menu-item>
          <el-menu-item index="/resource/recommend">推荐资源</el-menu-item>
        </el-sub-menu>
        
        <!-- ==================== AI 服务 ==================== -->
        <el-sub-menu index="ai" class="ai-menu">
          <template #title>
            <el-icon><MagicStick /></el-icon>
            <span>AI 服务</span>
            <el-badge value="NEW" class="ai-badge" />
          </template>
          <el-menu-item index="/ai/chat">
            <el-icon><ChatDotRound /></el-icon>
            智能对话
          </el-menu-item>
          <el-menu-item index="/ai/learning-agent">
            <el-icon><User /></el-icon>
            学习助手
          </el-menu-item>
          <el-menu-item index="/ai/zen-tutor">
            <el-icon><Connection /></el-icon>
            AI私教
            <el-tag size="small" type="warning" effect="dark" class="menu-tag">AI</el-tag>
          </el-menu-item>
          <el-menu-item index="/ai/learning-path">
            <el-icon><Guide /></el-icon>
            学习路径
            <el-tag size="small" type="primary" effect="dark" class="menu-tag">NEW</el-tag>
          </el-menu-item>
          <el-menu-item index="/ai/learning-records">
            <el-icon><Histogram /></el-icon>
            学习记录
            <el-tag size="small" type="primary" effect="dark" class="menu-tag">NEW</el-tag>
          </el-menu-item>
          <el-menu-item index="/ai/teacher-assistant">
            <el-icon><Monitor /></el-icon>
            教师助手
            <el-tag size="small" type="primary" effect="dark" class="menu-tag">NEW</el-tag>
          </el-menu-item>
        </el-sub-menu>
        
        <!-- ==================== 考试管理 ==================== -->
        <el-sub-menu index="exam">
          <template #title>
            <el-icon><Edit /></el-icon>
            <span>考试管理</span>
          </template>
          <el-menu-item index="/exam/list">考试列表</el-menu-item>
        </el-sub-menu>
        
        <!-- ==================== 考勤管理 ==================== -->
        <el-sub-menu index="attendance">
          <template #title>
            <el-icon><Clock /></el-icon>
            <span>考勤管理</span>
          </template>
          <el-menu-item index="/attendance/list">考勤记录</el-menu-item>
        </el-sub-menu>
        
        <!-- ==================== 通知公告 ==================== -->
        <el-sub-menu index="notice">
          <template #title>
            <el-icon><Bell /></el-icon>
            <span>通知公告</span>
          </template>
          <el-menu-item index="/notice/list">通知列表</el-menu-item>
        </el-sub-menu>
        
        <!-- ==================== 扩展业务 ==================== -->
        <el-sub-menu index="extended">
          <template #title>
            <el-icon><Grid /></el-icon>
            <span>扩展业务</span>
          </template>
          <el-menu-item index="/extended/dormitory">宿舍管理</el-menu-item>
          <el-menu-item index="/extended/library">图书管理</el-menu-item>
          <el-menu-item index="/extended/card">一卡通</el-menu-item>
          <el-menu-item index="/extended/scholarship">奖助学金</el-menu-item>
        </el-sub-menu>
        
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header>
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentModule">{{ currentModule }}</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentPage">{{ currentPage }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <ThemeSwitch />
          <el-button type="primary" link @click="goToAIChat">
            <el-icon><ChatDotRound /></el-icon>
            AI 助手
          </el-button>
          <el-button type="primary" link @click="goToDashboard">
            <el-icon><DataAnalysis /></el-icon>
            数据概览
          </el-button>
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" :icon="UserIcon" />
              <span class="username">{{ username }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="settings">系统设置</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import {
  School,
  DataAnalysis,
  Setting,
  Reading,
  Document,
  MagicStick,
  Clock,
  Bell,
  Edit,
  Grid,
  ChatDotRound,
  User,
  Histogram,
  Guide,
  Monitor,
  UserFilled
} from '@element-plus/icons-vue'
import ThemeSwitch from '@/components/ThemeSwitch.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 用户头像图标
const UserIcon = UserFilled

// 当前用户名
const username = computed(() => userStore.userInfo?.real_name || userStore.userInfo?.username || 'Admin')

// 当前面包屑
const currentModule = computed(() => {
  const path = route.path
  const moduleMap: Record<string, string> = {
    '/dashboard': '首页',
    '/system': '系统管理',
    '/edu': '教务管理',
    '/resource': '资源管理',
    '/ai': 'AI 服务',
    '/exam': '考试管理',
    '/attendance': '考勤管理',
    '/notice': '通知公告',
    '/extended': '扩展业务',
    '/settings': '系统设置'
  }
  for (const [key, value] of Object.entries(moduleMap)) {
    if (path.startsWith(key)) return value
  }
  return ''
})

const currentPage = computed(() => {
  return route.meta?.title as string || ''
})

// 跳转到 AI 对话
const goToAIChat = () => {
  router.push('/ai/chat')
}

// 跳转到仪表盘
const goToDashboard = () => {
  router.push('/dashboard')
}

// 处理下拉菜单命令
const handleCommand = (command: string) => {
  switch (command) {
    case 'logout':
      userStore.logout()
      router.push('/login')
      ElMessage.success('已退出登录')
      break
    case 'profile':
      ElMessage.info('个人中心功能开发中')
      break
    case 'settings':
      router.push('/settings')
      break
  }
}
</script>

<style scoped lang="scss">
.app-layout {
  height: 100vh;
  
  .el-aside {
    background-color: #304156;
    
    .logo {
      height: 60px;
    }
    
    .menu {
      border-right: none;
      
      // 菜单项内标签样式
      :deep(.el-menu-item) {
        display: flex;
        align-items: center;
        gap: 8px;
        
        .menu-tag {
          margin-left: auto;
          transform: scale(0.8);
        }
      }
      
      // AI 菜单特殊样式
      .ai-menu {
        :deep(.el-sub-menu__title) {
          display: flex;
          align-items: center;
          gap: 8px;
        }
      }
      
      .ai-badge {
        margin-left: 8px;
      }
    }
  }
  
  .el-header {
    background-color: #fff;
    box-shadow: 0 1px 4px rgba(0,21,41,.08);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 20px;
    
    .header-left {
      display: flex;
      align-items: center;
    }
    
    .header-right {
      display: flex;
      align-items: center;
      gap: 16px;
      
      .user-info {
        display: flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: 4px;
        transition: background-color 0.3s;
        
        &:hover {
          background-color: #f5f7fa;
        }
        
        .username {
          font-weight: 500;
          color: #303133;
        }
      }
    }
  }
  
  .el-main {
    background-color: #f0f2f5;
    padding: 20px;
    
    // toolbar 中的 select 元素宽度设置
    :deep(.toolbar) {
      .el-form-item__content {
        // 确保内容区域宽度自适应
        display: inline-flex;
        align-items: center;
        
        .el-select {
          // 设置一个足够显示常见内容的最小宽度
          min-width: 140px;
          width: auto !important;
          max-width: 300px;
          
          // 让选择器根据内容自动调整
          .el-select__wrapper {
            width: auto;
            min-width: 140px;
          }
          
          // 确保选中项能完整显示
          .el-select__selection {
            width: auto;
            min-width: 140px;
          }
          
          // 占位符和选中文字不换行
          .el-select__placeholder,
          .el-select__selected-item {
            white-space: nowrap;
          }
        }
      }
    }
  }
}

// 面包屑样式
:deep(.el-breadcrumb) {
  font-size: 14px;
  
  .el-breadcrumb__inner {
    color: #909399;
    
    &.is-link:hover {
      color: #409eff;
    }
  }
  
  .el-breadcrumb__item:last-child .el-breadcrumb__inner {
    color: #303133;
    font-weight: 500;
  }
}
</style>
