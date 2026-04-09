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