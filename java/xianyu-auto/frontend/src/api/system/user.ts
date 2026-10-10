import { request } from '@/utils/request'
import type { PageResult } from '@/types/common'

export interface SysUser {
  id?: number
  username: string
  nickname?: string
  email?: string
  phone?: string
  role: string
  status?: number
  lastLoginAt?: number
  lastLoginIp?: string
  createdAt?: number
  updatedAt?: number
  passwordHash?: string  // 创建/重置时作为明文密码传递
}

export function pageUsers(params: { pageNo?: number; pageSize?: number; keyword?: string }) {
  return request<PageResult<SysUser>>({
    url: '/system/users',
    method: 'get',
    params
  })
}

export function createUser(data: SysUser) {
  return request<void>({
    url: '/system/users',
    method: 'post',
    data
  })
}

export function updateUser(id: number, data: SysUser) {
  return request<void>({
    url: `/system/users/${id}`,
    method: 'put',
    data
  })
}

export function deleteUsers(ids: number[]) {
  return request<void>({
    url: '/system/users',
    method: 'delete',
    data: ids
  })
}

export function resetPassword(id: number, newPassword: string) {
  return request<void>({
    url: `/system/users/${id}/reset-password`,
    method: 'put',
    data: { newPassword }
  })
}

export function changeUserStatus(id: number, status: number) {
  return request<void>({
    url: `/system/users/${id}/status`,
    method: 'put',
    data: { status }
  })
}
