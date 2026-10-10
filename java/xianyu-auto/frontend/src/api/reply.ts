import { request } from '@/utils/request'

export interface KeywordRule {
  id?: number
  accountId: number
  itemId?: string
  keyword: string
  matchType: string
  replyContent: string
  priority: number
  status: string
  createdAt?: number
  updatedAt?: number
}

export interface ReplySettings {
  enabled: boolean
  defaultContent: string
  aiEnabled: boolean
  aiProvider: string
  aiSystemPrompt: string
  delayMinSec?: number
  delayMaxSec?: number
  contextWindow?: number
  yamlDefaultProvider?: string
  providers?: Record<string, { configured: boolean; model: string; baseUrl: string }>
}

export function pageKeywordRule(params: {
  pageNo?: number
  pageSize?: number
  keyword?: string
  accountId?: number
  matchType?: string
  status?: string
}) {
  return request<{ list: KeywordRule[]; total: number }>({
    url: '/reply/keyword/page',
    method: 'get',
    params
  })
}

export function createKeywordRule(data: KeywordRule) {
  return request({
    url: '/reply/keyword',
    method: 'post',
    data
  })
}

export function updateKeywordRule(id: number, data: Partial<KeywordRule>) {
  return request({
    url: `/reply/keyword/${id}`,
    method: 'put',
    data
  })
}

export function deleteKeywordRule(id: number) {
  return request({
    url: `/reply/keyword/${id}`,
    method: 'delete'
  })
}

export function updateKeywordRuleStatus(id: number, status: string) {
  return request({
    url: `/reply/keyword/${id}/status`,
    method: 'put',
    params: { status }
  })
}

export function getReplySettings() {
  return request<ReplySettings>({
    url: '/reply/config',
    method: 'get'
  })
}

export function saveReplySettings(data: Partial<ReplySettings>) {
  return request({
    url: '/reply/config',
    method: 'put',
    data
  })
}

export function testAi(prompt?: string) {
  return request<{ answer: string }>({
    url: '/reply/config/ai/test',
    method: 'post',
    data: { prompt }
  })
}
