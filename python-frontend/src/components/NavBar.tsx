import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import brandMark from '../assets/brand-mark.svg'

type Props = {
  right?: ReactNode
  logoVariant?: 'blue' | 'violet'
}

export function NavBar({ right }: Props) {
  return (
    <nav className="nav">
      <Link className="brand" to="/">
        <img className="brand-logo" src={brandMark} alt="" width={34} height={34} />
        <span>Project Agent</span>
      </Link>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>{right}</div>
    </nav>
  )
}
