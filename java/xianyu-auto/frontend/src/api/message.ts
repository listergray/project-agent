import { request } from '@/utils/request'
import type { PageResult } from '@/types/common'

export interface ChatMessage {
  id?: number
  accountId: number
  conversationId: string
  sender: string  // BUYER / SELLER / SYSTEM
  senderId?: string
  senderNick?: string
  itemId?: string
  msgType: string  // TEXT / IMAGE / ORDER / SYSTEM
  content?: string
  rawData?: string
  readStatus?: number
  createdAt?: number
}

export interface Conversation {
  conversationId: string
  accountId: number
  sender: string
  senderId?: string
  senderNick?: string
  itemId?: string
  lastContent?: string
  lastMsgType?: string
  lastMsgAt: number
  unreadCount: number
}

export function pageMessages(params: {
  pageNo?: number
  pageSize?: number
  accountId?: number
  conversationId?: string
  startTime?: number
  endTime?: number
}) {
  return request<PageResult<ChatMessage>>({
    url: '/message/page',
    method: 'get',
    params
  })
}

export function listConversations(accountId: number) {
  return request<Conversation[]>({
    url: `/message/conversations/${accountId}`,
    method: 'get'
  })
}

export function markConversationRead(accountId: number, conversationId: string) {
  return request<void>({
    url: `/message/read/${accountId}`,
    method: 'put',
    params: { conversationId }
  })
}

export function sendMessage(data: {
  accountId: number
  conversationId: string
  content: string
  itemId?: string
}) {
  return request<void>({
    url: '/message/send',
    method: 'post',
    data
  })
}
