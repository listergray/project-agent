import { request } from '@/utils/request'

export interface LoginResponse {
  token: string
  userInfo: any
}

export interface RefreshTokenResponse {
  token: string
}

export function login(username: string, password: string) {
  return request<LoginResponse>({
    url: '/auth/login',
    method: 'post',
    data: { username, password }
  })
}

export function logout() {
  return request<void>({
    url: '/auth/logout',
    method: 'post'
  })
}

export function getUserInfo() {
  return request<any>({
    url: '/auth/info',
    method: 'get'
  })
}

export function changePassword(oldPassword: string, newPassword: string) {
  return request<void>({
    url: '/auth/change-password',
    method: 'post',
    data: { oldPassword, newPassword }
  })
}

export function refreshToken() {
  return request<RefreshTokenResponse>({
    url: '/auth/refresh-token',
    method: 'post'
  })
}
