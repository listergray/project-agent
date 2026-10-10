import { request } from '@/utils/request'

export interface DeliveryRule {
  id?: number
  name: string
  accountId?: number
  productId?: number
  triggerType: string
  triggerKeywords?: string
  deliveryContent: string
  inventoryId?: number
  autoConfirm?: number
  delaySeconds?: number
  priority: number
  enabled: number
  createdAt?: number
}

export interface DeliveryLog {
  id?: number
  accountId: number
  accountNickname?: string
  ruleId?: number
  ruleName?: string
  conversationId: string
  buyerId?: string
  buyerNick?: string
  itemId?: string
  itemName?: string
  orderId?: string
  deliveryContent: string
  inventoryCode?: string
  inventoryId?: number
  consignStatus?: string
  status: string
  errorMsg?: string
  createdAt?: number
}

export function pageDeliveryRule(params: {
  pageNo?: number
  pageSize?: number
  keyword?: string
  accountId?: number
}) {
  return request<{ list: DeliveryRule[]; total: number }>({
    url: '/delivery/rule/page',
    method: 'get',
    params
  })
}

export function listDeliveryRule(params?: { accountId?: number }) {
  return request<DeliveryRule[]>({
    url: '/delivery/rule/list',
    method: 'get',
    params
  })
}

export function getDeliveryRule(id: number) {
  return request<DeliveryRule>({
    url: `/delivery/rule/${id}`,
    method: 'get'
  })
}

export function createDeliveryRule(data: DeliveryRule) {
  return request({
    url: '/delivery/rule',
    method: 'post',
    data
  })
}

export function updateDeliveryRule(id: number, data: Partial<DeliveryRule>) {
  return request({
    url: `/delivery/rule/${id}`,
    method: 'put',
    data
  })
}

export function deleteDeliveryRule(id: number) {
  return request({
    url: `/delivery/rule/${id}`,
    method: 'delete'
  })
}

export function pageDeliveryLog(params: {
  pageNo?: number
  pageSize?: number
  keyword?: string
  accountId?: number
  status?: string
}) {
  return request<{ list: DeliveryLog[]; total: number }>({
    url: '/delivery/log/page',
    method: 'get',
    params
  })
}

export function getDeliveryLog(id: number) {
  return request<DeliveryLog>({
    url: `/delivery/log/${id}`,
    method: 'get'
  })
}

export function resendDeliveryLog(id: number) {
  return request({
    url: `/delivery/log/${id}/resend`,
    method: 'post'
  })
}
