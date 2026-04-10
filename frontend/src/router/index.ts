import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import Layout from '@/views/Layout.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue')
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('@/views/system/Dashboard.vue')
      },
      {
        path: '/system/users',
        name: 'Users',
        component: () => import('@/views/system/User.vue')
      },
      {
        path: '/system/roles',
        name: 'Roles',
        component: () => import('@/views/system/Role.vue')
      },
      {
        path: '/system/departments',
        name: 'Departments',
        component: () => import('@/views/system/Department.vue')
      },
      {
        path: '/system/logs/operation',
        name: 'OperationLogs',
        component: () => import('@/views/system/OperationLog.vue')
      },
      {
        path: '/system/logs/login',
        name: 'LoginLogs',
        component: () => import('@/views/system/LoginLog.vue')
      },
      {
        path: '/edu/students',
        name: 'Students',
        component: () => import('@/views/edu/Student.vue')
      },
      {
        path: '/edu/grades',
        name: 'Grades',
        component: () => import('@/views/edu/Grade.vue')
      },
      {
        path: '/edu/classes',
        name: 'Classes',
        component: () => import('@/views/edu/Class.vue')
      },
      {
        path: '/edu/courses',
        name: 'Courses',
        component: () => import('@/views/edu/Course.vue')
      },
      {
        path: '/edu/scores',
        name: 'Scores',
        component: () => import('@/views/edu/Score.vue')
      },
      {
        path: '/edu/schedules',
        name: 'Schedules',
        component: () => import('@/views/edu/Schedule.vue')
      },
      {
        path: '/edu/classrooms',
        name: 'Classrooms',
        component: () => import('@/views/edu/Classroom.vue')
      },
      {
        path: '/resource/list',
        name: 'Resources',
        component: () => import('@/views/resource/Resource.vue')
      },
      {
        path: '/resource/favorites',
        name: 'Favorites',
        component: () => import('@/views/resource/Favorites.vue')
      },
      {
        path: '/resource/recommend',
        name: 'Recommend',
        component: () => import('@/views/resource/Recommend.vue')
      },
      {
        path: '/ai/chat',
        name: 'AIChat',
        component: () => import('@/views/ai/Chat.vue')
      },
      {
        path: '/exam/list',
        name: 'Exams',
        component: () => import('@/views/exam/Exam.vue')
      },
      {
        path: '/attendance/list',
        name: 'Attendance',
        component: () => import('@/views/attendance/Attendance.vue')
      },
      {
        path: '/notice/list',
        name: 'Notices',
        component: () => import('@/views/notice/Notice.vue')
      },
      {
        path: '/settings',
        name: 'Settings',
        component: () => import('@/views/settings/Settings.vue')
      },
      {
        path: '/edu/student-profiles',
        name: 'StudentProfiles',
        component: () => import('@/views/edu/StudentProfile.vue')
      },
      {
        path: '/edu/quality-records',
        name: 'QualityRecords',
        component: () => import('@/views/edu/QualityRecord.vue')
      },
      {
        path: '/system/teacher-profiles',
        name: 'TeacherProfiles',
        component: () => import('@/views/system/TeacherProfile.vue')
      },
      {
        path: '/edu/teaching-plans',
        name: 'TeachingPlans',
        component: () => import('@/views/edu/TeachingPlan.vue')
      },
      {
        path: '/edu/lesson-plans',
        name: 'LessonPlans',
        component: () => import('@/views/edu/LessonPlan.vue')
      },
      {
        path: '/edu/research-projects',
        name: 'ResearchProjects',
        component: () => import('@/views/edu/Research.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
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