import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as apiLogin, logout as apiLogout, getUserInfo, refreshToken as apiRefreshToken } from '@/api/auth'

export interface UserInfo {
  id: number
  username: string
  nickname?: string
  email?: string
  phone?: string
  role: string
  status?: number
  lastLoginAt?: number
  lastLoginIp?: string
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem('xianyu_token') || '')
  const userInfo = ref<UserInfo | null>(null)
  const loginTime = ref<number>(parseInt(localStorage.getItem('xianyu_login_time') || '0'))

  async function login(username: string, password: string) {
    const res = await apiLogin(username, password)
    token.value = res.token
    userInfo.value = res.userInfo
    loginTime.value = Date.now()
    localStorage.setItem('xianyu_token', res.token)
    localStorage.setItem('xianyu_login_time', String(Date.now()))
    return res
  }

  async function fetchUserInfo() {
    if (!token.value) return null
    const info = await getUserInfo()
    userInfo.value = info
    return info
  }

  async function refreshToken() {
    const res = await apiRefreshToken()
    token.value = res.token
    loginTime.value = Date.now()
    localStorage.setItem('xianyu_token', res.token)
    localStorage.setItem('xianyu_login_time', String(Date.now()))
    return res
  }

  async function logout() {
    try {
      await apiLogout()
    } catch (e) {
      // 忽略登出错误
    }
    token.value = ''
    userInfo.value = null
    loginTime.value = 0
    localStorage.removeItem('xianyu_token')
    localStorage.removeItem('xianyu_login_time')
  }

  function isLoggedIn() {
    return !!token.value
  }

  function isAdmin() {
    return userInfo.value?.role === 'ADMIN'
  }

  function getTokenRemainingSeconds() {
    if (!loginTime.value) return 0
    const elapsed = (Date.now() - loginTime.value) / 1000
    return Math.max(0, 7200 - elapsed) // 2小时 = 7200秒
  }

  return {
    token,
    userInfo,
    loginTime,
    login,
    fetchUserInfo,
    refreshToken,
    logout,
    isLoggedIn,
    isAdmin,
    getTokenRemainingSeconds
  }
})
