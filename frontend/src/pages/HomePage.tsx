import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { NavBar } from '../components/NavBar'
import './HomePage.css'

export function HomePage() {
  const [chunks, setChunks] = useState('—')
  const [items, setItems] = useState('—')
  const [tip, setTip] = useState('')
  const tipTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    api
      .health()
      .then((j) => {
        if (j.milvus) {
          setChunks(String(j.milvus.kb_chunks ?? '—'))
          setItems(String(j.milvus.kb_item_names ?? '—'))
        }
      })
      .catch(() => {})
    return () => {
      if (tipTimer.current) clearTimeout(tipTimer.current)
    }
  }, [])

  function showComingSoon() {
    setTip('功能开发中...')
    if (tipTimer.current) clearTimeout(tipTimer.current)
    tipTimer.current = setTimeout(() => setTip(''), 2200)
  }

  return (
    <>
      <NavBar />
      <section className="home-hero">
        <h2>AI赋能</h2>
        <h1>智化工程</h1>
        <div className={`home-tip ${tip ? 'show' : ''}`} aria-live="polite">
          {tip || '\u00A0'}
        </div>
        <div className="card-grid">
          <Link className="glass chat" to="/chat">
            <div className="ic">💬</div>
            <h3>开始对话</h3>
            <p>RAG 知识库 · 7+7 节点 · 3 个 Function Calling 工具 · Milvus 向量库 · SSE 流式</p>
          </Link>
          <Link className="glass project" to="/projects">
            <div className="ic">📁</div>
            <h3>项目管理</h3>
            <p>人工录入 / 文件解析 · 表单确认 · 提交审批 · 完整项目立项流程</p>
          </Link>
          <button type="button" className="glass asset" onClick={showComingSoon}>
            <div className="ic">📦</div>
            <h3>资源管理</h3>
            <p>资产台账 · 库存盘点 · 编码与库位 · 出入库流转</p>
          </button>
          <button type="button" className="glass people" onClick={showComingSoon}>
            <div className="ic">👥</div>
            <h3>人员管理</h3>
            <p>组织架构 · 工号岗位 · 权限角色 · 人员档案</p>
          </button>
        </div>
      </section>
      <section className="home-stats">
        <div className="stat">
          <div className="v">{chunks}</div>
          <div className="l">向量库 chunk 数</div>
        </div>
        <div className="stat">
          <div className="v">{items}</div>
          <div className="l">已导入知识手册</div>
        </div>
        <div className="stat">
          <div className="v">7+7</div>
          <div className="l">RAG 导入/检索节点</div>
        </div>
      </section>
    </>
  )
}
