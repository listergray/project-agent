import type { RoomKind } from '../../lib/homeLayout'
import type { PropKey } from '../../lib/roomScene'

type RoomMarkProps = { kind: string; accent?: boolean }

export function RoomMark({ kind, accent }: RoomMarkProps) {
  const stroke = accent ? 'rgba(255,255,255,0.9)' : 'rgba(255,255,255,0.55)'
  const fill = accent ? 'rgba(255,255,255,0.18)' : 'rgba(255,255,255,0.08)'
  switch (kind as RoomKind) {
    case 'living':
      return (
        <svg viewBox="0 0 64 48" className="dsh-mark" aria-hidden>
          <rect x="6" y="22" width="28" height="14" rx="3" fill={fill} stroke={stroke} strokeWidth="1.5" />
          <rect x="40" y="10" width="18" height="12" rx="2" fill={fill} stroke={stroke} strokeWidth="1.5" />
          <circle cx="49" cy="36" r="5" fill="none" stroke={stroke} strokeWidth="1.5" />
        </svg>
      )
    case 'bedroom':
    case 'bedroom2':
      return (
        <svg viewBox="0 0 64 48" className="dsh-mark" aria-hidden>
          <rect x="8" y="20" width="40" height="16" rx="3" fill={fill} stroke={stroke} strokeWidth="1.5" />
          <rect x="10" y="12" width="14" height="10" rx="2" fill={fill} stroke={stroke} strokeWidth="1.5" />
          <line x1="52" y1="18" x2="52" y2="40" stroke={stroke} strokeWidth="1.5" />
        </svg>
      )
    case 'kitchen':
      return (
        <svg viewBox="0 0 64 48" className="dsh-mark" aria-hidden>
          <rect x="10" y="14" width="16" height="26" rx="2" fill={fill} stroke={stroke} strokeWidth="1.5" />
          <rect x="34" y="24" width="20" height="16" rx="2" fill={fill} stroke={stroke} strokeWidth="1.5" />
          <circle cx="42" cy="32" r="3" fill="none" stroke={stroke} strokeWidth="1.2" />
        </svg>
      )
    case 'bathroom':
      return (
        <svg viewBox="0 0 64 48" className="dsh-mark" aria-hidden>
          <rect x="12" y="12" width="18" height="12" rx="2" fill={fill} stroke={stroke} strokeWidth="1.5" />
          <ellipse cx="42" cy="30" rx="10" ry="8" fill={fill} stroke={stroke} strokeWidth="1.5" />
          <path d="M22 24v14" stroke={stroke} strokeWidth="1.5" />
        </svg>
      )
    default:
      return (
        <svg viewBox="0 0 64 48" className="dsh-mark" aria-hidden>
          <rect x="12" y="10" width="40" height="28" rx="4" fill={fill} stroke={stroke} strokeWidth="1.5" />
          <line x1="20" y1="20" x2="44" y2="20" stroke={stroke} strokeWidth="1.2" />
          <line x1="20" y1="28" x2="36" y2="28" stroke={stroke} strokeWidth="1.2" />
        </svg>
      )
  }
}

export function PropMark({ kind }: { kind: PropKey | string }) {
  const stroke = 'rgba(255,255,255,0.55)'
  const fill = 'rgba(255,255,255,0.1)'
  switch (kind) {
    case 'sofa':
      return (
        <svg viewBox="0 0 48 36" className="dsh-mark sm" aria-hidden>
          <rect x="4" y="14" width="40" height="12" rx="3" fill={fill} stroke={stroke} />
          <rect x="2" y="10" width="8" height="16" rx="2" fill={fill} stroke={stroke} />
          <rect x="38" y="10" width="8" height="16" rx="2" fill={fill} stroke={stroke} />
        </svg>
      )
    case 'tv':
      return (
        <svg viewBox="0 0 48 36" className="dsh-mark sm" aria-hidden>
          <rect x="8" y="6" width="32" height="20" rx="2" fill={fill} stroke={stroke} />
          <line x1="24" y1="26" x2="24" y2="30" stroke={stroke} />
          <line x1="16" y1="30" x2="32" y2="30" stroke={stroke} />
        </svg>
      )
    case 'fridge':
      return (
        <svg viewBox="0 0 48 36" className="dsh-mark sm" aria-hidden>
          <rect x="14" y="2" width="20" height="32" rx="2" fill={fill} stroke={stroke} />
          <line x1="14" y1="14" x2="34" y2="14" stroke={stroke} />
        </svg>
      )
    case 'bed':
      return (
        <svg viewBox="0 0 48 36" className="dsh-mark sm" aria-hidden>
          <rect x="4" y="16" width="40" height="12" rx="2" fill={fill} stroke={stroke} />
          <rect x="6" y="8" width="12" height="10" rx="2" fill={fill} stroke={stroke} />
        </svg>
      )
    default:
      return (
        <svg viewBox="0 0 48 36" className="dsh-mark sm" aria-hidden>
          <rect x="10" y="8" width="28" height="20" rx="4" fill={fill} stroke={stroke} />
        </svg>
      )
  }
}
