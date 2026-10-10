import { request } from '@/utils/request'

export interface TradeOrder {
  id?: number
  accountId: number
  orderId: string
  itemId?: string
  itemTitle?: string
  buyerId?: string
  buyerNick?: string
  conversationId?: string
  status: string
  payAmount?: number
  paidAt?: number
  shippedAt?: number
  consignStatus?: string
  createdAt?: number
  updatedAt?: number
}

export function pageOrder(params: {
  pageNo?: number
  pageSize?: number
  accountId?: number
  status?: string
  keyword?: string
}) {
  return request<{ list: TradeOrder[]; total: number }>({
    url: '/order/page',
    method: 'get',
    params
  })
}

export function getOrder(id: number) {
  return request<TradeOrder>({
    url: `/order/${id}`,
    method: 'get'
  })
}

export function consignOrder(id: number) {
  return request<{ success: boolean; consignStatus: string }>({
    url: `/order/${id}/consign`,
    method: 'post'
  })
}

export function syncOrders(accountId: number) {
  return request<{ upserted: number; errors: number; pages: number }>({
    url: `/order/sync/${accountId}`,
    method: 'post'
  })
}
