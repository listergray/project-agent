import { request } from '@/utils/request'

export interface Product {
  id?: number
  accountId?: number
  name: string
  title?: string
  xianyuItemId?: string
  description?: string
  price?: number
  originalPrice?: number
  stockQty?: number
  shelfStatus?: string
  imagesJson?: string
  deliveryContent?: string
  defaultInventoryId?: number
  autoDelivery: number
  status: string
  syncStatus?: string
  lastSyncedAt?: number
  totalStock?: number
  usedCount?: number
  createdAt?: number
  updatedAt?: number
}

export function pageProduct(params: {
  pageNo?: number
  pageSize?: number
  keyword?: string
  accountId?: number
  shelfStatus?: string
}) {
  return request<{ list: Product[]; total: number }>({
    url: '/product/page',
    method: 'get',
    params
  })
}

export function listProduct(params?: { accountId?: number }) {
  return request<Product[]>({
    url: '/product/list',
    method: 'get',
    params
  })
}

export function getProduct(id: number) {
  return request<Product>({
    url: `/product/${id}`,
    method: 'get'
  })
}

export function createProduct(data: Product) {
  return request({
    url: '/product',
    method: 'post',
    data
  })
}

export function updateProduct(id: number, data: Partial<Product>) {
  return request({
    url: `/product/${id}`,
    method: 'put',
    data
  })
}

export function deleteProduct(id: number) {
  return request({
    url: `/product/${id}`,
    method: 'delete'
  })
}

export function syncProducts(accountId: number) {
  return request<{ upserted: number; errors: number; pages: number }>({
    url: `/product/sync/${accountId}`,
    method: 'post'
  })
}

export function setProductShelf(id: number, onSale: boolean, accountId?: number) {
  return request({
    url: `/product/${id}/shelf`,
    method: 'post',
    params: { onSale, accountId }
  })
}

export function copyProduct(id: number) {
  return request<Product>({
    url: `/product/${id}/copy`,
    method: 'post'
  })
}

export function refreshProductDetail(id: number, accountId?: number) {
  return request({
    url: `/product/${id}/refresh-detail`,
    method: 'post',
    params: { accountId }
  })
}

export function migrateProducts(data: {
  fromAccountId: number
  toAccountId: number
  productIds: number[]
}) {
  return request<{ success: number; failed: number; messages: string[] }>({
    url: '/product/migrate',
    method: 'post',
    data
  })
}
