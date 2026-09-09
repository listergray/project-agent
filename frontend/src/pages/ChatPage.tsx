import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
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

export function ChatPage() {
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

  useEffect(() => {
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
    const t = setInterval(check, 8000)
    api.ragPresets().then(setPresets).catch(() => {})
    return () => {
      clearInterval(t)
      abortRef.current?.abort()
    }
  }, [])

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
          next.push({ role: 'bot', streaming: true, data: { ...meta, answer: '' } })
          return next
        })
      },
      onToken: (piece: string) => {
        setMessages((prev) => {
          const next = [...prev]
          const last = next[next.length - 1]
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
    <div className="chat-page">
      <aside className="sidebar">
        <div className="sb-head">
          <div className="sb-brand">
            <img className="logo" src={brandMark} alt="" width={30} height={30} />
            <span>Project Agent</span>
          </div>
          <button
            className="new-btn"
            onClick={() => {
              abortRef.current?.abort()
              sessionIdRef.current = undefined
              setRewriteDraft('')
              setMessages([])
              setErr('')
              setQuery('')
              setSending(false)
            }}
          >
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

      <main className="main">
        <div className="top-bar">
          <div className="crumb">
            <Link to="/">导航</Link> / <strong>RAG 知识库 · 对话（流式）</strong>
          </div>
          <div>
            <span className={healthOk ? 'badge-ok' : 'badge-bad'}>
              <span className="badge-dot" />
              {health}
            </span>
          </div>
        </div>

        <div className="chat-wrap" ref={boxRef}>
          {!messages.length && (
            <div className="empty-state">
              <div className="logo-big">💬</div>
              <h1>随时开始吧</h1>
              <p>RAG 知识库 · SSE 流式回答 · Function Calling · Milvus 向量库</p>
            </div>
          )}
          {messages.map((m, i) => {
            if (m.role === 'user') {
              return (
                <div className="msg user" key={i}>
                  <div className="av">你</div>
                  <div className="bubble">{m.text}</div>
                </div>
              )
            }
            if (m.role === 'typing') {
              return (
                <div className="msg bot" key={i}>
                  <div className="av">R</div>
                  <div className="bubble typing">{m.text || '思考中…'}</div>
                </div>
              )
            }
            if (m.role === 'hitl') {
              return (
                <div className="msg bot" key={i}>
                  <div className="av">H</div>
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
              <div className="msg bot" key={i}>
                <div className="av">R</div>
                <div className="bubble">
                  <span className={`intent-chip ${isCode ? 'code' : ''}`}>意图 · {intent}</span>
                  <ToolCalls tcs={m.data.tool_calls} />
                  <Sources srcs={m.data.sources} />
                  <div style={{ marginTop: 10, whiteSpace: 'pre-wrap' }}>
                    {m.data.answer}
                    {m.streaming && <span className="stream-caret" />}
                  </div>
                  {!m.streaming && (
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
          <div className="presets">
            {presets.map((p) => (
              <button className="preset" key={p.query} onClick={() => send(p.query)}>
                <span className="tag">{p.tag.split('（')[0]}</span>
                {p.query}
              </button>
            ))}
          </div>
          <div className="input-box">
            <textarea
              ref={taRef}
              value={query}
              placeholder="给 RAG 知识库 发送消息…"
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

function ToolCalls({ tcs }: { tcs: Array<Record<string, unknown>> }) {
  if (!tcs?.length) {
    return (
      <div className="section">
        <div className="lbl">工具调用</div>
        <div style={{ color: '#94a3b8', fontSize: 12.5 }}>本次未触发 Function Calling（fallback 模板）</div>
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
