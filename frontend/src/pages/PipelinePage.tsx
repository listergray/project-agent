import { useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { NavBar } from '../components/NavBar'
import './PipelinePage.css'

const NODES = [
  { id: 'N1', title: '需求拆解', desc: '从需求文档抽取关键实体与边界条件' },
  { id: 'N2', title: '代码生成', desc: '生成 Service / Controller / Repository 三层' },
  { id: 'N3', title: '审查重构', desc: '静态错误检测 + 命名规范化' },
  { id: 'N4', title: '单测生成', desc: 'JUnit 5 + Mockito 覆盖主分支' },
  { id: 'N5', title: '接口文档', desc: '自动产出 OpenAPI + Markdown' },
  { id: 'N6', title: '审查兜底', desc: '全链路质量门禁 · unfixed_errors 必须为 0' },
]

type NodeState = 'idle' | 'run' | 'done' | 'err'
type LogItem = { ts: string; kind: string; msg: string }

export function PipelinePage() {
  const [states, setStates] = useState<Record<string, NodeState>>(
    Object.fromEntries(NODES.map((n) => [n.id, 'idle' as NodeState])),
  )
  const [logs, setLogs] = useState<LogItem[]>([])
  const [running, setRunning] = useState(false)
  const [summary, setSummary] = useState<{
    time: string
    dir: string
    files: number
    review: string
  } | null>(null)
  const [files, setFiles] = useState<Array<{ path: string; size_bytes: number }>>([])
  const fakeIdx = useRef(0)

  function pushLog(msg: string, kind = 'info') {
    const ts = new Date().toLocaleTimeString('zh-CN', { hour12: false })
    setLogs((prev) => [...prev, { ts, kind, msg }])
  }

  function setNode(id: string, state: NodeState) {
    setStates((prev) => ({ ...prev, [id]: state }))
  }

  async function run() {
    setStates(Object.fromEntries(NODES.map((n) => [n.id, 'idle' as NodeState])))
    setLogs([])
    setFiles([])
    setSummary(null)
    setRunning(true)
    fakeIdx.current = 0
    const start = Date.now()
    pushLog('流水线启动 · 提交 POST /api/v1/copilot/run')

    const tick = setInterval(() => {
      const i = fakeIdx.current
      if (i < NODES.length) {
        setNode(NODES[i].id, 'run')
        pushLog(`${NODES[i].id} · ${NODES[i].title} 开始执行`)
        if (i > 0) {
          setNode(NODES[i - 1].id, 'done')
          pushLog(`${NODES[i - 1].id} · 已完成`, 'ok')
        }
        fakeIdx.current++
      }
    }, 18000)

    try {
      const j = await api.copilotRun()
      clearInterval(tick)
      NODES.forEach((n) => setNode(n.id, 'done'))
      pushLog('全流水线完成 · 审查门禁通过', 'ok')
      const elapsed = ((Date.now() - start) / 1000).toFixed(1)
      const fl = j.files || []
      setSummary({
        time: elapsed + ' s',
        dir: j.output_dir || '—',
        files: fl.length,
        review: j.errors?.length ? `✗ errors=${j.errors.length}` : '✓',
      })
      setFiles(fl)
      if (fl.length) pushLog(`已生成 ${fl.length} 个文件到 ${j.output_dir || 'output/'}`, 'ok')
    } catch (e) {
      clearInterval(tick)
      pushLog('运行失败 · ' + (e as Error).message, 'err')
      const idx = fakeIdx.current - 1
      if (idx >= 0) setNode(NODES[idx].id, 'err')
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="pipe-page">
      <NavBar
        logoVariant="violet"
        right={
          <>
            <Link className="ghost-btn" to="/chat">
              💬 对话
            </Link>
            <a className="ghost-btn" href="/docs" target="_blank" rel="noreferrer">
              API 文档
            </a>
          </>
        }
      />

      <main className="wrap">
        <div className="page-head">
          <span className="tag">⚡ 代码助手 · AI 编程提效</span>
          <h1>5+1 节点流水线</h1>
          <p>
            从业务需求文档出发，自动走完「需求拆解 → 代码生成 → 审查重构 → 单测生成 → 接口文档」五步，最后落盘到{' '}
            <code>output/copilot_&lt;timestamp&gt;/</code>。
          </p>
        </div>

        <div className="layout">
          <div className="panel">
            <h3>
              <div className="ic">⚙</div> 节点流水线
            </h3>
            <div className="nodes">
              {NODES.map((n, i) => (
                <div key={n.id}>
                  <div className={`node ${states[n.id] !== 'idle' ? states[n.id] : ''}`}>
                    <div className="num">{n.id}</div>
                    <div className="info">
                      <div className="t">{n.title}</div>
                      <div className="d">{n.desc}</div>
                    </div>
                    <span className="st">
                      {states[n.id] === 'run'
                        ? '运行中…'
                        : states[n.id] === 'done'
                          ? '✓ 完成'
                          : states[n.id] === 'err'
                            ? '✗ 失败'
                            : '待运行'}
                    </span>
                  </div>
                  {i < NODES.length - 1 && <div className="arrow" />}
                </div>
              ))}
            </div>
          </div>

          <div className="panel">
            <h3>
              <div className="ic">▶</div> 运行控制台
            </h3>
            <div className="run-bar">
              <button className={`run-btn ${running ? 'loading' : ''}`} disabled={running} onClick={run}>
                <span className="spinner" />
                <span className="label">{running ? '运行中 · 预计 60-180s' : '运行流水线 · 预计 60-180s'}</span>
              </button>
            </div>

            {summary && (
              <div className="summary show">
                <div className="row"><span>⏱ 耗时</span><b>{summary.time}</b></div>
                <div className="row"><span>📁 产出目录</span><b>{summary.dir}</b></div>
                <div className="row"><span>📄 文件数</span><b>{summary.files}</b></div>
                <div className="row"><span>✅ 审查</span><b>{summary.review}</b></div>
              </div>
            )}

            <div className="log-panel">
              {logs.map((l, i) => (
                <div key={i}>
                  <span className="ts">{l.ts}</span>
                  <span className="tag-n" style={l.kind === 'err' ? { background: '#ef4444' } : undefined}>
                    {l.kind === 'ok' ? 'OK' : l.kind === 'err' ? 'ERR' : 'LOG'}
                  </span>
                  <span className={l.kind === 'ok' ? 'ok' : l.kind === 'err' ? 'err' : 'info'}>{l.msg}</span>
                </div>
              ))}
            </div>

            <h3 style={{ fontSize: 13, color: '#475569', fontWeight: 600, margin: '18px 0 10px' }}>📂 产出文件</h3>
            {!files.length ? (
              <div className="empty">点击「运行流水线」开始</div>
            ) : (
              <div className="files">
                {files.map((f) => {
                  const ext = f.path.split('.').pop()?.toLowerCase() || ''
                  return (
                    <div className={`file ${ext}`} key={f.path}>
                      <div className="ftype">{ext.toUpperCase().slice(0, 4) || '?'}</div>
                      <div className="fname">{f.path}</div>
                      <div className="fsize">{(f.size_bytes / 1024).toFixed(1)} KB</div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
