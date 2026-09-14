import { useEffect, useState } from 'react'
import { ChatPage } from '../pages/ChatPage'
import './AiAssistantFloat.css'

type Props = {
  autoHint?: boolean
  title?: string
  onOpenChange?: (open: boolean) => void
}

export function AiAssistantFloat({ autoHint = true, title = '项目 AI 助手', onOpenChange }: Props) {
  const [open, setOpen] = useState(false)
  const [hint, setHint] = useState(false)
  const [chatKey, setChatKey] = useState(0)

  function setOpenState(next: boolean) {
    setOpen(next)
    onOpenChange?.(next)
  }

  useEffect(() => {
    if (!autoHint) return
    const t = window.setTimeout(() => setHint(true), 600)
    const hide = window.setTimeout(() => setHint(false), 5600)
    return () => {
      window.clearTimeout(t)
      window.clearTimeout(hide)
    }
  }, [autoHint])

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setOpen(false)
        onOpenChange?.(false)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onOpenChange])

  return (
    <div className={`ai-float${open ? ' ai-float--open' : ''}`}>
      {!open && (
        <div className="ai-float-launcher">
          {hint && (
            <div className="ai-float-hint" role="status">
              {'您好，我是 AI 助手 ～'}
              <button type="button" className="ai-float-hint-x" aria-label="close-hint" onClick={() => setHint(false)}>
                ×
              </button>
            </div>
          )}
          <button
            type="button"
            className="ai-float-fab"
            title="AI"
            aria-label="open-ai-assistant"
            onClick={() => {
              setHint(false)
              setOpenState(true)
            }}
          >
            <RobotIcon />
          </button>
        </div>
      )}

      {open && (
        <aside className="ai-float-panel" role="dialog" aria-label={title}>
          <header className="ai-float-head">
            <div className="ai-float-tabs">
              <span className="ai-float-tab on">{title}</span>
            </div>
            <div className="ai-float-actions">
              <button type="button" className="ai-float-icon-btn" title="new" onClick={() => setChatKey((k) => k + 1)}>
                +
              </button>
              <button type="button" className="ai-float-icon-btn" title="close" onClick={() => setOpenState(false)}>
                ×
              </button>
            </div>
          </header>
          <div className="ai-float-body">
            <ChatPage key={chatKey} variant="panel" />
          </div>
          <footer className="ai-float-foot">
            {'内容由 AI 生成，仅供参考，您据此所作判断及操作均由您自行承担责任。'}
          </footer>
        </aside>
      )}
    </div>
  )
}

function RobotIcon() {
  return (
    <svg className="ai-float-robot" viewBox="0 0 64 64" width="40" height="40" aria-hidden>
      <circle cx="32" cy="32" r="32" fill="#2563eb" />
      <ellipse cx="32" cy="36" rx="18" ry="15" fill="#fff" />
      <rect x="18" y="28" width="28" height="12" rx="6" fill="#0f172a" />
      <rect x="22" y="31.5" width="20" height="5" rx="2.5" fill="#38bdf8" />
      <circle cx="22" cy="22" r="3.2" fill="#bfdbfe" />
      <circle cx="42" cy="22" r="3.2" fill="#bfdbfe" />
    </svg>
  )
}
