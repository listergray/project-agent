import { request } from '@/utils/request'
import type { PageResult } from '@/types/common'

export interface SysLog {
  id?: number
  operator?: string
  action: string
  method?: string
  params?: string
  result?: string
  ip?: string
  durationMs?: number
  errorMsg?: string
  createdAt?: number
}

export function pageLogs(params: {
  pageNo?: number
  pageSize?: number
  keyword?: string
  action?: string
}) {
  return request<PageResult<SysLog>>({
    url: '/system/logs',
    method: 'get',
    params
  })
}

export function clearAllLogs() {
  return request<void>({
    url: '/system/logs',
    method: 'delete'
  })
}
