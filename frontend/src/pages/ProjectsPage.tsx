import { useCallback, useEffect, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { NavBar } from '../components/NavBar'
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

export function ProjectsPage() {
  const [tab, setTab] = useState<Tab>('create')
  const [mode, setMode] = useState<Mode>('manual')
  const [step, setStep] = useState(1)
  const [stats, setStats] = useState<ProjectStats>({ total: 0, draft: 0, pending: 0, approved: 0, rejected: 0 })
  const [fields, setFields] = useState<ProjectFields>(emptyProjectFields())
  const [editingId, setEditingId] = useState<string | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [parsing, setParsing] = useState(false)
  const [banner, setBanner] = useState<{ kind: 'parse' | 'ok'; text: string } | null>(null)
  const [hint, setHint] = useState('当前：新立项 · 未保存')
  const [toast, setToast] = useState<{ msg: string; type: string } | null>(null)
  const [pending, setPending] = useState<ProjectRecord[]>([])
  const [all, setAll] = useState<ProjectRecord[]>([])
  const [filter, setFilter] = useState('')
  const [review, setReview] = useState<{ id: string; action: 'approve' | 'reject' } | null>(null)
  const [reviewer, setReviewer] = useState('审批人')
  const [comment, setComment] = useState('')

  const showToast = useCallback((msg: string, type = '') => {
    setToast({ msg, type })
    window.setTimeout(() => setToast(null), 3200)
  }, [])

  const refreshStats = useCallback(() => {
    api.projectStats().then(setStats).catch(() => {})
  }, [])

  useEffect(() => {
    refreshStats()
  }, [refreshStats])

  const loadApprove = useCallback(async () => {
    try {
      const j = await api.listProjects('pending')
      setPending(j.items)
    } catch {
      setPending([])
    }
  }, [])

  const loadAll = useCallback(async () => {
    try {
      const j = await api.listProjects(filter || undefined)
      setAll(j.items)
    } catch {
      setAll([])
    }
  }, [filter])

  useEffect(() => {
    if (tab === 'approve') loadApprove()
    if (tab === 'list') loadAll()
  }, [tab, loadApprove, loadAll])

  function setField<K extends keyof ProjectFields>(key: K, value: ProjectFields[K]) {
    setFields((prev) => ({ ...prev, [key]: value }))
  }

  function onPickFile(f: File | null) {
    if (!f) return
    const ext = '.' + (f.name.split('.').pop() || '').toLowerCase()
    if (!['.md', '.markdown', '.txt', '.pdf'].includes(ext)) {
      showToast('不支持的格式', 'err')
      return
    }
    if (f.size > 20 * 1024 * 1024) {
      showToast('文件超过 20MB', 'err')
      return
    }
    setFile(f)
    showToast('已选择文件', 'ok')
  }

  async function onParse() {
    if (!file) return
    setParsing(true)
    try {
      const j = await api.parseProject(file)
      setFields(j.fields)
      setEditingId(null)
      const conf = Math.round((j.confidence || 0) * 100)
      setBanner({
        kind: 'parse',
        text: `已解析「${j.filename}」· 方式 ${j.method} · 置信度 ${conf}% · 请人工确认后提交`,
      })
      setHint(`解析回填 · 置信度 ${conf}% · 尚未保存`)
      setStep(2)
      showToast('解析完成，请确认表单', 'ok')
    } catch (e) {
      showToast('解析失败: ' + (e as Error).message, 'err')
    } finally {
      setParsing(false)
    }
  }

  async function saveDraft() {
    if (!fields.project_name.trim()) {
      showToast('请填写项目名称', 'err')
      return null
    }
    const j = editingId
      ? await api.updateProject(editingId, fields)
      : await api.createProject(fields)
    setEditingId(j.id)
    setHint(`草稿已保存 · ID ${j.id}`)
    setStep(3)
    refreshStats()
    return j
  }

  async function onSubmit() {
    try {
      const j = await saveDraft()
      if (!j) return
      const out = await api.submitProject(j.id)
      setHint(`已提交审批 · ${out.project_name}`)
      setBanner({
        kind: 'ok',
        text: '已提交审批，可在「审批中心」处理，或在「全部项目」查看进度。',
      })
      setStep(4)
      showToast('已提交审批', 'ok')
      refreshStats()
    } catch (e) {
      showToast((e as Error).message, 'err')
    }
  }

  async function confirmReview() {
    if (!review) return
    const action = review.action
    try {
      const j = (await api.reviewProject(review.id, {
        action,
        reviewer: reviewer || '审批人',
        comment: comment || '',
      })) as Awaited<ReturnType<typeof api.reviewProject>> & {
        rag_synced?: boolean
        rag_error?: string
      }
      setReview(null)
      setComment('')
      setStep(4)
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
    setFile(null)
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
    setStep(2)
    showToast('已载入到表单', 'ok')
  }

  return (
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

      <div className="proj-layout">
        <aside className="left-col">
          <h4>录入审批流程</h4>
          {[
            ['选择录入方式', '人工 / 文件解析'],
            ['填写与确认', '表单人工核对'],
            ['提交审批', '进入待审队列'],
            ['审批结论', '通过或驳回'],
          ].map(([a, b], i) => {
            const n = i + 1
            const cls = n < step ? 'done' : n === step ? 'active' : ''
            return (
              <div className={`step ${cls}`} key={n}>
                <div className="num">{n}</div>
                <div className="t">
                  <div className="a">{a}</div>
                  <div className="b">{b}</div>
                </div>
              </div>
            )
          })}
          <div className="mini-stats">
            <div className="mini-stat"><div className="v">{stats.draft}</div><div className="l">草稿</div></div>
            <div className="mini-stat"><div className="v">{stats.pending}</div><div className="l">待审批</div></div>
            <div className="mini-stat"><div className="v">{stats.approved}</div><div className="l">已通过</div></div>
            <div className="mini-stat"><div className="v">{stats.rejected}</div><div className="l">已驳回</div></div>
          </div>
        </aside>

        <main className="right-col">
          <div className="tabs">
            {([
              ['create', '新建立项'],
              ['approve', '审批中心'],
              ['list', '全部项目'],
            ] as const).map(([k, label]) => (
              <button key={k} className={`tab ${tab === k ? 'on' : ''}`} onClick={() => setTab(k)}>
                {label}
              </button>
            ))}
          </div>

          {tab === 'create' && (
            <section className="card">
              <h3>① 选择录入方式</h3>
              <p className="sub">可直接填表，也可上传 .md / .txt / .pdf，系统解析后回填表单供你确认。</p>
              <div className="mode-row">
                <div
                  className={`mode ${mode === 'manual' ? 'on' : ''}`}
                  onClick={() => {
                    setMode('manual')
                    setStep(2)
                  }}
                >
                  <div className="t">✍️ 人工录入</div>
                  <div className="d">空白表单，手动填写项目编号、负责人、预算等字段后提交。</div>
                </div>
                <div
                  className={`mode ${mode === 'file' ? 'on' : ''}`}
                  onClick={() => {
                    setMode('file')
                    setStep(2)
                  }}
                >
                  <div className="t">📤 文件上传解析</div>
                  <div className="d">上传立项文档，自动抽取字段 → 进入表单确认 → 再提交审批。</div>
                </div>
              </div>

              {mode === 'file' && (
                <div>
                  <label
                    className="drop"
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                      e.preventDefault()
                      onPickFile(e.dataTransfer.files?.[0] || null)
                    }}
                  >
                    <h4>拖拽立项文件到这里</h4>
                    <p>或点击选择 · 支持 .md / .txt / .pdf · 单文件 ≤ 20MB</p>
                    {file && (
                      <div className="file-chip">
                        📎 {file.name} · {(file.size / 1024).toFixed(1)} KB
                      </div>
                    )}
                    <input
                      type="file"
                      accept=".md,.markdown,.txt,.pdf"
                      hidden
                      onChange={(e) => onPickFile(e.target.files?.[0] || null)}
                    />
                  </label>
                  <div className="btn-row" style={{ marginBottom: 14 }}>
                    <button className="btn btn-primary" disabled={!file || parsing} onClick={onParse}>
                      {parsing ? '解析中…' : '解析并填入表单'}
                    </button>
                    <button
                      className="btn btn-ghost"
                      disabled={!file}
                      onClick={() => {
                        setFile(null)
                        setBanner(null)
                      }}
                    >
                      清除文件
                    </button>
                  </div>
                </div>
              )}

              {banner && <div className={`banner ${banner.kind} show`}>{banner.text}</div>}

              <h3>② 项目信息确认</h3>
              <p className="sub">解析或手填后请逐项核对；确认无误再保存草稿或提交审批。</p>

              <form
                onSubmit={(e: FormEvent) => {
                  e.preventDefault()
                  onSubmit()
                }}
              >
                <div className="form-grid">
                  <Field label="项目编号">
                    <input value={fields.project_code} onChange={(e) => setField('project_code', e.target.value)} placeholder="如 PRJ-2026-001" />
                  </Field>
                  <Field label="项目名称" required>
                    <input value={fields.project_name} onChange={(e) => setField('project_name', e.target.value)} required placeholder="必填" />
                  </Field>
                  <Field label="项目类型">
                    <select value={fields.project_type} onChange={(e) => setField('project_type', e.target.value)}>
                      {['研发', '实施', '运维', '预研', '其他'].map((x) => (
                        <option key={x}>{x}</option>
                      ))}
                    </select>
                  </Field>
                  <Field label="优先级">
                    <select value={fields.priority} onChange={(e) => setField('priority', e.target.value)}>
                      {['P0', 'P1', 'P2'].map((x) => (
                        <option key={x}>{x}</option>
                      ))}
                    </select>
                  </Field>
                  <Field label="项目负责人">
                    <input value={fields.owner} onChange={(e) => setField('owner', e.target.value)} />
                  </Field>
                  <Field label="所属部门">
                    <input value={fields.department} onChange={(e) => setField('department', e.target.value)} />
                  </Field>
                  <Field label="业务发起人">
                    <input value={fields.sponsor} onChange={(e) => setField('sponsor', e.target.value)} />
                  </Field>
                  <Field label="风险等级">
                    <select value={fields.risk_level} onChange={(e) => setField('risk_level', e.target.value)}>
                      {['低', '中', '高'].map((x) => (
                        <option key={x}>{x}</option>
                      ))}
                    </select>
                  </Field>
                  <Field label="计划开始">
                    <input type="date" value={fields.start_date} onChange={(e) => setField('start_date', e.target.value)} />
                  </Field>
                  <Field label="计划结束">
                    <input type="date" value={fields.end_date} onChange={(e) => setField('end_date', e.target.value)} />
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
                  <Field label="核心成员">
                    <input value={fields.members} onChange={(e) => setField('members', e.target.value)} placeholder="逗号分隔" />
                  </Field>
                  <Field label="项目概述" full>
                    <textarea value={fields.description} onChange={(e) => setField('description', e.target.value)} />
                  </Field>
                  <Field label="目标与交付物" full>
                    <textarea value={fields.goals} onChange={(e) => setField('goals', e.target.value)} />
                  </Field>
                  <Field label="备注" full>
                    <textarea value={fields.remark} onChange={(e) => setField('remark', e.target.value)} />
                  </Field>
                </div>
              </form>

              <div className="actions">
                <div className="hint">{hint}</div>
                <div className="btn-row">
                  <button className="btn btn-ghost" type="button" onClick={resetForm}>
                    重置
                  </button>
                  <button
                    className="btn btn-ghost"
                    type="button"
                    onClick={async () => {
                      try {
                        await saveDraft()
                        showToast('草稿已保存', 'ok')
                      } catch (e) {
                        showToast((e as Error).message, 'err')
                      }
                    }}
                  >
                    保存草稿
                  </button>
                  <button className="btn btn-primary" type="button" onClick={onSubmit}>
                    确认并提交审批
                  </button>
                </div>
              </div>
            </section>
          )}

          {tab === 'approve' && (
            <section className="card">
              <h3>待审批队列</h3>
              <p className="sub">申请人提交后进入此列表；审批人可填写意见后通过或驳回。</p>
              <ItemList
                items={pending}
                empty="暂无待审批项目"
                approve
                onApprove={(id) => setReview({ id, action: 'approve' })}
                onReject={(id) => setReview({ id, action: 'reject' })}
              />
            </section>
          )}

          {tab === 'list' && (
            <section className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginBottom: 12 }}>
                <div>
                  <h3 style={{ margin: 0 }}>全部项目</h3>
                  <p className="sub" style={{ margin: '6px 0 0' }}>
                    按最近更新排序 · 可查看状态流转历史
                  </p>
                </div>
                <select
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                  style={{ border: '1px solid var(--slate-200)', borderRadius: 999, padding: '7px 12px', fontSize: 13, background: '#fff' }}
                >
                  <option value="">全部状态</option>
                  <option value="draft">草稿</option>
                  <option value="pending">待审批</option>
                  <option value="approved">已通过</option>
                  <option value="rejected">已驳回</option>
                </select>
              </div>
              <ItemList items={all} empty="暂无项目" onEdit={continueEdit} />
            </section>
          )}
        </main>
      </div>

      {review && (
        <div className="modal show" onClick={(e) => e.target === e.currentTarget && setReview(null)}>
          <div className="modal-card">
            <h3>{review.action === 'approve' ? '确认通过？' : '确认驳回？'}</h3>
            <p>
              {review.action === 'approve'
                ? '通过后项目状态变为「已通过」，流程结束。'
                : '驳回后申请人可修改表单并重新提交。'}
            </p>
            <div className="field" style={{ marginBottom: 12 }}>
              <label>审批人</label>
              <input value={reviewer} onChange={(e) => setReviewer(e.target.value)} />
            </div>
            <div className="field" style={{ marginBottom: 16 }}>
              <label>审批意见</label>
              <textarea value={comment} onChange={(e) => setComment(e.target.value)} placeholder="可选" />
            </div>
            <div className="btn-row" style={{ justifyContent: 'flex-end' }}>
              <button className="btn btn-ghost" onClick={() => setReview(null)}>
                取消
              </button>
              <button className={`btn ${review.action === 'approve' ? 'btn-ok' : 'btn-danger'}`} onClick={confirmReview}>
                {review.action === 'approve' ? '确认通过' : '确认驳回'}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className={`toast ${toast ? `show ${toast.type}` : ''}`}>{toast?.msg}</div>
    </>
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

function ItemList({
  items,
  empty,
  approve,
  onApprove,
  onReject,
  onEdit,
}: {
  items: ProjectRecord[]
  empty: string
  approve?: boolean
  onApprove?: (id: string) => void
  onReject?: (id: string) => void
  onEdit?: (p: ProjectRecord) => void
}) {
  if (!items.length) return <div className="empty">{empty}</div>
  return (
    <div className="list">
      {items.map((p) => (
        <div className="item" key={p.id}>
          <div className="top">
            <div>
              <div className="name">{p.project_name || '未命名'}</div>
              <div className="meta">
                {p.project_code || '无编号'} · {p.project_type} · {p.owner || '未指定负责人'} · 预算 ¥
                {Number(p.budget || 0).toLocaleString()} · 更新 {p.updated_at || '—'}
                {p.source_file ? ` · 来源 ${p.source_file}` : ''}
              </div>
            </div>
            <span className={`badge ${p.status}`}>{STATUS_LABEL[p.status]}</span>
          </div>
          {p.description && <div className="meta" style={{ marginTop: 8 }}>{p.description.slice(0, 160)}</div>}
          {!!p.history?.length && (
            <div className="timeline">
              {[...p.history].slice(-5).reverse().map((h, i) => (
                <div className="tl" key={i}>
                  {h.at} · {h.action} · {h.by}
                  {h.note ? ` · ${h.note}` : ''}
                </div>
              ))}
            </div>
          )}
          <div className="ops">
            {approve && p.status === 'pending' && (
              <>
                <button className="btn btn-ok" onClick={() => onApprove?.(p.id)}>通过</button>
                <button className="btn btn-danger" onClick={() => onReject?.(p.id)}>驳回</button>
              </>
            )}
            {(p.status === 'draft' || p.status === 'rejected') && onEdit && (
              <button className="btn btn-ghost" onClick={() => onEdit(p)}>继续编辑</button>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
