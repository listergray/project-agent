import type {
  ChatResp,
  CopilotResp,
  HealthResp,
  ProjectFields,
  ProjectRecord,
  ProjectStats,
} from '../types'

async function parseError(r: Response): Promise<string> {
  try {
    const j = await r.json()
    if (typeof j.detail === 'string') return j.detail
    if (j.detail) return JSON.stringify(j.detail)
    return r.statusText || `HTTP ${r.status}`
  } catch {
    return r.statusText || `HTTP ${r.status}`
  }
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, init)
  if (!r.ok) throw new Error(await parseError(r))
  return r.json() as Promise<T>
}

function metaFromData(data: Record<string, unknown>): Omit<ChatResp, 'answer'> {
  const needRagRaw = data.need_rag
  let need_rag: boolean | null = null
  if (typeof needRagRaw === 'boolean') need_rag = needRagRaw
  else if (needRagRaw === 'true' || needRagRaw === 1) need_rag = true
  else if (needRagRaw === 'false' || needRagRaw === 0) need_rag = false

  return {
    session_id: String(data.session_id || ''),
    intent: String(data.intent || 'MIXED'),
    tool_calls: (data.tool_calls as Array<Record<string, unknown>>) || [],
    sources: (data.sources as string[]) || [],
    elapsed_ms: Number(data.elapsed_ms || 0),
    need_rag,
    self_rag_route_reason:
      data.self_rag_route_reason == null ? null : String(data.self_rag_route_reason),
    self_rag_retries: Number(data.self_rag_retries || 0),
    self_rag_grade: (data.self_rag_grade as Record<string, unknown>) || null,
    multi_queries: (data.multi_queries as string[]) || [],
    retrieval_paths: (data.retrieval_paths as Record<string, unknown>) || null,
    faithfulness_score:
      data.faithfulness_score == null ? null : Number(data.faithfulness_score),
    faithfulness: (data.faithfulness as Record<string, unknown>) || null,
    interrupted: Boolean(data.interrupted),
    interrupt_payload: (data.interrupt_payload as Record<string, unknown>) || null,
    need_human_review: Boolean(data.need_human_review),
  }
}

type StreamHandlers = {
  onStatus?: (msg: string) => void
  onMeta?: (meta: Omit<ChatResp, 'answer'>) => void
  onToken?: (text: string) => void
  onDone?: () => void
  onInterrupted?: (meta: Omit<ChatResp, 'answer'>) => void
  onError?: (detail: string) => void
}

async function consumeSse(
  url: string,
  body: unknown,
  handlers: StreamHandlers,
  signal?: AbortSignal,
) {
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify(body),
    signal,
  })
  if (!r.ok) throw new Error(await parseError(r))
  if (!r.body) throw new Error('浏览器不支持流式响应')

  const reader = r.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buf = ''
  let eventName = 'message'

  const dispatch = (name: string, dataRaw: string) => {
    let data: Record<string, unknown> = {}
    try {
      data = JSON.parse(dataRaw) as Record<string, unknown>
    } catch {
      data = { text: dataRaw }
    }
    if (name === 'status') {
      handlers.onStatus?.(String(data.message || data.stage || '处理中…'))
    } else if (name === 'meta') {
      handlers.onMeta?.(metaFromData(data))
    } else if (name === 'token') {
      handlers.onToken?.(String(data.text || ''))
    } else if (name === 'interrupted') {
      handlers.onInterrupted?.(metaFromData(data))
    } else if (name === 'done') {
      handlers.onDone?.()
    } else if (name === 'error') {
      const detail = data.detail
      handlers.onError?.(
        typeof detail === 'string' ? detail : JSON.stringify(detail ?? data),
      )
    }
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true })
    const blocks = buf.split('\n\n')
    buf = blocks.pop() || ''
    for (const block of blocks) {
      const lines = block.split('\n')
      const dataLines: string[] = []
      for (const line of lines) {
        if (line.startsWith('event:')) eventName = line.slice(6).trim()
        else if (line.startsWith('data:')) dataLines.push(line.slice(5).trimStart())
      }
      if (dataLines.length) {
        dispatch(eventName, dataLines.join('\n'))
        eventName = 'message'
      }
    }
  }
}

export const api = {
  health: () => request<HealthResp>('/api/v1/health', { cache: 'no-store' }),

  projectStats: () => request<ProjectStats>('/api/v1/projects/stats'),

  listProjects: (status?: string) =>
    request<{ items: ProjectRecord[]; total: number }>(
      `/api/v1/projects${status ? `?status=${encodeURIComponent(status)}` : ''}`,
    ),

  createProject: (payload: ProjectFields) =>
    request<ProjectRecord>('/api/v1/projects', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),

  updateProject: (id: string, payload: ProjectFields) =>
    request<ProjectRecord>(`/api/v1/projects/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),

  submitProject: (id: string) =>
    request<ProjectRecord>(`/api/v1/projects/${id}/submit`, { method: 'POST' }),

  reviewProject: (id: string, body: { action: string; reviewer: string; comment: string }) =>
    request<ProjectRecord>(`/api/v1/projects/${id}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),

  parseProject: async (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return request<{
      fields: ProjectFields
      confidence: number
      method: string
      filename: string
    }>('/api/v1/projects/parse', { method: 'POST', body: fd })
  },

  ragPresets: () => request<Array<{ tag: string; query: string }>>('/api/v1/rag/presets'),

  ragChat: (query: string, session_id?: string) =>
    request<ChatResp>('/api/v1/rag/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, session_id }),
    }),

  ragChatStream: (
    query: string,
    handlers: StreamHandlers,
    opts?: { session_id?: string; signal?: AbortSignal },
  ) =>
    consumeSse(
      '/api/v1/rag/chat/stream',
      { query, session_id: opts?.session_id },
      handlers,
      opts?.signal,
    ),

  ragChatResumeStream: (
    body: { session_id: string; action: string; rewritten_query?: string },
    handlers: StreamHandlers,
    opts?: { signal?: AbortSignal },
  ) => consumeSse('/api/v1/rag/chat/resume/stream', body, handlers, opts?.signal),

  ragPreview: async (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return request<Record<string, unknown>>('/api/v1/rag/preview', { method: 'POST', body: fd })
  },

  ragRollback: (item_pk: string) =>
    request<Record<string, unknown>>('/api/v1/rag/rollback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_pk }),
    }),

  ragChunks: (item_pk: string) =>
    request<{ total: number; chunks: unknown[] }>(
      `/api/v1/rag/chunks/${encodeURIComponent(item_pk)}?max_chars=10&limit=20000`,
    ),

  copilotRun: (requirement_doc?: string) =>
    request<CopilotResp>('/api/v1/copilot/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ requirement_doc: requirement_doc || null }),
    }),
}
