import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { NavBar } from '../components/NavBar'
import './UploadPage.css'

type PreviewResult = {
  item?: { pk?: string; name?: string; category?: string; summary?: string }
  file_meta?: { name?: string; size_bytes?: number }
  chunks_total?: number
  chunks_preview?: Array<{
    seq: number
    title_path?: string
    content_preview?: string
    char_count?: number
  }>
  stats?: {
    before?: { kb_chunks?: number; kb_item_names?: number }
    after?: { kb_chunks?: number; kb_item_names?: number }
    delta_chunks?: number
    delta_items?: number
  }
  elapsed_ms?: number
  trace_id?: string
}

export function UploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const [step, setStep] = useState(1)
  const [busy, setBusy] = useState(false)
  const [progress, setProgress] = useState(0)
  const [stage, setStage] = useState('')
  const [result, setResult] = useState<PreviewResult | null>(null)
  const [toast, setToast] = useState<{ msg: string; type: string } | null>(null)
  const [live, setLive] = useState({ chunks: '—', items: '—' })
  const [rollbackOpen, setRollbackOpen] = useState(false)

  function toastMsg(msg: string, type = '') {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 4000)
  }

  function refreshHealth() {
    api
      .health()
      .then((j) => {
        if (j.milvus) {
          setLive({
            chunks: String(j.milvus.kb_chunks ?? '—'),
            items: String(j.milvus.kb_item_names ?? '—'),
          })
        }
      })
      .catch(() => {})
  }

  useEffect(() => {
    refreshHealth()
  }, [])

  function onPick(f: File | null) {
    if (!f) return
    const ext = '.' + (f.name.split('.').pop() || '').toLowerCase()
    if (!['.md', '.markdown', '.txt', '.pdf'].includes(ext)) {
      toastMsg('不支持的格式', 'err')
      return
    }
    if (f.size > 50 * 1024 * 1024) {
      toastMsg('超过 50MB', 'err')
      return
    }
    setFile(f)
    setResult(null)
    setStep(2)
    toastMsg('已添加文件', 'ok')
  }

  async function parse() {
    if (!file) return
    setBusy(true)
    setProgress(15)
    setStage('上传文件…')
    const timer = setInterval(() => {
      setProgress((p) => (p < 75 ? p + 4 : p))
    }, 300)
    const t0 = performance.now()
    try {
      const j = (await api.ragPreview(file)) as PreviewResult
      clearInterval(timer)
      setProgress(100)
      setStage('入库完成')
      j.elapsed_ms = Math.round(performance.now() - t0)
      setResult(j)
      setStep(3)
      toastMsg(`已入库「${j.item?.name || ''}」共 ${j.chunks_total} chunks`, 'ok')
      refreshHealth()
    } catch (e) {
      clearInterval(timer)
      toastMsg('解析失败: ' + (e as Error).message, 'err')
    } finally {
      setBusy(false)
      setTimeout(() => setProgress(0), 600)
    }
  }

  async function rollback() {
    const pk = result?.item?.pk
    if (!pk) return
    try {
      await api.ragRollback(pk)
      setRollbackOpen(false)
      setResult(null)
      setFile(null)
      setStep(1)
      toastMsg('已撤销本次导入', 'ok')
      refreshHealth()
    } catch (e) {
      toastMsg('撤销失败: ' + (e as Error).message, 'err')
    }
  }

  return (
    <>
      <NavBar
        right={
          <>
            <Link className="ghost-btn" to="/">← 导航</Link>
            <Link className="ghost-btn" to="/chat">对话</Link>
          </>
        }
      />

      <section className="up-hero">
        <h2>知识库 · 导入流水线</h2>
        <h1>把业务文档变成可被提问的知识</h1>
        <p>支持 .md / .txt / .pdf · 解析预览后确认保留或撤销本次导入。</p>
      </section>

      <div className="up-layout">
        <aside className="left-col">
          <h4>导入进度</h4>
          {[
            ['选择文件', '拖拽或点击'],
            ['解析入库', '7 节点流水线'],
            ['预览确认', '保留或撤销'],
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
          <div className="live-status">
            <div className="row"><span>文件</span><b>{file ? 1 : 0}</b></div>
            <div className="row"><span>chunks</span><b>{live.chunks}</b></div>
            <div className="row"><span>items</span><b>{live.items}</b></div>
          </div>
        </aside>

        <main className="right-col">
          <label
            className="drop"
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault()
              onPick(e.dataTransfer.files?.[0] || null)
            }}
          >
            <div className="icon-wrap">📤</div>
            <h3>拖拽文件到这里</h3>
            <p className="sub">或点击选择 · .md / .txt / .pdf · ≤ 50MB</p>
            {file && <div className="file-chip">📎 {file.name}</div>}
            <input
              type="file"
              accept=".md,.markdown,.txt,.pdf"
              hidden
              onChange={(e) => onPick(e.target.files?.[0] || null)}
            />
          </label>

          {progress > 0 && (
            <div className="progress-card">
              <div className="head">
                <span>{stage}</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <div className="bar-wrap">
                <div className="bar-fill" style={{ width: `${progress}%` }} />
              </div>
            </div>
          )}

          <div className="actions">
            <div className="hint">{file ? `已选 ${file.name}` : '请先选择文件'}</div>
            <div className="btn-row">
              <button
                className="btn btn-ghost"
                disabled={!file || busy}
                onClick={() => {
                  setFile(null)
                  setResult(null)
                  setStep(1)
                }}
              >
                清空
              </button>
              <button className="btn btn-primary" disabled={!file || busy} onClick={parse}>
                解析并入库
              </button>
            </div>
          </div>

          {result && (
            <div className="result">
              <div className="info-card">
                <div className="top">
                  <h3>{result.item?.name || '—'}</h3>
                  <span className="badge">{(result.item?.category || 'OTHER').toUpperCase()}</span>
                </div>
                <div className="summary">{result.item?.summary || '（无摘要）'}</div>
                <div className="meta">
                  <div><span>文件</span><b>{result.file_meta?.name || '—'}</b></div>
                  <div><span>分块</span><b>{result.chunks_total ?? '—'}</b></div>
                  <div><span>耗时</span><b>{result.elapsed_ms ? (result.elapsed_ms / 1000).toFixed(1) + ' s' : '—'}</b></div>
                  <div><span>增量</span><b>+{result.stats?.delta_chunks ?? 0} chunks</b></div>
                </div>
              </div>

              <div className="chunks-card">
                <div className="chunks-head">
                  <h4>分块预览</h4>
                  <span className="badge-count">{result.chunks_preview?.length || 0} / {result.chunks_total}</span>
                </div>
                <div className="chunks-list">
                  {(result.chunks_preview || []).map((c) => (
                    <div className="chunk" key={c.seq}>
                      <div className="row1">
                        <span className="seq">#{c.seq}</span>
                        <span className="path">{c.title_path || '(无路径)'}</span>
                        <span className="chars">{c.char_count} 字</span>
                      </div>
                      <div className="text">{c.content_preview}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="confirm-bar">
                <div>
                  <h5>已成功入库</h5>
                  <p>可前往对话提问，或撤销本次导入</p>
                </div>
                <div className="btn-row">
                  <button className="btn btn-danger" onClick={() => setRollbackOpen(true)}>
                    撤销本次导入
                  </button>
                  <Link className="btn btn-primary" to="/chat">
                    前往对话 →
                  </Link>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      {rollbackOpen && (
        <div className="modal show" onClick={(e) => e.target === e.currentTarget && setRollbackOpen(false)}>
          <div className="modal-card">
            <h3>确认撤销本次导入？</h3>
            <p>相关 chunks 与 item 将被删除，不可恢复。</p>
            <div className="btn-row" style={{ justifyContent: 'flex-end' }}>
              <button className="btn btn-ghost" onClick={() => setRollbackOpen(false)}>取消</button>
              <button className="btn btn-danger" onClick={rollback}>确认删除</button>
            </div>
          </div>
        </div>
      )}

      <div className={`toast ${toast ? `show ${toast.type}` : ''}`}>{toast?.msg}</div>
    </>
  )
}
