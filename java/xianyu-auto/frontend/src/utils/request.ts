import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/modules/user'
import router from '@/router'

const service: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截：注入 token
service.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers['Authorization'] = userStore.token
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截：统一处理 CommonResult
service.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res && typeof res === 'object' && 'code' in res) {
      if (res.code === 0) {
        return res.data
      }
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || 'Error'))
    }
    return res
  },
  (error) => {
    const status = error.response?.status
    const data = error.response?.data
    const message = data?.message || error.message || '网络异常'
    const url = error.response?.config?.url || ''
    
    if (status === 401) {
      // 避免 logout 请求再次触发 401 处理导致循环
      if (url.includes('/auth/logout')) {
        // 静默处理，直接拒绝，不弹出消息
        return Promise.reject(error)
      }
      const userStore = useUserStore()
      // 避免多次触发 logout
      if (userStore.isLoggedIn()) {
        userStore.logout().catch(() => {})
        ElMessage.error('登录已过期，请重新登录')
        router.push('/login')
      }
    } else if (status === 403) {
      ElMessage.error('无权限访问')
    } else {
      ElMessage.error(message)
    }
    return Promise.reject(error)
  }
)

export function request<T = any>(config: AxiosRequestConfig): Promise<T> {
  return service(config) as Promise<T>
}

export default service
