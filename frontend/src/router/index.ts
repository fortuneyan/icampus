import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import Layout from '@/views/Layout.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [
      // ==================== 仪表盘 ====================
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('@/views/system/Dashboard.vue'),
        meta: { title: '仪表盘' },
      },

      // ==================== 系统管理 ====================
      {
        path: '/system/users',
        name: 'Users',
        component: () => import('@/views/system/User.vue'),
        meta: { title: '用户管理', module: 'system' },
      },
      {
        path: '/system/roles',
        name: 'Roles',
        component: () => import('@/views/system/Role.vue'),
        meta: { title: '角色管理', module: 'system' },
      },
      {
        path: '/system/departments',
        name: 'Departments',
        component: () => import('@/views/system/Department.vue'),
        meta: { title: '部门管理', module: 'system' },
      },
      {
        path: '/system/logs/operation',
        name: 'OperationLogs',
        component: () => import('@/views/system/OperationLog.vue'),
        meta: { title: '操作日志', module: 'system' },
      },
      {
        path: '/system/logs/login',
        name: 'LoginLogs',
        component: () => import('@/views/system/LoginLog.vue'),
        meta: { title: '登录日志', module: 'system' },
      },
      {
        path: '/system/teacher-profiles',
        name: 'TeacherProfiles',
        component: () => import('@/views/system/TeacherProfile.vue'),
        meta: { title: '教师档案', module: 'system' },
      },
      {
        path: '/system/monitor',
        name: 'Monitor',
        component: () => import('@/views/system/Monitor.vue'),
        meta: { title: '服务监控', module: 'system' },
      },
      {
        path: '/system/online-users',
        name: 'OnlineUsers',
        component: () => import('@/views/system/OnlineUser.vue'),
        meta: { title: '在线用户', module: 'system' },
      },
      {
        path: '/system/scheduler',
        name: 'Scheduler',
        component: () => import('@/views/system/Scheduler.vue'),
        meta: { title: '定时任务', module: 'system' },
      },
      {
        path: '/system/cache',
        name: 'Cache',
        component: () => import('@/views/system/Cache.vue'),
        meta: { title: '缓存监控', module: 'system' },
      },

      // ==================== 教务管理 ====================
      {
        path: '/edu/students',
        name: 'Students',
        component: () => import('@/views/edu/Student.vue'),
        meta: { title: '学生管理', module: 'edu' },
      },
      {
        path: '/edu/grades',
        name: 'Grades',
        component: () => import('@/views/edu/Grade.vue'),
        meta: { title: '年级管理', module: 'edu' },
      },
      {
        path: '/edu/classes',
        name: 'Classes',
        component: () => import('@/views/edu/Class.vue'),
        meta: { title: '班级管理', module: 'edu' },
      },
      {
        path: '/edu/courses',
        name: 'Courses',
        component: () => import('@/views/edu/Course.vue'),
        meta: { title: '课程管理', module: 'edu' },
      },
      {
        path: '/edu/scores',
        name: 'Scores',
        component: () => import('@/views/edu/Score.vue'),
        meta: { title: '成绩管理', module: 'edu' },
      },
      {
        path: '/edu/schedules',
        name: 'Schedules',
        component: () => import('@/views/edu/Schedule.vue'),
        meta: { title: '课表管理', module: 'edu' },
      },
      {
        path: '/edu/classrooms',
        name: 'Classrooms',
        component: () => import('@/views/edu/Classroom.vue'),
        meta: { title: '教室管理', module: 'edu' },
      },
      {
        path: '/edu/student-profiles',
        name: 'StudentProfiles',
        component: () => import('@/views/edu/StudentProfile.vue'),
        meta: { title: '学籍档案', module: 'edu' },
      },
      {
        path: '/edu/quality-records',
        name: 'QualityRecords',
        component: () => import('@/views/edu/QualityRecord.vue'),
        meta: { title: '综合素质', module: 'edu' },
      },
      {
        path: '/edu/teaching-plans',
        name: 'TeachingPlans',
        component: () => import('@/views/edu/TeachingPlan.vue'),
        meta: { title: '教学计划', module: 'edu' },
      },
      {
        path: '/edu/lesson-plans',
        name: 'LessonPlans',
        component: () => import('@/views/edu/LessonPlan.vue'),
        meta: { title: '教案管理', module: 'edu' },
      },
      {
        path: '/edu/research-projects',
        name: 'ResearchProjects',
        component: () => import('@/views/edu/Research.vue'),
        meta: { title: '教研项目', module: 'edu' },
      },

      // ==================== 资源管理 ====================
      {
        path: '/resource/list',
        name: 'Resources',
        component: () => import('@/views/resource/Resource.vue'),
        meta: { title: '资源列表', module: 'resource' },
      },
      {
        path: '/resource/favorites',
        name: 'Favorites',
        component: () => import('@/views/resource/Favorites.vue'),
        meta: { title: '我的收藏', module: 'resource' },
      },
      {
        path: '/resource/recommend',
        name: 'Recommend',
        component: () => import('@/views/resource/Recommend.vue'),
        meta: { title: '推荐资源', module: 'resource' },
      },

      // ==================== 考试管理 ====================
      {
        path: '/exam/list',
        name: 'Exams',
        component: () => import('@/views/exam/Exam.vue'),
        meta: { title: '考试管理', module: 'exam' },
      },

      // ==================== 考勤管理 ====================
      {
        path: '/attendance/list',
        name: 'Attendance',
        component: () => import('@/views/attendance/Attendance.vue'),
        meta: { title: '考勤记录', module: 'attendance' },
      },

      // ==================== 通知公告 ====================
      {
        path: '/notice/list',
        name: 'Notices',
        component: () => import('@/views/notice/Notice.vue'),
        meta: { title: '通知公告', module: 'notice' },
      },

      // ==================== 系统设置 ====================
      {
        path: '/settings',
        name: 'Settings',
        component: () => import('@/views/settings/Settings.vue'),
        meta: { title: '系统设置', module: 'settings' },
      },

      // ==================== AI 功能模块 ====================
      // 所有 AI 相关页面统一使用 /ai/ 路径前缀
      // 对应后端 API 前缀: /api/v1/ai/
      {
        path: '/ai/chat',
        name: 'AIChat',
        component: () => import('@/views/ai/Chat.vue'),
        meta: { title: 'AI 对话', module: 'ai', aiFeature: true },
      },
      {
        path: '/ai/learning-agent',
        name: 'LearningAgent',
        component: () => import('@/views/ai/LearningAgent.vue'),
        meta: { title: '学习助手', module: 'ai', aiFeature: true },
      },
      {
        path: '/ai/learning-path',
        name: 'LearningPath',
        component: () => import('@/views/ai/LearningPath.vue'),
        meta: { title: '学习路径', module: 'ai', aiFeature: true },
      },
      {
        path: '/ai/learning-records',
        name: 'LearningRecords',
        component: () => import('@/views/ai/LearningRecord.vue'),
        meta: { title: '学习记录', module: 'ai', aiFeature: true },
      },
      {
        path: '/ai/teacher-assistant',
        name: 'TeacherAssistant',
        component: () => import('@/views/ai/TeacherAssistant.vue'),
        meta: { title: '教师助手', module: 'ai', aiFeature: true },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router
