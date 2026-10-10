import { request } from '@/utils/request'
import type { PageResult } from '@/types/common'

export interface Account {
  id?: number
  nickname?: string
  userId?: string
  userNick?: string
  avatar?: string
  deviceId?: string
  status?: string  // OFFLINE / CONNECTING / ONLINE / ERROR / NEED_VERIFY / EXPIRED / DISABLED
  lastError?: string
  lastLoginAt?: number
  lastKeepaliveAt?: number
  autoStart?: number
  createdAt?: number
  updatedAt?: number
}

export interface AccountStatus {
  id: number
  status: string
  lastError: string | null
  lastKeepaliveAt: number | null
  lastLoginAt: number | null
  hasCookie: boolean
  hasWsToken: boolean
  userId?: string
}

export interface WsStatus {
  connected: boolean
  registered: boolean
  lastHeartbeatAt?: number
  reconnectAttempts?: number
}

export function pageAccounts(params: { pageNo?: number; pageSize?: number; keyword?: string }) {
  return request<PageResult<Account>>({
    url: '/account/page',
    method: 'get',
    params
  })
}

export function listAllAccounts() {
  return request<Account[]>({
    url: '/account/all',
    method: 'get'
  })
}

export function getAccount(id: number) {
  return request<Account>({
    url: `/account/${id}`,
    method: 'get'
  })
}

export function getAccountStatus(id: number) {
  return request<AccountStatus>({
    url: `/account/${id}/status`,
    method: 'get'
  })
}

export function createAccount(data: Partial<Account>) {
  return request<Account>({
    url: '/account',
    method: 'post',
    data
  })
}

export function updateAccount(id: number, data: Partial<Account>) {
  return request<void>({
    url: `/account/${id}`,
    method: 'put',
    data
  })
}

export function updateAccountCookie(id: number, cookie: string) {
  return request<void>({
    url: `/account/${id}/cookie`,
    method: 'put',
    data: { cookie }
  })
}

export function deleteAccount(id: number) {
  return request<void>({
    url: `/account/${id}`,
    method: 'delete'
  })
}

export function connectAccount(id: number) {
  return request<void>({
    url: `/account/${id}/connect`,
    method: 'post'
  })
}

export function disconnectAccount(id: number) {
  return request<void>({
    url: `/account/${id}/disconnect`,
    method: 'post'
  })
}

export function reconnectAccount(id: number) {
  return request<void>({
    url: `/account/${id}/reconnect`,
    method: 'post'
  })
}

export function getWsStatus(id: number) {
  return request<WsStatus>({
    url: `/account/${id}/ws-status`,
    method: 'get'
  })
}

export function getAllWsStatus() {
  return request<Record<number, WsStatus>>({
    url: '/account/ws-status',
    method: 'get'
  })
}
