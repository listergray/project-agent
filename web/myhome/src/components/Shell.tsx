import { useEffect, useRef, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { ASSET_KINDS } from '../lib/assetKinds'

const links = [
  { to: '/', label: '首页', end: true },
  { to: '/today', label: '今日' },
  { to: '/todos', label: '待办' },
  { to: '/goals', label: '目标' },
  { to: '/body', label: '身体' },
  { to: '/people', label: '交际' },
  { to: '/nine', label: '九宫' },
  { to: '/home', label: '小屋', prefix: true },
  { to: '/settings', label: '册上' },
] as const

export function Shell() {
  return (
    <div className="shell-bg">
      <header className="spine">
        <NavLink to="/" className="spine-brand" end>
          我的所有
        </NavLink>
        <nav>
          <AssetMenu />
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={'end' in link ? link.end : 'prefix' in link ? false : undefined}
              className={({ isActive }) => (isActive ? 'active' : undefined)}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <Outlet />
    </div>
  )
}

function AssetMenu() {
  const { pathname } = useLocation()
  const on = pathname.startsWith('/assets')
  const [open, setOpen] = useState(false)
  const box = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const close = (event: PointerEvent) => {
      if (!box.current?.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('pointerdown', close)
    return () => document.removeEventListener('pointerdown', close)
  }, [])

  useEffect(() => {
    setOpen(false)
  }, [pathname])

  return (
    <div ref={box} className={on ? 'nav-drop on' : 'nav-drop'}>
      <button
        type="button"
        className={on ? 'active' : undefined}
        aria-expanded={open}
        aria-haspopup="true"
        onClick={() => setOpen((value) => !value)}
      >
        资产
      </button>
      {open ? (
        <div className="nav-panel">
          <NavLink to="/assets" end>
            总览
          </NavLink>
          {ASSET_KINDS.map((item) => (
            <NavLink key={item.id} to={`/assets/${item.id}`}>
              {item.name}
            </NavLink>
          ))}
        </div>
      ) : null}
    </div>
  )
}
