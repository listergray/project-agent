import { request } from '@/utils/request'

export interface Inventory {
  id?: number
  code: string
  content: string
  type: string
  productId?: number
  stock: number
  usedCount: number
  status: string
  productName?: string
  createdAt?: number
}

export function pageInventory(params: {
  pageNo?: number
  pageSize?: number
  keyword?: string
  type?: string
  productId?: number
}) {
  return request<{ list: Inventory[]; total: number }>({
    url: '/inventory/page',
    method: 'get',
    params
  })
}

export function listInventory(params?: { productId?: number }) {
  return request<Inventory[]>({
    url: '/inventory/list',
    method: 'get',
    params
  })
}

export function getInventory(id: number) {
  return request<Inventory>({
    url: `/inventory/${id}`,
    method: 'get'
  })
}

export function createInventory(data: Inventory) {
  return request({
    url: '/inventory',
    method: 'post',
    data
  })
}

export function batchCreateInventory(data: { codes: string[]; content: string; type: string; productId?: number }) {
  return request({
    url: '/inventory/batch',
    method: 'post',
    data
  })
}

export function updateInventory(id: number, data: Partial<Inventory>) {
  return request({
    url: `/inventory/${id}`,
    method: 'put',
    data
  })
}

export function deleteInventory(id: number) {
  return request({
    url: `/inventory/${id}`,
    method: 'delete'
  })
}

export function batchDeleteInventory(ids: number[]) {
  return request({
    url: '/inventory/batch',
    method: 'delete',
    data: ids
  })
}
