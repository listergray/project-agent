import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useLiveQuery } from 'dexie-react-hooks'
import { db } from '../db'

const OPENPLAN_SRC = '/openplan/editor/?embed=1'
const MSG = {
  ready: 'wodesuoyou:openplan-ready',
  load: 'wodesuoyou:openplan-load',
  save: 'wodesuoyou:openplan-save',
} as const

export function OpenPlanDesign() {
  const home = useLiveQuery(() => db.homes.get('main'))
  const iframeRef = useRef<HTMLIFrameElement>(null)
  const [ready, setReady] = useState(false)
  const [savedAt, setSavedAt] = useState<number | null>(null)
  const [missingBuild, setMissingBuild] = useState(false)

  const pushProject = useCallback(() => {
    const win = iframeRef.current?.contentWindow
    if (!win || !home) return
    let project: unknown = null
    if (home.openPlanJson) {
      try {
        project = JSON.parse(home.openPlanJson)
      } catch {
        project = null
      }
    }
    win.postMessage({ type: MSG.load, project }, '*')
  }, [home])

  useEffect(() => {
    void fetch('/openplan/index.html', { method: 'GET', cache: 'no-store' })
      .then((res) => {
        if (!res.ok) setMissingBuild(true)
      })
      .catch(() => setMissingBuild(true))
  }, [])

  useEffect(() => {
    function onMessage(event: MessageEvent) {
      if (event.data?.type === MSG.ready) {
        setReady(true)
        pushProject()
        return
      }
      if (event.data?.type === MSG.save && event.data.project) {
        const json = JSON.stringify(event.data.project)
        void db.homes.update('main', {
          openPlanJson: json,
          updatedAt: Date.now(),
        })
        setSavedAt(Date.now())
      }
    }
    window.addEventListener('message', onMessage)
    return () => window.removeEventListener('message', onMessage)
  }, [pushProject])

  useEffect(() => {
    if (ready) pushProject()
  }, [ready, pushProject])

  const onFrameLoad = useCallback(() => {
    setReady(true)
    window.setTimeout(() => pushProject(), 50)
  }, [pushProject])

  useEffect(() => {
    const frame = iframeRef.current
    if (!frame) return
    const onLoad = () => onFrameLoad()
    frame.addEventListener('load', onLoad)
    try {
      if (frame.contentDocument?.readyState === 'complete') onFrameLoad()
    } catch {
      /* ignore */
    }
    return () => frame.removeEventListener('load', onLoad)
  }, [onFrameLoad])

  if (!home) {
    return (
      <div className="openplan-shell">
        <p className="empty">读取中。</p>
      </div>
    )
  }

  if (missingBuild) {
    return (
      <div className="openplan-shell openplan-missing">
        <header className="openplan-bar">
          <Link to="/home" className="btn">
            ← 回小屋
          </Link>
        </header>
        <div className="openplan-missing-body">
          <h1>尚未构建 OpenPlan3D</h1>
          <p>
            在项目根目录执行 <code>npm run build:openplan</code>
            ，将编辑器输出到 <code>public/openplan</code> 后再打开本页。
          </p>
          <p className="section-lead">
            源码在 <code>third_party/openplan</code>（基于 MIT 的 OpenPlan3D /
            laanlabs/open3dFloorplan）。
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="openplan-shell">
      <header className="openplan-bar">
        <Link to="/home" className="btn">
          ← 回小屋
        </Link>
        <div className="openplan-bar-meta">
          <span className="dsh-kicker">OpenPlan3D</span>
          <span className="section-lead">
            {ready
              ? savedAt
                ? `已写入账本 · ${new Date(savedAt).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}`
                : '画墙、门窗、家具；改动会自动记入本机'
              : '载入编辑器…'}
          </span>
        </div>
      </header>
      <iframe
        ref={iframeRef}
        className="openplan-frame"
        title="OpenPlan3D 户型编辑"
        src={OPENPLAN_SRC}
        allow="fullscreen"
      />
    </div>
  )
}
