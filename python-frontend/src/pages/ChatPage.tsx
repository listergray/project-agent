import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import type { ChatResp } from '../types'
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
  | {
      role: 'hitl'
      session_id: string
      payload: Record<string, unknown>
      meta: Omit<ChatResp, 'answer'>
    }

const QUICK = [
  { label: 'FS-2024-0876 库存', q: 'FS-2024-0876 现在有多少库存？单价和总价是多少？' },
  { label: '固定资产入库流程', q: '固定资产入库的完整流程是什么？' },
  { label: '陈昊工号与同义词', q: '帮我查一下员工陈昊的工号、部门和岗位，存货/库存相关的同义词有哪些？' },
  { label: '最新审批项目', q: '最近审批通过的项目有哪些？' },
]

const HISTORY_KEY = 'pa-ai-chat-history-v1'

type HistoryItem = {
  id: string
  title: string
  updatedAt: string
  messages: Array<
    | { role: 'user'; text: string }
    | {
        role: 'bot'
        answer: string
        tool_calls?: Array<Record<string, unknown>>
        sources?: string[]
        intent?: string
      }
  >
}

function loadHistory(): HistoryItem[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as HistoryItem[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function saveHistory(list: HistoryItem[]) {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(list.slice(0, 30)))
  } catch {
    /* ignore */
  }
}

type ChatPageProps = {
  /** page = 完整智能对话页；panel = 悬浮助手内嵌 */
  variant?: 'page' | 'panel'
  /** 面板模式下由父级触发「新对话」时可传入 key 重置；也可调用此回调同步 UI */
  onSessionReset?: () => void
}

export function ChatPage({ variant = 'page', onSessionReset }: ChatPageProps) {
  const params = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : null
  const urlPanel = !!(params && (params.get('panel') === '1' || params.get('embed') === '1'))
  const isPanel = variant === 'panel' || urlPanel
  /** 仅超管可见 Milvus 状态：由若依壳通过 ?admin=1 传入 */
  const isSuperAdmin = params?.get('admin') === '1'
  const showMilvusBadge = isSuperAdmin

  const [messages, setMessages] = useState<Msg[]>([])
  const [query, setQuery] = useState('')
  const [err, setErr] = useState('')
  const [sending, setSending] = useState(false)
  const [health, setHealth] = useState('检查中…')
  const [healthOk, setHealthOk] = useState(true)
  const [presets, setPresets] = useState<Array<{ tag: string; query: string }>>([])
  const boxRef = useRef<HTMLDivElement>(null)
  const taRef = useRef<HTMLTextAreaElement>(null)
  const abortRef = useRef<AbortController | null>(null)
  const sessionIdRef = useRef<string | undefined>(undefined)
  const [rewriteDraft, setRewriteDraft] = useState('')
  const [historyOpen, setHistoryOpen] = useState(false)
  const [historyList, setHistoryList] = useState<HistoryItem[]>(() => loadHistory())

  useEffect(() => {
    if (!isPanel) return
    document.documentElement.classList.add('chat-embed-panel-html')
    document.body.classList.add('chat-embed-panel-body')
    return () => {
      document.documentElement.classList.remove('chat-embed-panel-html')
      document.body.classList.remove('chat-embed-panel-body')
    }
  }, [isPanel])

  function persistCurrentToHistory() {
    const firstUser = messages.find((m) => m.role === 'user')
    if (!firstUser || firstUser.role !== 'user') return
    const item: HistoryItem = {
      id: `${Date.now()}`,
      title: firstUser.text.slice(0, 36) || '未命名对话',
      updatedAt: new Date().toISOString(),
      messages: messages
        .filter((m) => m.role === 'user' || m.role === 'bot')
        .map((m) => {
          if (m.role === 'user') return { role: 'user' as const, text: m.text }
          return {
            role: 'bot' as const,
            answer: m.data.answer,
            tool_calls: m.data.tool_calls || [],
            sources: m.data.sources || [],
            intent: m.data.intent,
          }
        }),
    }
    const next = [item, ...historyList.filter((h) => h.title !== item.title)].slice(0, 30)
    setHistoryList(next)
    saveHistory(next)
  }

  function resetSession() {
    if (messages.length) persistCurrentToHistory()
    abortRef.current?.abort()
    sessionIdRef.current = undefined
    setRewriteDraft('')
    setMessages([])
    setErr('')
    setQuery('')
    setSending(false)
    setHistoryOpen(false)
    onSessionReset?.()
  }

  function restoreHistory(item: HistoryItem) {
    persistCurrentToHistory()
    setMessages(
      item.messages.map((m) => {
        if (m.role === 'user') return { role: 'user' as const, text: m.text }
        return {
          role: 'bot' as const,
          streaming: false,
          data: {
            session_id: '',
            answer: m.answer,
            sources: m.sources || [],
            tool_calls: m.tool_calls || [],
            intent: m.intent || 'MIXED',
            elapsed_ms: 0,
          },
        }
      }),
    )
    setHistoryOpen(false)
  }

  useEffect(() => {
    const onMsg = (ev: MessageEvent) => {
      const data = ev.data
      if (!data || data.source !== 'pa-parse') return
      if (data.type === 'pa-ai-new') resetSession()
      if (data.type === 'pa-ai-history') setHistoryOpen((v) => !v)
    }
    window.addEventListener('message', onMsg)
    return () => window.removeEventListener('message', onMsg)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages, historyList])


  useEffect(() => {
    let healthTimer: number | undefined
    if (showMilvusBadge) {
      const check = () => {
        api
          .health()
          .then((j) => {
            const m = j.milvus || {}
            if (j.readiness && m.kb_chunks != null && m.kb_item_names != null) {
              setHealth(`Milvus 已连接 · ${m.kb_item_names} 手册 / ${m.kb_chunks} chunks`)
              setHealthOk(true)
            } else if (m.error) {
              setHealth(`Milvus 未就绪：${String(m.error).slice(0, 80)}`)
              setHealthOk(false)
            } else {
              setHealth('服务存活，但向量库未就绪')
              setHealthOk(false)
            }
          })
          .catch(() => {
            setHealth('服务未连接')
            setHealthOk(false)
          })
      }
      check()
      healthTimer = window.setInterval(check, 8000)
    }
    api.ragPresets().then(setPresets).catch(() => {})
    return () => {
      if (healthTimer) window.clearInterval(healthTimer)
      abortRef.current?.abort()
    }
  }, [showMilvusBadge])

  useEffect(() => {
    if (boxRef.current) boxRef.current.scrollTop = boxRef.current.scrollHeight
  }, [messages])

  async function send(text?: string) {
    const q = (text || query).trim()
    if (!q || sending) return
    setErr('')
    setQuery('')
    setSending(true)
    abortRef.current?.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl
    const timer = setTimeout(() => ctrl.abort(), 180000)

    setMessages((m) => [...m, { role: 'user', text: q }, { role: 'typing', text: '检索与推理中…' }])

    let gotMeta = false
    try {
      await api.ragChatStream(
        q,
        streamHandlers(() => {
          gotMeta = true
        }),
        { signal: ctrl.signal, session_id: sessionIdRef.current },
      )
      if (!gotMeta) {
        setMessages((prev) => prev.filter((x) => x.role !== 'typing'))
      }
    } catch (e) {
      setMessages((prev) => prev.filter((x) => x.role !== 'typing'))
      if ((e as Error).name === 'AbortError') {
        setErr('请求超时或已取消（后端处理可能超过 180s）')
      } else {
        setErr('请求失败：' + (e as Error).message)
      }
    } finally {
      clearTimeout(timer)
      setSending(false)
      taRef.current?.focus()
    }
  }

  function streamHandlers(onGotMeta: () => void) {
    return {
      onStatus: (msg: string) => {
        setMessages((prev) => {
          const next = [...prev]
          const last = next[next.length - 1]
          if (last?.role === 'typing') next[next.length - 1] = { role: 'typing', text: msg }
          return next
        })
      },
      onMeta: (meta: Omit<ChatResp, 'answer'>) => {
        onGotMeta()
        if (meta.session_id) sessionIdRef.current = meta.session_id
        setMessages((prev) => {
          const next = prev.filter((x) => x.role !== 'typing')
          const last = next[next.length - 1]
          if (last?.role === 'bot' && last.streaming) {
            next[next.length - 1] = {
              ...last,
              streaming: true,
              data: { ...last.data, ...meta, answer: last.data.answer },
            }
            return next
          }
          next.push({ role: 'bot', streaming: true, data: { ...meta, answer: '' } })
          return next
        })
      },
      onToken: (piece: string) => {
        setMessages((prev) => {
          const next = [...prev]
          let last = next[next.length - 1]
          if (last?.role === 'typing') {
            next[next.length - 1] = {
              role: 'bot',
              streaming: true,
              data: {
                session_id: sessionIdRef.current || '',
                answer: piece,
                sources: [],
                tool_calls: [],
                intent: 'MIXED',
                elapsed_ms: 0,
              },
            }
            return next
          }
          if (last?.role === 'bot') {
            next[next.length - 1] = {
              ...last,
              streaming: true,
              data: { ...last.data, answer: last.data.answer + piece },
            }
          }
          return next
        })
      },
      onInterrupted: (meta: Omit<ChatResp, 'answer'>) => {
        onGotMeta()
        if (meta.session_id) sessionIdRef.current = meta.session_id
        setRewriteDraft(String(meta.interrupt_payload?.suggested_query || ''))
        setMessages((prev) => [
          ...prev.filter((x) => x.role !== 'typing' && x.role !== 'hitl'),
          {
            role: 'hitl',
            session_id: meta.session_id,
            payload: meta.interrupt_payload || {},
            meta,
          },
        ])
      },
      onDone: () => {
        setMessages((prev) => {
          const next = [...prev]
          const last = next[next.length - 1]
          if (last?.role === 'bot') next[next.length - 1] = { ...last, streaming: false }
          return next
        })
      },
      onError: (detail: string) => {
        setMessages((prev) => prev.filter((x) => x.role !== 'typing'))
        setErr('请求失败：' + detail)
      },
    }
  }

  async function resumeHitl(action: 'approve' | 'rewrite') {
    if (!sessionIdRef.current || sending) return
    setSending(true)
    setErr('')
    abortRef.current?.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl
    setMessages((prev) => [
      ...prev.filter((x) => x.role !== 'hitl'),
      { role: 'typing', text: action === 'rewrite' ? '按新问法继续…' : '放行继续生成…' },
    ])
    let gotMeta = false
    try {
      await api.ragChatResumeStream(
        {
          session_id: sessionIdRef.current,
          action,
          rewritten_query: action === 'rewrite' ? rewriteDraft : undefined,
        },
        streamHandlers(() => {
          gotMeta = true
        }),
        { signal: ctrl.signal },
      )
      if (!gotMeta) setMessages((prev) => prev.filter((x) => x.role !== 'typing'))
    } catch (e) {
      setMessages((prev) => prev.filter((x) => x.role !== 'typing'))
      setErr('恢复失败：' + (e as Error).message)
    } finally {
      setSending(false)
    }
  }

  return (
    <div className={`chat-page${isPanel ? ' chat-page--panel' : ''}`}>
      {!isPanel && (
        <aside className="sidebar">
          <div className="sb-head">
            <button className="new-btn" type="button" onClick={resetSession}>
              ＋ 开始新对话
            </button>
          </div>
          <div className="sb-list">
            <div className="sb-section">
              <h4>今天</h4>
              {QUICK.map((item) => (
                <div className="sb-item" key={item.label} onClick={() => send(item.q)}>
                  <span className="ic">💬</span>
                  <span>{item.label}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="sb-foot">
            <div className="av">U</div>
            <span>本地用户</span>
          </div>
        </aside>
      )}

      <main className="main">
        {showMilvusBadge && (
          <div className="top-bar top-bar--status-only">
            <span className={healthOk ? 'badge-ok' : 'badge-bad'}>
              <span className="badge-dot" />
              {health}
            </span>
          </div>
        )}

        <div className="chat-wrap" ref={boxRef}>
          {isPanel && historyOpen && (
            <div className="hist-panel">
              <div className="hist-head">
                <strong>历史对话</strong>
                <button type="button" className="hist-close" onClick={() => setHistoryOpen(false)}>
                  ×
                </button>
              </div>
              {historyList.length === 0 ? (
                <div className="hist-empty">暂无历史对话</div>
              ) : (
                <div className="hist-list">
                  {historyList.map((h) => (
                    <button key={h.id} type="button" className="hist-item" onClick={() => restoreHistory(h)}>
                      <span className="hist-title">{h.title}</span>
                      <span className="hist-time">{h.updatedAt.slice(0, 16).replace('T', ' ')}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
          {!messages.length && !historyOpen && (
            <div className="empty-state">
              {isPanel ? (
                <>
                  <div className="panel-hero">
                    <div className="logo-big ai-bot-face" aria-hidden>
                      <BotAvatar />
                    </div>
                    <div className="panel-hero-text">
                      <div className="panel-hello">您好，欢迎使用</div>
                      <div className="panel-hello-em">AI 助手</div>
                    </div>
                  </div>
                  <div className="panel-quick">
                    <div className="panel-quick-title">我可以帮您</div>
                    <div className="panel-quick-grid panel-quick-grid--3">
                      {[
                        { t: '项目预警', q: '帮我查看当前项目预警有哪些？' },
                        { t: '我的待办', q: '我的待办事项有哪些？请汇总立项与审批相关待办。' },
                        { t: '项目统计', q: '给我一份项目统计：草稿、待审批、已通过、已驳回各多少？' },
                      ].map((x) => (
                        <button key={x.t} type="button" className="panel-quick-card" onClick={() => send(x.q)}>
                          {x.t}
                        </button>
                      ))}
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <div className="logo-big">💬</div>
                  <h1>随时开始吧</h1>
                  <p>RAG 知识库 · SSE 流式回答 · Function Calling · Milvus 向量库</p>
                </>
              )}
            </div>
          )}
          {messages.map((m, i) => {
            if (m.role === 'user') {
              return (
                <div className={`msg user${isPanel ? ' msg--panel' : ''}`} key={i}>
                  {!isPanel && <div className="av">你</div>}
                  <div className="bubble">{m.text}</div>
                </div>
              )
            }
            if (m.role === 'typing') {
              return (
                <div className={`msg bot${isPanel ? ' msg--panel' : ''}`} key={i}>
                  <div className="av">{isPanel ? <BotAvatar small /> : 'R'}</div>
                  <div className="bubble bubble--plain">
                    {m.text && m.text !== '思考中…' && m.text !== '检索与推理中…' ? (
                      <div className="bot-lead">{m.text}</div>
                    ) : null}
                    <GeneratingRow />
                  </div>
                </div>
              )
            }
            if (m.role === 'hitl') {
              return (
                <div className={`msg bot${isPanel ? ' msg--panel' : ''}`} key={i}>
                  <div className="av">{isPanel ? <BotAvatar small /> : 'H'}</div>
                  <div className="bubble">
                    <span className="intent-chip">⏸ 图级 HITL · 待确认</span>
                    <div style={{ marginTop: 10, whiteSpace: 'pre-wrap' }}>
                      {String(m.payload.message || '需要人工确认后继续')}
                    </div>
                    {!!m.payload.draft_answer && (
                      <div style={{ marginTop: 8, opacity: 0.85, whiteSpace: 'pre-wrap', fontSize: 13 }}>
                        {String(m.payload.draft_answer).slice(0, 800)}
                      </div>
                    )}
                    <label style={{ display: 'block', marginTop: 12, fontSize: 12, color: '#64748b' }}>
                      改写问法
                      <input
                        value={rewriteDraft}
                        onChange={(e) => setRewriteDraft(e.target.value)}
                        style={{
                          width: '100%',
                          marginTop: 6,
                          padding: '8px 10px',
                          borderRadius: 10,
                          border: '1px solid #e2e8f0',
                        }}
                      />
                    </label>
                    <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                      <button className="btn btn-primary" type="button" disabled={sending} onClick={() => resumeHitl('approve')}>
                        放行继续
                      </button>
                      <button className="btn btn-ok" type="button" disabled={sending} onClick={() => resumeHitl('rewrite')}>
                        用新问法继续
                      </button>
                    </div>
                  </div>
                </div>
              )
            }
            const intent = m.data.intent || 'MIXED'
            const isCode = /CODE|RESOURCE|TOOL/i.test(intent)
            return (
              <div className={`msg bot${isPanel ? ' msg--panel' : ''}`} key={i}>
                <div className="av">{isPanel ? <BotAvatar small /> : 'R'}</div>
                <div className={`bubble${isPanel ? ' bubble--plain' : ''}`}>
                  {!isPanel && (
                    <span className={`intent-chip ${isCode ? 'code' : ''}`}>意图 · {intent}</span>
                  )}
                  <ToolCalls tcs={m.data.tool_calls} panel={isPanel} />
                  {!isPanel && <Sources srcs={m.data.sources} />}
                  <div className="bot-answer" style={{ marginTop: isPanel ? 0 : 10, whiteSpace: 'pre-wrap' }}>
                    {m.data.answer}
                    {m.streaming && !isPanel && <span className="stream-caret" />}
                  </div>
                  {m.streaming && isPanel && <GeneratingRow />}
                  {isPanel && !m.streaming && m.data.answer && (
                    <div className="msg-actions">
                      <button type="button" title="有用" onClick={() => {}}>
                        👍
                      </button>
                      <button type="button" title="没用" onClick={() => {}}>
                        👎
                      </button>
                      <button
                        type="button"
                        title="复制"
                        onClick={() => navigator.clipboard?.writeText(m.data.answer || '')}
                      >
                        ⧉
                      </button>
                    </div>
                  )}
                  {!isPanel && !m.streaming && (
                    <div className="meta">
                      <span>⏱ {m.data.elapsed_ms ?? '?'} ms</span>
                      <span>🆔 {String(m.data.session_id || '').slice(0, 8) || '—'}</span>
                      {m.data.need_rag === false && <span>⏭ 跳过 RAG</span>}
                      {m.data.need_rag === true && <span>📚 走 RAG</span>}
                      {(m.data.multi_queries?.length || 0) > 0 && (
                        <span>🔀 Fusion ×{m.data.multi_queries!.length}</span>
                      )}
                      {(m.data.self_rag_retries ?? 0) > 0 && (
                        <span>🔁 Self-RAG ×{m.data.self_rag_retries}</span>
                      )}
                      {m.data.faithfulness_score != null && (
                        <span>✅ 忠实度 {Number(m.data.faithfulness_score).toFixed(2)}</span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        <div className="input-area">
          {!isPanel && (
            <div className="presets">
              {presets.map((p) => (
                <button className="preset" key={p.query} onClick={() => send(p.query)}>
                  <span className="tag">{p.tag.split('（')[0]}</span>
                  {p.query}
                </button>
              ))}
            </div>
          )}
          <div className="input-box">
            <textarea
              ref={taRef}
              value={query}
              placeholder={isPanel ? '今天有什么需要我帮您的吗？描述您的需求…' : '给 RAG 知识库 发送消息…'}
              rows={1}
              onChange={(e) => {
                setQuery(e.target.value)
                e.target.style.height = 'auto'
                e.target.style.height = Math.min(e.target.scrollHeight, 180) + 'px'
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  send()
                }
              }}
            />
            <div className="input-tools">
              <div className="tools-l">
                <button className="chip-btn" type="button">🧠 深度思考</button>
                <button className="chip-btn" type="button">🔍 智能搜索</button>
              </div>
              <button className="send-btn" disabled={sending} onClick={() => send()} title="发送">
                ↑
              </button>
            </div>
          </div>
          {err && <div className="err">{err}</div>}
        </div>
      </main>
    </div>
  )
}

function ToolCalls({ tcs, panel }: { tcs: Array<Record<string, unknown>>; panel?: boolean }) {
  if (!tcs?.length) {
    if (panel) return null
    return (
      <div className="section">
        <div className="lbl">工具调用</div>
        <div style={{ color: '#94a3b8', fontSize: 12.5 }}>本次未触发 Function Calling（fallback 模板）</div>
      </div>
    )
  }
  if (panel) {
    return (
      <div className="tool-success-list">
        {tcs.map((t, i) => {
          const name = String(t.name || t.tool || '工具调用')
          const args = (t.arguments || t.args || {}) as Record<string, unknown>
          const entries = Object.entries(args)
          return (
            <div className="tool-success-card" key={i}>
              <div className="tool-success-head">
                <span className="tool-success-ico">🔧</span>
                <span className="tool-success-name">{name}</span>
                <span className="tool-success-code">{'</>'}</span>
              </div>
              <div className="tool-success-ok">✓ 工具调用成功</div>
              {entries.length > 0 && (
                <div className="tool-success-table-wrap">
                  <table className="tool-success-table">
                    <thead>
                      <tr>
                        <th>参数</th>
                        <th>值</th>
                      </tr>
                    </thead>
                    <tbody>
                      {entries.slice(0, 8).map(([k, v]) => (
                        <tr key={k}>
                          <td>{k}</td>
                          <td>{typeof v === 'string' ? v : JSON.stringify(v)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )
        })}
      </div>
    )
  }
  return (
    <div className="section">
      <div className="lbl">工具调用 · {tcs.length}</div>
      {tcs.map((t, i) => (
        <div className="toolcard" key={i}>
          <span className="name">ƒ {String(t.name || t.tool || '')}</span>
          <pre>{JSON.stringify(t.arguments || t.args || t, null, 2)}</pre>
        </div>
      ))}
    </div>
  )
}

function Sources({ srcs }: { srcs: string[] }) {
  if (!srcs?.length) return null
  return (
    <div className="section">
      <div className="lbl">溯源 · {srcs.length}</div>
      {srcs.slice(0, 4).map((s, i) => (
        <span className="src" key={i}>
          {String(s).slice(0, 80)}
        </span>
      ))}
      {srcs.length > 4 && <span className="src">… 还有 {srcs.length - 4} 条</span>}
    </div>
  )
}

function GeneratingRow() {
  return (
    <div className="gen-status" aria-live="polite">
      正在生成
      <span className="gen-dots" aria-hidden>
        <i />
        <i />
        <i />
      </span>
    </div>
  )
}

function BotAvatar({ small }: { small?: boolean }) {
  const s = small ? 34 : 56
  return (
    <svg viewBox="0 0 64 64" width={s} height={s} aria-hidden>
      <circle cx="32" cy="32" r="30" fill="#2563eb" />
      <ellipse cx="32" cy="36" rx="18" ry="15" fill="#fff" />
      <rect x="18" y="28" width="28" height="12" rx="6" fill="#0f172a" />
      <rect x="22" y="31.5" width="20" height="5" rx="2.5" fill="#38bdf8" />
      <circle cx="22" cy="22" r="3.2" fill="#bfdbfe" />
      <circle cx="42" cy="22" r="3.2" fill="#bfdbfe" />
    </svg>
  )
}

