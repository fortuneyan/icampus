import request from '@/utils/request'

// 在线用户统计
export interface OnlineUserStats {
  online_count: number
  active_count: number
  today_login: number
  peak_count: number
}

// 在线用户信息
export interface OnlineUser {
  user_id: number
  username: string
  real_name: string
  role: string
  ip_address: string
  login_time: string
  last_activity: string
  status: 'active' | 'idle'
}

// 获取在线用户列表
export function getOnlineUsers(params?: {
  page?: number
  page_size?: number
}) {
  return request<{
    data: OnlineUser[]
    total: number
    stats: OnlineUserStats
  }>({
    url: '/system/online-users',
    method: 'get',
    params
  })
}

// 获取在线用户统计
export function getOnlineUserStats() {
  return request<OnlineUserStats>({
    url: '/system/online-users/stats',
    method: 'get'
  })
}

// 强制用户下线
export function forceUserLogout(userId: number) {
  return request({
    url: `/system/online-users/${userId}/force-logout`,
    method: 'post'
  })
}

// 获取用户会话列表
export function getUserSessions(userId: number) {
  return request({
    url: `/system/online-users/${userId}/sessions`,
    method: 'get'
  })
}
