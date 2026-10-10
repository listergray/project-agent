import { request } from '@/utils/request'

export interface SysConfig {
  id?: number
  configKey: string
  configValue?: string
  configGroup?: string
  description?: string
  createdAt?: number
  updatedAt?: number
}

export function listConfigs(group?: string) {
  return request<SysConfig[]>({
    url: '/system/configs',
    method: 'get',
    params: { group }
  })
}

export function getConfigsByGroup(group: string) {
  return request<Record<string, string>>({
    url: `/system/configs/group/${group}`,
    method: 'get'
  })
}

export function saveConfig(data: SysConfig) {
  return request<void>({
    url: '/system/configs',
    method: 'post',
    data
  })
}

export function saveBatchConfigs(configs: SysConfig[]) {
  return request<void>({
    url: '/system/configs/batch',
    method: 'post',
    data: configs
  })
}

export function deleteConfig(key: string) {
  return request<void>({
    url: `/system/configs/${key}`,
    method: 'delete'
  })
}
