import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { NavBar } from '../components/NavBar'
import { AiAssistantFloat } from '../components/AiAssistantFloat'
import {
  emptyProjectFields,
  type ProjectFields,
  type ProjectRecord,
  type ProjectStats,
  type ProjectStatus,
} from '../types'
import './ProjectsPage.css'

const STATUS_LABEL: Record<ProjectStatus, string> = {
  draft: '草稿',
  pending: '待审批',
  approved: '已通过',
  rejected: '已驳回',
}

type Tab = 'create' | 'approve' | 'list'
type Mode = 'manual' | 'file'
type ResultKind = 'draft' | 'submitted' | null
type StatusFilter = '' | ProjectStatus

const KPI_ITEMS: Array<{ key: StatusFilter; label: string; warn?: boolean }> = [
  { key: '', label: '全部' },
  { key: 'draft', label: '草稿' },
  { key: 'pending', label: '待审批', warn: true },
  { key: 'approved', label: '已通过' },
  { key: 'rejected', label: '已驳回' },
]

function detectEmbed(): boolean {
  try {
    const params = new URLSearchParams(window.location.search)
    if (params.get('embed') === '1') return true
    if (window.self !== window.top) return true
  } catch {
    // cross-origin iframe access to top throws → treat as embed
    return true
  }
  return false
}

/** Best-effort current user from RuoYi / common admin SPA storage. */
function resolveCurrentUser(): string | null {
  const pick = (raw: string | null): string | null => {
    if (!raw) return null
    const trimmed = raw.trim()
    if (!trimmed) return null
    try {
      const parsed = JSON.parse(trimmed) as Record<string, unknown> | string
      if (typeof parsed === 'string' && parsed.trim()) return parsed.trim()
      if (parsed && typeof parsed === 'object') {
        for (const k of ['username', 'userName', 'nickName', 'nickname', 'name', 'realName', 'displayName']) {
          const v = parsed[k]
          if (typeof v === 'string' && v.trim()) return v.trim()
        }
        const user = parsed.user
        if (user && typeof user === 'object') {
          const u = user as Record<string, unknown>
          for (const k of ['username', 'userName', 'nickName', 'nickname', 'name']) {
            const v = u[k]
            if (typeof v === 'string' && v.trim()) return v.trim()
          }
        }
      }
    } catch {
      if (trimmed.length < 80 && !trimmed.startsWith('{')) return trimmed
    }
    return null
  }

  try {
    const keys = [
      'USERNAME',
      'username',
      'userName',
      'user',
      'USER',
      'currentUser',
      'loginUser',
      'Admin-Token-User',
      'ruoyi_user',
      'userInfo',
    ]
    for (const store of [localStorage, sessionStorage]) {
      for (const k of keys) {
        const hit = pick(store.getItem(k))
        if (hit) return hit
      }
    }
    // scan for objects that look like user profiles
    for (const store of [localStorage, sessionStorage]) {
      for (let i = 0; i < store.length; i++) {
        const key = store.key(i)
        if (!key) continue
        if (!/user|login|profile|account/i.test(key)) continue
        const hit = pick(store.getItem(key))
        if (hit) return hit
      }
    }
  } catch {
    /* ignore */
  }
  return null
}

function formatBudget(n: number | undefined | null): string {
  return `¥${Number(n || 0).toLocaleString()}`
}

function formatUpdated(s?: string | null): string {
  if (!s) return '—'
  // keep compact: prefer MM-DD HH:mm when ISO-like
  const m = s.match(/(\d{2}-\d{2})\s+(\d{2}:\d{2})/) || s.match(/(\d{4}-\d{2}-\d{2})[T\s](\d{2}:\d{2})/)
  if (m) return `${m[1].slice(-5)} ${m[2]}`.replace(/^(\d{4}-)/, '')
  return s.length > 16 ? s.slice(0, 16) : s
}

export function ProjectsPage() {
  const embed = useMemo(() => detectEmbed(), [])
  const currentUser = useMemo(() => resolveCurrentUser(), [])

  const [tab, setTab] = useState<Tab>(() => {
    try {
      const t = new URLSearchParams(window.location.search).get('tab')
      if (t === 'create' || t === 'approve' || t === 'list') return t
    } catch {
      /* ignore */
    }
    return 'list'
  })
  const [aiOpen, setAiOpen] = useState(false)
  const [mode, setMode] = useState<Mode>('manual')
  const [step, setStep] = useState(1)
  const [resultKind, setResultKind] = useState<ResultKind>(null)
  const [stats, setStats] = useState<ProjectStats>({ total: 0, draft: 0, pending: 0, approved: 0, rejected: 0 })
  const [fields, setFields] = useState<ProjectFields>(emptyProjectFields())
  const [editingId, setEditingId] = useState<string | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [extraImages, setExtraImages] = useState<File[]>([])
  const [parsing, setParsing] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [banner, setBanner] = useState<{ kind: 'parse' | 'ok'; text: string } | null>(null)
  const [hint, setHint] = useState('当前：新立项 · 未保存')
  const [toast, setToast] = useState<{ msg: string; type: string } | null>(null)
  const [pending, setPending] = useState<ProjectRecord[]>([])
  const [all, setAll] = useState<ProjectRecord[]>([])
  const [filter, setFilter] = useState<StatusFilter>('')
  const [keyword, setKeyword] = useState('')
  const [review, setReview] = useState<{ id: string; action: 'approve' | 'reject' } | null>(null)
  const [reviewer, setReviewer] = useState(currentUser || '审批人')
  const [comment, setComment] = useState('')
  const [viewing, setViewing] = useState<ProjectRecord | null>(null)

  const showToast = useCallback((msg: string, type = '') => {
    setToast({ msg, type })
    window.setTimeout(() => setToast(null), 3000)
  }, [])

  const refreshStats = useCallback(() => {
    api.projectStats().then(setStats).catch(() => {})
  }, [])

  useEffect(() => {
    refreshStats()
  }, [refreshStats])

  useEffect(() => {
    if (!embed) return
    document.body.classList.add('pm-embed-body')
    return () => document.body.classList.remove('pm-embed-body')
  }, [embed])

  useEffect(() => {
    if (currentUser) setReviewer(currentUser)
  }, [currentUser])

  const loadApprove = useCallback(async () => {
    try {
      const j = await api.listProjects('pending')
      setPending(j.items)
    } catch {
      setPending([])
    }
  }, [])

  const keywordRef = useRef(keyword)
  keywordRef.current = keyword

  const loadAll = useCallback(async (qOverride?: string) => {
    try {
      const q = (qOverride !== undefined ? qOverride : keywordRef.current).trim()
      const j = await api.listProjects(filter || undefined, q || undefined)
      setAll(j.items)
    } catch {
      setAll([])
    }
  }, [filter])

  useEffect(() => {
    if (tab === 'approve') loadApprove()
    if (tab === 'list') loadAll()
  }, [tab, loadApprove, loadAll])

  // Debounced keyword → server-side q refresh (~300ms)
  const keywordBoot = useRef(true)
  useEffect(() => {
    if (tab !== 'list') return
    if (keywordBoot.current) {
      keywordBoot.current = false
      return
    }
    const t = window.setTimeout(() => {
      loadAll(keyword)
    }, 300)
    return () => window.clearTimeout(t)
  }, [keyword, tab, loadAll])

  // Lightweight client safety filter (server already filtered by q)
  const filteredList = useMemo(() => {
    const q = keyword.trim().toLowerCase()
    if (!q) return all
    return all.filter((p) => {
      const hay = `${p.project_name || ''} ${p.project_code || ''} ${p.owner || ''}`.toLowerCase()
      return hay.includes(q)
    })
  }, [all, keyword])

  function setField<K extends keyof ProjectFields>(key: K, value: ProjectFields[K]) {
    setFields((prev) => ({ ...prev, [key]: value }))
  }

  function setStatusFilter(next: StatusFilter) {
    setFilter(next)
    setTab('list')
  }

  async function onPickFiles(list: FileList | File[] | null) {
    if (!list || list.length === 0) return
    const files = Array.from(list)
    const docExts = ['.md', '.markdown', '.txt', '.pdf', '.docx', '.xlsx', '.xlsm', '.zip']
    const imgExts = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']
    const docs = files.filter((f) => docExts.includes('.' + (f.name.split('.').pop() || '').toLowerCase()))
    const imgs = files.filter((f) => imgExts.includes('.' + (f.name.split('.').pop() || '').toLowerCase()))
    if (!docs.length && !imgs.length) {
      showToast('请选择 Word/Excel/PDF/MD 等文档，或与图片一并选择', 'err')
      return
    }
    const doc = docs[0] || file
    if (!doc) {
      showToast('请至少选择一份立项文档（.docx / .xlsx / .pdf / .md / .zip）', 'err')
      return
    }
    if (doc.size > 20 * 1024 * 1024) {
      showToast('文件超过 20MB', 'err')
      return
    }
    setFile(doc)
    setExtraImages(imgs)

    const lower = doc.name.toLowerCase()
    if ((lower.endsWith('.md') || lower.endsWith('.markdown')) && imgs.length === 0) {
      try {
        const text = await doc.text()
        const refs = [
          ...Array.from(text.matchAll(/!\[[^\]]*\]\(([^)]+)\)/g)).map((m) => m[1]),
          ...Array.from(text.matchAll(/!\[\[([^\]|#]+)/g)).map((m) => m[1]),
          ...Array.from(text.matchAll(/<img[^>]+src=["']([^"']+)["']/gi)).map((m) => m[1]),
        ]
          .map((s) => s.trim().replace(/^<|>$/g, ''))
          .filter((s) => s && !s.startsWith('data:') && !/^https?:\/\//i.test(s))
        // 仅相对路径缺文件时提示；data: 内嵌图后端可直接解析
        if (refs.length > 0) {
          showToast(
            `文档引用了 ${refs.length} 张外部图片（如 ${refs[0]}）。不必打包：请按住 Ctrl 多选同目录图片；若图已内嵌 base64 可直接解析`,
            'err',
          )
        }
      } catch {
        /* ignore */
      }
    }

    const tip =
      imgs.length > 0
        ? `已选择 ${doc.name} + ${imgs.length} 张图片`
        : `已选择 ${doc.name}`
    showToast(tip, 'ok')
  }

  async function onParse() {
    if (!file || parsing) return
    setParsing(true)
    showToast('正在解析（含图片识别时可能较慢）…')
    try {
      const j = await api.parseProject(file, extraImages)
      setFields(j.fields)
      setEditingId(null)
      const conf = Math.round((j.confidence || 0) * 100)
      const imgPart =
        j.images_parsed && j.images_parsed > 0 ? ` · 图片 ${j.images_parsed} 张` : ''
      const warnPart =
        j.warnings && j.warnings.length ? ` · 注意：${j.warnings[0]}` : ''
      setBanner({
        kind: 'parse',
        text: `已解析「${j.filename}」· 方式 ${j.method} · 置信度 ${conf}%${imgPart}${warnPart} · 请人工确认后提交`,
      })
      setHint(`解析回填 · 置信度 ${conf}% · 尚未保存`)
      setStep(2)
      if (j.warnings?.length && !(j.images_parsed && j.images_parsed > 0)) {
        showToast(j.warnings[0], 'err')
      } else {
        showToast(
          j.images_parsed && j.images_parsed > 0
            ? `解析完成（已识别 ${j.images_parsed} 张图），请确认表单`
            : '解析完成，请确认表单',
          'ok',
        )
      }
    } catch (e) {
      const msg = (e as Error).message || String(e)
      if (msg.includes('解析超时')) showToast(msg, 'err')
      else showToast('解析失败: ' + msg, 'err')
    } finally {
      setParsing(false)
    }
  }

  async function saveDraft(opts?: { stayOnForm?: boolean }) {
    if (!fields.project_name.trim()) {
      showToast('请填写项目名称', 'err')
      return null
    }
    const j = editingId
      ? await api.updateProject(editingId, fields)
      : await api.createProject(fields)
    setEditingId(j.id)
    setHint(`草稿已保存 · ID ${j.id}`)
    if (!opts?.stayOnForm) {
      setResultKind('draft')
      setStep(3)
    }
    refreshStats()
    return j
  }

  async function onSubmit() {
    if (submitting) return
    setSubmitting(true)
    try {
      const j = await saveDraft({ stayOnForm: true })
      if (!j) return
      const out = await api.submitProject(j.id)
      setHint(`已提交审批 · ${out.project_name}`)
      setBanner({
        kind: 'ok',
        text: '已提交审批，可在「审批中心」处理，或在「全部项目」查看进度。',
      })
      setResultKind('submitted')
      setStep(3)
      showToast('已提交审批', 'ok')
      refreshStats()
    } catch (e) {
      showToast((e as Error).message, 'err')
    } finally {
      setSubmitting(false)
    }
  }

  async function confirmReview() {
    if (!review) return
    const action = review.action
    if (action === 'reject' && !comment.trim()) {
      showToast('驳回时请填写审批意见', 'err')
      return
    }
    try {
      const j = (await api.reviewProject(review.id, {
        action,
        reviewer: reviewer || currentUser || '审批人',
        comment: comment || '',
      })) as Awaited<ReturnType<typeof api.reviewProject>> & {
        rag_synced?: boolean
        rag_error?: string
      }
      setReview(null)
      setComment('')
      if (action === 'approve') {
        if (j.rag_synced) {
          showToast('已通过，已同步到知识库，可在对话中提问', 'ok')
        } else {
          showToast(
            j.rag_error
              ? `已通过，但知识库同步失败：${j.rag_error}`
              : '已通过（知识库未同步）',
            j.rag_error ? 'err' : 'ok',
          )
        }
      } else {
        showToast('已驳回', 'ok')
      }
      refreshStats()
      loadApprove()
      if (tab === 'list') loadAll()
    } catch (e) {
      showToast((e as Error).message, 'err')
    }
  }

  function resetForm() {
    setFields(emptyProjectFields())
    setEditingId(null)
    setBanner(null)
    setHint('当前：新立项 · 未保存')
    setStep(1)
    setResultKind(null)
    setFile(null)
    setMode('manual')
  }

  function continueEdit(p: ProjectRecord) {
    const next = emptyProjectFields()
    ;(Object.keys(next) as Array<keyof ProjectFields>).forEach((k) => {
      const v = p[k]
      if (v !== undefined && v !== null) {
        ;(next as unknown as Record<string, unknown>)[k] = v
      }
    })
    setFields(next)
    setEditingId(p.id)
    setTab('create')
    setMode(p.source_file ? 'file' : 'manual')
    setHint(`编辑中 · ID ${p.id}`)
    setResultKind(null)
    setBanner(null)
    setStep(2)
    showToast('已载入到表单', 'ok')
  }

  function openCreate() {
    resetForm()
    setTab('create')
  }

  const kpiValue = (key: StatusFilter): number => {
    if (key === '') return stats.total
    return stats[key]
  }

  return (
    <div className={`pm-page${embed ? ' pm-embed' : ''}${tab === 'create' && aiOpen ? ' pm-ai-open' : ''}`}>
      {!embed && (
        <>
          <NavBar right={<Link className="ghost-btn" to="/">← 返回首页</Link>} />
          <section className="proj-hero">
            <h2>立项 · 解析 · 确认 · 审批</h2>
            <h1>项目管理</h1>
            <p>
              支持人工录入或上传立项文档自动解析；解析结果先进入表单人工确认，再提交审批。完整流程：录入 → 确认 →
              提交 → 审批通过/驳回。
            </p>
          </section>
        </>
      )}

      <div className={`pm-shell${tab === 'create' && aiOpen ? ' pm-shell--ai' : ''}`}>
        <div className="pm-head">
          <div>
            <h1>项目管理</h1>
            <p>立项录入 → 确认 → 提交审批 → 通过 / 驳回</p>
          </div>
          <button type="button" className="btn btn-primary" onClick={openCreate}>
            + 新建立项
          </button>
        </div>

        <div className="pm-kpi">
          {KPI_ITEMS.map((item) => (
            <button
              type="button"
              key={item.key || 'all'}
              className={`pm-kpi-card${filter === item.key ? ' on' : ''}${item.warn ? ' warn' : ''}`}
              onClick={() => setStatusFilter(item.key)}
            >
              <div className="v">{kpiValue(item.key)}</div>
              <div className="l">{item.label}</div>
            </button>
          ))}
        </div>

        <div className="pm-panel">
          <div className="pm-tabs">
            {(
              [
                ['list', '全部项目'],
                ['create', '新建立项'],
                ['approve', `审批中心${stats.pending ? ` · ${stats.pending}` : ''}`],
              ] as const
            ).map(([k, label]) => (
              <button
                key={k}
                type="button"
                className={`pm-tab${tab === k ? ' on' : ''}`}
                onClick={() => setTab(k)}
              >
                {label}
              </button>
            ))}
          </div>

          {tab === 'list' && (
            <section className="pm-view">
              <div className="pm-toolbar">
                <input
                  className="grow"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                  placeholder="搜索项目名称 / 编号 / 负责人"
                />
                <select
                  value={filter}
                  onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
                >
                  <option value="">全部状态</option>
                  <option value="draft">草稿</option>
                  <option value="pending">待审批</option>
                  <option value="approved">已通过</option>
                  <option value="rejected">已驳回</option>
                </select>
                <button type="button" className="btn btn-ghost" onClick={() => { refreshStats(); loadAll() }}>
                  刷新
                </button>
              </div>

              {filteredList.length === 0 ? (
                <div className="pm-empty">
                  <p>暂无项目</p>
                  <button type="button" className="btn btn-primary" onClick={openCreate}>
                    新建立项
                  </button>
                </div>
              ) : (
                <div className="pm-table-wrap">
                  <table className="pm-table">
                    <thead>
                      <tr>
                        <th>名称</th>
                        <th>编号</th>
                        <th>类型</th>
                        <th>负责人</th>
                        <th>优先级</th>
                        <th>预算</th>
                        <th>状态</th>
                        <th>更新</th>
                        <th>操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredList.map((p) => (
                        <tr key={p.id}>
                          <td>
                            <div className="name">{p.project_name || '未命名'}</div>
                          </td>
                          <td>{p.project_code || '—'}</td>
                          <td>{p.project_type || '—'}</td>
                          <td>{p.owner || '—'}</td>
                          <td className={`pri ${p.priority || ''}`}>{p.priority || '—'}</td>
                          <td>{formatBudget(p.budget)}</td>
                          <td>
                            <span className={`badge ${p.status}`}>{STATUS_LABEL[p.status]}</span>
                          </td>
                          <td>{formatUpdated(p.updated_at)}</td>
                          <td>
                            <div className="ops">
                              {p.status === 'pending' && (
                                <>
                                  <button type="button" className="btn btn-ok btn-sm" onClick={() => setReview({ id: p.id, action: 'approve' })}>
                                    通过
                                  </button>
                                  <button type="button" className="btn btn-danger btn-sm" onClick={() => setReview({ id: p.id, action: 'reject' })}>
                                    驳回
                                  </button>
                                </>
                              )}
                              {(p.status === 'draft' || p.status === 'rejected') && (
                                <button type="button" className="btn btn-ghost btn-sm" onClick={() => continueEdit(p)}>
                                  继续编辑
                                </button>
                              )}
                              {p.status === 'approved' && (
                                <button type="button" className="btn btn-ghost btn-sm" onClick={() => setViewing(p)}>
                                  查看
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          )}

          {tab === 'create' && (
            <section className="pm-view pm-create">
              <div className="pm-steps">
                {[
                  ['选择录入方式', 1],
                  ['填写与确认', 2],
                  ['提交结果', 3],
                ].map(([label, n]) => {
                  const num = n as number
                  const cls = num < step ? 'done' : num === step ? 'on' : ''
                  return (
                    <div className={`pm-step ${cls}`} key={num}>
                      {num} {label}
                    </div>
                  )
                })}
              </div>

              {step === 1 && (
                <>
                  <p className="sub">选择人工录入或上传立项文档自动解析；确认后进入表单核对。</p>
                  <div className="mode-row">
                    <button
                      type="button"
                      className={`mode${mode === 'manual' ? ' on' : ''}`}
                      onClick={() => {
                        setMode('manual')
                        setStep(2)
                      }}
                    >
                      <div className="mode-icon" aria-hidden>
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                          <path d="M12 20h9" />
                          <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
                        </svg>
                      </div>
                      <div className="t">人工录入</div>
                      <div className="d">空白表单，手动填写项目编号、负责人、预算等字段后提交。</div>
                    </button>
                    <button
                      type="button"
                      className={`mode${mode === 'file' ? ' on' : ''}`}
                      onClick={() => {
                        setMode('file')
                        setStep(2)
                      }}
                    >
                      <div className="mode-icon" aria-hidden>
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                          <path d="M14 2v6h6" />
                          <path d="M12 18v-6" />
                          <path d="M9 15l3-3 3 3" />
                        </svg>
                      </div>
                      <div className="t">文件上传解析</div>
                      <div className="d">上传 Word / Excel / PDF / MD，自动抽字段（含文档内图片）→ 人工确认 → 提交审批。</div>
                    </button>
                  </div>
                </>
              )}

              {step === 2 && (
                <>
                  {mode === 'file' && (
                    <div>
                      <label
                        className="drop"
                        onDragOver={(e) => e.preventDefault()}
                        onDrop={(e) => {
                          e.preventDefault()
                          onPickFiles(e.dataTransfer.files)
                        }}
                      >
                        <h4>拖拽立项文件到这里</h4>
                        <p>
                          支持 Word(.docx) / Excel(.xlsx) / PDF / MD；自动识别文档内图片。≤ 20MB。
                          支持内嵌图、相对路径、Obsidian ![[图]]；仅传 md 而图片在别处时请一并选中图片。
                        </p>
                        {file && (
                          <div className="file-chip">
                            {file.name} · {(file.size / 1024).toFixed(1)} KB
                            {extraImages.length > 0 ? ` · +${extraImages.length} 图` : ''}
                          </div>
                        )}
                        <input
                          type="file"
                          accept=".md,.markdown,.txt,.pdf,.docx,.xlsx,.xlsm,.zip,image/*,.doc,.xls"
                          multiple
                          hidden
                          onChange={(e) => onPickFiles(e.target.files)}
                        />
                      </label>
                      <div className="btn-row" style={{ marginBottom: 14 }}>
                        <button
                          type="button"
                          className="btn btn-primary"
                          disabled={!file || parsing}
                          onClick={onParse}
                        >
                          {parsing ? '解析中…' : '解析并填入'}
                        </button>
                        <button
                          type="button"
                          className="btn btn-ghost"
                          disabled={!file || parsing}
                          onClick={() => {
                            setFile(null)
                            setExtraImages([])
                            setBanner(null)
                          }}
                        >
                          清除文件
                        </button>
                        <button type="button" className="btn btn-ghost" onClick={() => setStep(1)}>
                          返回上一步
                        </button>
                      </div>
                    </div>
                  )}

                  {banner && <div className={`banner ${banner.kind} show`}>{banner.text}</div>}

                  {mode === 'manual' && (
                    <div className="btn-row" style={{ marginBottom: 12 }}>
                      <button type="button" className="btn btn-ghost" onClick={() => setStep(1)}>
                        返回上一步
                      </button>
                    </div>
                  )}

                  <form
                    onSubmit={(e: FormEvent) => {
                      e.preventDefault()
                      onSubmit()
                    }}
                  >
                    <div className="form-group">
                      <h4>基本信息</h4>
                      <div className="form-grid">
                        <Field label="项目编号">
                          <input
                            value={fields.project_code}
                            onChange={(e) => setField('project_code', e.target.value)}
                            placeholder="如 PRJ-2026-001"
                          />
                        </Field>
                        <Field label="项目名称" required>
                          <input
                            value={fields.project_name}
                            onChange={(e) => setField('project_name', e.target.value)}
                            required
                            placeholder="必填"
                          />
                        </Field>
                        <Field label="项目类型">
                          <select
                            value={fields.project_type}
                            onChange={(e) => setField('project_type', e.target.value)}
                          >
                            {['研发', '实施', '运维', '预研', '其他'].map((x) => (
                              <option key={x}>{x}</option>
                            ))}
                          </select>
                        </Field>
                        <Field label="优先级">
                          <select
                            value={fields.priority}
                            onChange={(e) => setField('priority', e.target.value)}
                          >
                            {['P0', 'P1', 'P2'].map((x) => (
                              <option key={x}>{x}</option>
                            ))}
                          </select>
                        </Field>
                      </div>
                    </div>

                    <div className="form-group">
                      <h4>组织与成员</h4>
                      <div className="form-grid">
                        <Field label="项目负责人">
                          <input value={fields.owner} onChange={(e) => setField('owner', e.target.value)} />
                        </Field>
                        <Field label="所属部门">
                          <input
                            value={fields.department}
                            onChange={(e) => setField('department', e.target.value)}
                          />
                        </Field>
                        <Field label="业务发起人">
                          <input
                            value={fields.sponsor}
                            onChange={(e) => setField('sponsor', e.target.value)}
                          />
                        </Field>
                        <Field label="核心成员">
                          <input
                            value={fields.members}
                            onChange={(e) => setField('members', e.target.value)}
                            placeholder="逗号分隔"
                          />
                        </Field>
                      </div>
                    </div>

                    <div className="form-group">
                      <h4>计划与预算</h4>
                      <div className="form-grid">
                        <Field label="计划开始">
                          <input
                            type="date"
                            value={fields.start_date}
                            onChange={(e) => setField('start_date', e.target.value)}
                          />
                        </Field>
                        <Field label="计划结束">
                          <input
                            type="date"
                            value={fields.end_date}
                            onChange={(e) => setField('end_date', e.target.value)}
                          />
                        </Field>
                        <Field label="预算（元）">
                          <input
                            type="number"
                            min={0}
                            step={0.01}
                            value={fields.budget}
                            onChange={(e) => setField('budget', parseFloat(e.target.value || '0') || 0)}
                          />
                        </Field>
                        <Field label="风险等级">
                          <select
                            value={fields.risk_level}
                            onChange={(e) => setField('risk_level', e.target.value)}
                          >
                            {['低', '中', '高'].map((x) => (
                              <option key={x}>{x}</option>
                            ))}
                          </select>
                        </Field>
                      </div>
                    </div>

                    <div className="form-group">
                      <h4>描述与备注</h4>
                      <div className="form-grid">
                        <Field label="项目概述" full>
                          <textarea
                            value={fields.description}
                            onChange={(e) => setField('description', e.target.value)}
                          />
                        </Field>
                        <Field label="目标与交付物" full>
                          <textarea value={fields.goals} onChange={(e) => setField('goals', e.target.value)} />
                        </Field>
                        <Field label="备注" full>
                          <textarea value={fields.remark} onChange={(e) => setField('remark', e.target.value)} />
                        </Field>
                      </div>
                    </div>
                  </form>

                  <div className="pm-footer-actions">
                    <div className="hint">{hint}</div>
                    <div className="btn-row">
                      <button type="button" className="btn btn-ghost" onClick={resetForm}>
                        重置
                      </button>
                      <button
                        type="button"
                        className="btn btn-ghost"
                        disabled={submitting}
                        onClick={async () => {
                          try {
                            const j = await saveDraft()
                            if (j) showToast('草稿已保存', 'ok')
                          } catch (e) {
                            showToast((e as Error).message, 'err')
                          }
                        }}
                      >
                        保存草稿
                      </button>
                      <button
                        type="button"
                        className="btn btn-primary"
                        disabled={submitting || parsing}
                        onClick={onSubmit}
                      >
                        {submitting ? '提交中…' : '确认并提交审批'}
                      </button>
                    </div>
                  </div>
                </>
              )}

              {step === 3 && (
                <div className="pm-result">
                  <div className={`pm-result-icon ${resultKind === 'submitted' ? 'ok' : 'draft'}`}>
                    {resultKind === 'submitted' ? '✓' : '○'}
                  </div>
                  <h3>{resultKind === 'submitted' ? '已提交审批' : '草稿已保存'}</h3>
                  <p>
                    {resultKind === 'submitted'
                      ? '项目已进入待审队列，可在审批中心处理，或在全部项目中查看进度。'
                      : '草稿已写入项目库，可稍后继续编辑并提交审批。'}
                  </p>
                  <div className="btn-row" style={{ justifyContent: 'center' }}>
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={() => {
                        setTab('approve')
                        loadApprove()
                      }}
                    >
                      去审批中心
                    </button>
                    <button
                      type="button"
                      className="btn btn-ghost"
                      onClick={() => {
                        setTab('list')
                        loadAll()
                        refreshStats()
                      }}
                    >
                      查看全部
                    </button>
                    <button type="button" className="btn btn-ghost" onClick={resetForm}>
                      再立一项
                    </button>
                  </div>
                </div>
              )}
            </section>
          )}

          {tab === 'approve' && (
            <section className="pm-view">
              <h3 className="pm-section-title">待审批队列</h3>
              <p className="sub">申请人提交后进入此列表；审批人默认为当前用户，驳回时请填写意见。</p>
              <ApproveList
                items={pending}
                onApprove={(id) => setReview({ id, action: 'approve' })}
                onReject={(id) => setReview({ id, action: 'reject' })}
                onView={setViewing}
              />
            </section>
          )}
        </div>
      </div>

      {review && (
        <div className="modal show" onClick={(e) => e.target === e.currentTarget && setReview(null)}>
          <div className="modal-card">
            <h3>{review.action === 'approve' ? '确认通过？' : '确认驳回？'}</h3>
            <p>
              {review.action === 'approve'
                ? '通过后项目状态变为「已通过」，流程结束。'
                : '驳回后申请人可修改表单并重新提交。驳回须填写审批意见。'}
            </p>
            <div className="field" style={{ marginBottom: 12 }}>
              <label>审批人</label>
              <input
                value={reviewer}
                readOnly={!!currentUser}
                onChange={(e) => !currentUser && setReviewer(e.target.value)}
                className={currentUser ? 'readonly' : undefined}
              />
              {currentUser && <div className="field-hint">已默认当前登录用户</div>}
            </div>
            <div className="field" style={{ marginBottom: 16 }}>
              <label>
                审批意见
                {review.action === 'reject' && <span className="req"> *</span>}
              </label>
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder={review.action === 'reject' ? '驳回时必填' : '可选'}
              />
            </div>
            <div className="btn-row" style={{ justifyContent: 'flex-end' }}>
              <button type="button" className="btn btn-ghost" onClick={() => setReview(null)}>
                取消
              </button>
              <button
                type="button"
                className={`btn ${review.action === 'approve' ? 'btn-ok' : 'btn-danger'}`}
                onClick={confirmReview}
              >
                {review.action === 'approve' ? '确认通过' : '确认驳回'}
              </button>
            </div>
          </div>
        </div>
      )}

      {viewing && (
        <div className="modal show" onClick={(e) => e.target === e.currentTarget && setViewing(null)}>
          <div className="modal-card modal-wide">
            <h3>{viewing.project_name || '项目详情'}</h3>
            <p className="sub" style={{ marginTop: 0 }}>
              {viewing.project_code || '无编号'} · {STATUS_LABEL[viewing.status]} · 更新 {viewing.updated_at || '—'}
            </p>
            <div className="view-grid">
              <div><span>类型</span>{viewing.project_type || '—'}</div>
              <div><span>负责人</span>{viewing.owner || '—'}</div>
              <div><span>部门</span>{viewing.department || '—'}</div>
              <div><span>优先级</span>{viewing.priority || '—'}</div>
              <div><span>预算</span>{formatBudget(viewing.budget)}</div>
              <div><span>风险</span>{viewing.risk_level || '—'}</div>
              <div className="full"><span>概述</span>{viewing.description || '—'}</div>
              <div className="full"><span>目标</span>{viewing.goals || '—'}</div>
            </div>
            {!!viewing.history?.length && (
              <div className="timeline">
                {[...viewing.history]
                  .slice(-5)
                  .reverse()
                  .map((h, i) => (
                    <div className="tl" key={i}>
                      {h.at} · {h.action} · {h.by}
                      {h.note ? ` · ${h.note}` : ''}
                    </div>
                  ))}
              </div>
            )}
            <div className="btn-row" style={{ justifyContent: 'flex-end', marginTop: 14 }}>
              <button type="button" className="btn btn-ghost" onClick={() => setViewing(null)}>
                关闭
              </button>
            </div>
          </div>
        </div>
      )}

      <div className={`toast ${toast ? `show ${toast.type}` : ''}`}>{toast?.msg}</div>

      {/* 若依 /project/parse 外壳已提供悬浮 AI，embed 模式下不再重复挂载 */}
      {!embed && tab === 'create' && (
        <AiAssistantFloat autoHint title="项目 AI 助手" onOpenChange={setAiOpen} />
      )}
    </div>
  )
}

function Field({
  label,
  required,
  full,
  children,
}: {
  label: string
  required?: boolean
  full?: boolean
  children: ReactNode
}) {
  return (
    <div className={`field ${full ? 'full' : ''}`}>
      <label>
        {label}
        {required && <span className="req"> *</span>}
      </label>
      {children}
    </div>
  )
}

function ApproveList({
  items,
  onApprove,
  onReject,
  onView,
}: {
  items: ProjectRecord[]
  onApprove: (id: string) => void
  onReject: (id: string) => void
  onView: (p: ProjectRecord) => void
}) {
  if (!items.length) return <div className="empty">暂无待审批项目</div>
  return (
    <div className="list">
      {items.map((p) => (
        <div className="item" key={p.id}>
          <div className="top">
            <div>
              <div className="name">{p.project_name || '未命名'}</div>
              <div className="meta">
                {p.project_code || '无编号'} · {p.project_type} · {p.owner || '未指定负责人'} · 预算{' '}
                {formatBudget(p.budget)}
                {p.source_file ? ` · 来源 ${p.source_file}` : ''}
              </div>
            </div>
            <span className={`badge ${p.status}`}>{STATUS_LABEL[p.status]}</span>
          </div>
          {!!p.history?.length && (
            <div className="timeline">
              {[...p.history]
                .slice(-5)
                .reverse()
                .map((h, i) => (
                  <div className="tl" key={i}>
                    {h.at} · {h.action} · {h.by}
                    {h.note ? ` · ${h.note}` : ''}
                  </div>
                ))}
            </div>
          )}
          <div className="ops">
            <button type="button" className="btn btn-ok" onClick={() => onApprove(p.id)}>
              通过
            </button>
            <button type="button" className="btn btn-danger" onClick={() => onReject(p.id)}>
              驳回
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => onView(p)}>
              查看
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
