<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '../api/client'
import type { ChatResp } from '../types'
import brandMark from '../assets/brand-mark.svg'
import './ChatPage.css'

type Msg =
  | { role: 'user'; text: string }
  | { role: 'bot'; data: ChatResp; streaming?: boolean }
  | { role: 'typing'; text?: string }
  | {
      role: 'hitl'
      session_id: string
      payload: Record<string, unknown>
      meta: Omit<ChatResp, 'answer'>
    }

const QUICK = [
  { label: 'FS-2024-0876 库存', q: 'FS-2024-0876 现在有多少库存？单价和总价是多少？' },
  { label: '固定资产入库流程', q: '固定资产入库的完整流程是什么？' },
  { label: '最新审批项目', q: '最近审批通过的项目有哪些？' },
]

const messages = ref<Msg[]>([])
const query = ref('')
const err = ref('')
const sending = ref(false)
const health = ref('检查中…')
const healthOk = ref(true)
const presets = ref<Array<{ tag: string; query: string }>>([])
const sessionId = ref<string | undefined>()
const rewriteDraft = ref('')
const boxRef = ref<HTMLElement | null>(null)
let abort: AbortController | null = null
let healthTimer: ReturnType<typeof setInterval> | null = null

const empty = computed(() => messages.value.length === 0)

onMounted(() => {
  const check = () => {
    api
      .health()
      .then((j) => {
        const m = j.milvus || {}
        if (m.kb_chunks != null && m.kb_item_names != null) {
          health.value = `Milvus · ${m.kb_item_names} 手册 / ${m.kb_chunks} chunks`
          healthOk.value = true
        } else {
          health.value = 'Milvus 未就绪'
          healthOk.value = false
        }
      })
      .catch(() => {
        health.value = '服务未连接'
        healthOk.value = false
      })
  }
  check()
  healthTimer = setInterval(check, 8000)
  api.ragPresets().then((p) => (presets.value = p)).catch(() => {})
})

onUnmounted(() => {
  abort?.abort()
  if (healthTimer) clearInterval(healthTimer)
})

async function scrollBottom() {
  await nextTick()
  if (boxRef.value) boxRef.value.scrollTop = boxRef.value.scrollHeight
}

function applyMetaHandlers(gotMeta: { v: boolean }) {
  return {
    onStatus: (msg: string) => {
      const next = [...messages.value]
      const last = next[next.length - 1]
      if (last?.role === 'typing') next[next.length - 1] = { role: 'typing', text: msg }
      messages.value = next
      scrollBottom()
    },
    onMeta: (meta: Omit<ChatResp, 'answer'>) => {
      gotMeta.v = true
      if (meta.session_id) sessionId.value = meta.session_id
      messages.value = [
        ...messages.value.filter((x) => x.role !== 'typing'),
        { role: 'bot', streaming: true, data: { ...meta, answer: '' } },
      ]
      scrollBottom()
    },
    onToken: (piece: string) => {
      const next = [...messages.value]
      const last = next[next.length - 1]
      if (last?.role === 'bot') {
        next[next.length - 1] = {
          ...last,
          streaming: true,
          data: { ...last.data, answer: last.data.answer + piece },
        }
        messages.value = next
        scrollBottom()
      }
    },
    onInterrupted: (meta: Omit<ChatResp, 'answer'>) => {
      gotMeta.v = true
      if (meta.session_id) sessionId.value = meta.session_id
      rewriteDraft.value = String(meta.interrupt_payload?.suggested_query || '')
      messages.value = [
        ...messages.value.filter((x) => x.role !== 'typing' && x.role !== 'hitl'),
        {
          role: 'hitl',
          session_id: meta.session_id,
          payload: meta.interrupt_payload || {},
          meta,
        },
      ]
      scrollBottom()
    },
    onDone: () => {
      const next = [...messages.value]
      const last = next[next.length - 1]
      if (last?.role === 'bot') next[next.length - 1] = { ...last, streaming: false }
      messages.value = next
    },
    onError: (detail: string) => {
      messages.value = messages.value.filter((x) => x.role !== 'typing')
      err.value = '请求失败：' + detail
    },
  }
}

async function send(text?: string) {
  const q = (text || query.value).trim()
  if (!q || sending.value) return
  err.value = ''
  query.value = ''
  sending.value = true
  abort?.abort()
  const ctrl = new AbortController()
  abort = ctrl
  const timer = setTimeout(() => ctrl.abort(), 180000)

  messages.value = [...messages.value, { role: 'user', text: q }, { role: 'typing', text: '检索与推理中…' }]
  scrollBottom()

  const gotMeta = { v: false }
  try {
    await api.ragChatStream(q, applyMetaHandlers(gotMeta), {
      session_id: sessionId.value,
      signal: ctrl.signal,
    })
    if (!gotMeta.v) messages.value = messages.value.filter((x) => x.role !== 'typing')
  } catch (e) {
    messages.value = messages.value.filter((x) => x.role !== 'typing')
    if ((e as Error).name === 'AbortError') err.value = '请求超时或已取消'
    else err.value = '请求失败：' + (e as Error).message
  } finally {
    clearTimeout(timer)
    sending.value = false
  }
}

async function resumeHitl(action: 'approve' | 'rewrite') {
  if (!sessionId.value || sending.value) return
  sending.value = true
  err.value = ''
  abort?.abort()
  const ctrl = new AbortController()
  abort = ctrl
  messages.value = [
    ...messages.value.filter((x) => x.role !== 'hitl'),
    { role: 'typing', text: action === 'rewrite' ? '按新问法继续…' : '放行继续生成…' },
  ]
  const gotMeta = { v: false }
  try {
    await api.ragChatResumeStream(
      {
        session_id: sessionId.value,
        action,
        rewritten_query: action === 'rewrite' ? rewriteDraft.value : undefined,
      },
      applyMetaHandlers(gotMeta),
      { signal: ctrl.signal },
    )
    if (!gotMeta.v) messages.value = messages.value.filter((x) => x.role !== 'typing')
  } catch (e) {
    messages.value = messages.value.filter((x) => x.role !== 'typing')
    err.value = '恢复失败：' + (e as Error).message
  } finally {
    sending.value = false
  }
}

function newChat() {
  abort?.abort()
  sessionId.value = undefined
  messages.value = []
  err.value = ''
  query.value = ''
  sending.value = false
  rewriteDraft.value = ''
}
</script>

<template>
  <div class="chat-page">
    <aside class="sidebar">
      <div class="sb-head">
        <div class="sb-brand">
          <img class="logo" :src="brandMark" alt="" width="30" height="30" />
          <span>Project Agent</span>
        </div>
        <button class="new-btn" type="button" @click="newChat">＋ 开始新对话</button>
      </div>
      <div class="sb-list">
        <div class="sb-section">
          <h4>快捷问题</h4>
          <div v-for="item in QUICK" :key="item.label" class="sb-item" @click="send(item.q)">
            <span class="ic">💬</span>
            <span>{{ item.label }}</span>
          </div>
        </div>
      </div>
      <div class="sb-foot">
        <div class="av">U</div>
        <span>本地用户</span>
      </div>
    </aside>

    <main class="main">
      <div class="top-bar">
        <RouterLink class="ghost-btn" to="/">← 首页</RouterLink>
        <span :class="['health', healthOk ? 'ok' : 'bad']">{{ health }}</span>
      </div>

      <div ref="boxRef" class="msg-box">
        <div v-if="empty" class="empty-state">
          <div class="logo-big">💬</div>
          <h2>企业知识库对话</h2>
          <p>支持多查询 Fusion · Self-RAG · 忠实度校验 · 图级 HITL</p>
        </div>

        <template v-for="(m, i) in messages" :key="i">
          <div v-if="m.role === 'user'" class="msg user">
            <div class="bubble">{{ m.text }}</div>
            <div class="av">U</div>
          </div>
          <div v-else-if="m.role === 'typing'" class="msg bot">
            <div class="av">R</div>
            <div class="bubble">{{ m.text || '…' }}</div>
          </div>
          <div v-else-if="m.role === 'hitl'" class="msg bot">
            <div class="av">H</div>
            <div class="bubble">
              <span class="intent-chip">⏸ 图级 HITL · 待确认</span>
              <p style="margin: 8px 0">{{ String(m.payload.message || '需要人工确认') }}</p>
              <p v-if="m.payload.draft_answer" style="white-space: pre-wrap; opacity: 0.85">
                {{ String(m.payload.draft_answer).slice(0, 600) }}
              </p>
              <label style="display: block; font-size: 12px; color: #64748b; margin-top: 8px">
                改写问法
                <input v-model="rewriteDraft" style="width: 100%; margin-top: 4px; padding: 8px" />
              </label>
              <div style="display: flex; gap: 8px; margin-top: 12px">
                <button class="btn btn-primary" type="button" :disabled="sending" @click="resumeHitl('approve')">
                  放行继续
                </button>
                <button class="btn btn-ok" type="button" :disabled="sending" @click="resumeHitl('rewrite')">
                  用新问法继续
                </button>
              </div>
            </div>
          </div>
          <div v-else-if="m.role === 'bot'" class="msg bot">
            <div class="av">R</div>
            <div class="bubble">
              <span class="intent-chip">意图 · {{ m.data.intent || 'MIXED' }}</span>
              <div style="margin-top: 10px; white-space: pre-wrap">
                {{ m.data.answer }}
                <span v-if="m.streaming" class="stream-caret" />
              </div>
              <div v-if="!m.streaming" class="meta">
                <span>⏱ {{ m.data.elapsed_ms ?? '?' }} ms</span>
                <span>🆔 {{ String(m.data.session_id || '').slice(0, 8) || '—' }}</span>
                <span v-if="(m.data.multi_queries?.length || 0) > 0">🔀 Fusion ×{{ m.data.multi_queries!.length }}</span>
                <span v-if="(m.data.self_rag_retries ?? 0) > 0">🔁 Self-RAG ×{{ m.data.self_rag_retries }}</span>
                <span v-if="m.data.faithfulness_score != null">
                  ✅ 忠实度 {{ Number(m.data.faithfulness_score).toFixed(2) }}
                </span>
              </div>
            </div>
          </div>
        </template>
      </div>

      <div v-if="err" class="err-banner">{{ err }}</div>

      <div class="input-area">
        <div class="presets">
          <button v-for="p in presets" :key="p.query" class="preset" type="button" @click="send(p.query)">
            {{ p.tag }}
          </button>
        </div>
        <div class="composer">
          <textarea
            v-model="query"
            rows="2"
            placeholder="输入问题，Enter 发送"
            @keydown.enter.exact.prevent="send()"
          />
          <button class="btn btn-primary" type="button" :disabled="sending" @click="send()">发送</button>
        </div>
      </div>
    </main>
  </div>
</template>
