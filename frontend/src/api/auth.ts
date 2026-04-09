import request from '@/utils/request'

export interface LoginParams {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token?: string
  token_type: string
  expires_in: number
  user: {
    id: string
    username: string
    email?: string
    real_name?: string
    avatar?: string
    status: string
  }
}

export function login(data: LoginParams) {
  return request.post<any, LoginResponse>('/auth/login', data)
}

export function logout() {
  return request.post('/auth/logout')
}

export function getUserInfo() {
  return request.get('/auth/me')
}

export function refreshToken(refresh_token: string) {
  return request.post('/auth/refresh', { refresh_token })
}