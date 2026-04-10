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
        
        <el-sub-menu index="system">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统管理</span>
          </template>
          <el-menu-item index="/system/users">用户管理</el-menu-item>
          <el-menu-item index="/system/roles">角色管理</el-menu-item>
          <el-menu-item index="/system/departments">部门管理</el-menu-item>
        </el-sub-menu>
        
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
        
        <el-sub-menu index="resource">
          <template #title>
            <el-icon><Document /></el-icon>
            <span>资源管理</span>
          </template>
          <el-menu-item index="/resource/list">资源库</el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu index="ai">
          <template #title>
            <el-icon><MagicStick /></el-icon>
            <span>AI服务</span>
          </template>
          <el-menu-item index="/ai/chat">智能对话</el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu index="exam">
          <template #title>
            <el-icon><Document /></el-icon>
            <span>考试管理</span>
          </template>
          <el-menu-item index="/exam/list">考试列表</el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu index="attendance">
          <template #title>
            <el-icon><Clock /></el-icon>
            <span>考勤管理</span>
          </template>
          <el-menu-item index="/attendance/list">考勤记录</el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu index="notice">
          <template #title>
            <el-icon><Bell /></el-icon>
            <span>通知公告</span>
          </template>
          <el-menu-item index="/notice/list">通知列表</el-menu-item>
        </el-sub-menu>
        
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><User /></el-icon>
              <span>{{ username }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
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
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { School, DataAnalysis, Setting, Reading, User } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const username = computed(() => userStore.userInfo?.real_name || userStore.userInfo?.username || 'Admin')

const handleCommand = (command: string) => {
  if (command === 'logout') {
    userStore.logout()
    router.push('/login')
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
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      color: #fff;
      font-size: 18px;
      font-weight: bold;
      border-bottom: 1px solid #3a4554;
    }
    
    .menu {
      border-right: none;
    }
  }
  
  .el-header {
    background-color: #fff;
    box-shadow: 0 1px 4px rgba(0,21,41,.08);
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding: 0 20px;
    
    .user-info {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
    }
  }
  
  .el-main {
    background-color: #f0f2f5;
    padding: 20px;
  }
}
</style>