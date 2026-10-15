import type { PropKey } from '../../lib/roomScene'

type Props = { kind: PropKey; size?: number }

export function PixelPropIcon({ kind, size = 48 }: Props) {
  const s = size
  switch (kind) {
    case 'sofa':
      return (
        <svg viewBox="0 0 16 10" width={s} height={s * 0.62} aria-hidden className="pixel-icon">
          <rect x="1" y="4" width="14" height="4" fill="#8b6914" />
          <rect x="0" y="3" width="3" height="5" fill="#6d5210" />
          <rect x="13" y="3" width="3" height="5" fill="#6d5210" />
          <rect x="2" y="2" width="12" height="2" fill="#a67c1a" />
          <rect x="4" y="5" width="8" height="1" fill="#c49a2a" />
        </svg>
      )
    case 'tv':
      return (
        <svg viewBox="0 0 16 12" width={s} height={s * 0.75} aria-hidden className="pixel-icon">
          <rect x="2" y="1" width="12" height="8" fill="#2a3540" />
          <rect x="3" y="2" width="10" height="6" fill="#4a90c4" />
          <rect x="7" y="9" width="2" height="2" fill="#1a2228" />
          <rect x="5" y="11" width="6" height="1" fill="#1a2228" />
        </svg>
      )
    case 'fridge':
      return (
        <svg viewBox="0 0 10 16" width={s * 0.62} height={s} aria-hidden className="pixel-icon">
          <rect x="1" y="0" width="8" height="16" fill="#d8dde2" />
          <rect x="2" y="1" width="6" height="6" fill="#eef2f5" />
          <rect x="2" y="8" width="6" height="7" fill="#eef2f5" />
          <rect x="7" y="3" width="1" height="2" fill="#6d7a85" />
          <rect x="7" y="10" width="1" height="2" fill="#6d7a85" />
        </svg>
      )
    case 'bed':
      return (
        <svg viewBox="0 0 16 10" width={s} height={s * 0.62} aria-hidden className="pixel-icon">
          <rect x="0" y="4" width="16" height="5" fill="#7a8f72" />
          <rect x="1" y="2" width="4" height="3" fill="#d4dbe0" />
          <rect x="1" y="5" width="14" height="3" fill="#9aaea0" />
        </svg>
      )
    case 'desk':
      return (
        <svg viewBox="0 0 14 10" width={s} height={s * 0.71} aria-hidden className="pixel-icon">
          <rect x="1" y="3" width="12" height="2" fill="#8b6914" />
          <rect x="2" y="5" width="2" height="4" fill="#6d5210" />
          <rect x="10" y="5" width="2" height="4" fill="#6d5210" />
          <rect x="5" y="1" width="4" height="2" fill="#4a90c4" />
        </svg>
      )
    case 'table':
      return (
        <svg viewBox="0 0 12 10" width={s} height={s * 0.83} aria-hidden className="pixel-icon">
          <rect x="1" y="2" width="10" height="2" fill="#a67c1a" />
          <rect x="2" y="4" width="1" height="5" fill="#6d5210" />
          <rect x="9" y="4" width="1" height="5" fill="#6d5210" />
        </svg>
      )
    case 'wardrobe':
      return (
        <svg viewBox="0 0 10 14" width={s * 0.65} height={s} aria-hidden className="pixel-icon">
          <rect x="1" y="0" width="8" height="14" fill="#6d5210" />
          <rect x="2" y="1" width="3" height="12" fill="#8b6914" />
          <rect x="6" y="1" width="2" height="12" fill="#a67c1a" />
          <rect x="4" y="6" width="1" height="2" fill="#1a2228" />
        </svg>
      )
    case 'chair':
      return (
        <svg viewBox="0 0 10 12" width={s * 0.75} height={s} aria-hidden className="pixel-icon">
          <rect x="2" y="0" width="6" height="4" fill="#8b6914" />
          <rect x="1" y="4" width="8" height="2" fill="#a67c1a" />
          <rect x="2" y="6" width="1" height="5" fill="#6d5210" />
          <rect x="7" y="6" width="1" height="5" fill="#6d5210" />
        </svg>
      )
    case 'lamp':
      return (
        <svg viewBox="0 0 8 14" width={s * 0.55} height={s} aria-hidden className="pixel-icon">
          <rect x="3" y="5" width="2" height="8" fill="#6d5210" />
          <rect x="1" y="0" width="6" height="5" fill="#e8c84a" />
          <rect x="2" y="1" width="4" height="3" fill="#f5dc6a" />
        </svg>
      )
    case 'shelf':
      return (
        <svg viewBox="0 0 12 14" width={s * 0.75} height={s} aria-hidden className="pixel-icon">
          <rect x="1" y="0" width="1" height="14" fill="#6d5210" />
          <rect x="10" y="0" width="1" height="14" fill="#6d5210" />
          <rect x="1" y="3" width="10" height="1" fill="#8b6914" />
          <rect x="1" y="7" width="10" height="1" fill="#8b6914" />
          <rect x="1" y="11" width="10" height="1" fill="#8b6914" />
          <rect x="3" y="1" width="2" height="2" fill="#9a3b32" />
          <rect x="6" y="5" width="3" height="2" fill="#3d6b5f" />
        </svg>
      )
    case 'stove':
      return (
        <svg viewBox="0 0 12 10" width={s} height={s * 0.83} aria-hidden className="pixel-icon">
          <rect x="0" y="2" width="12" height="8" fill="#445058" />
          <rect x="2" y="4" width="3" height="3" fill="#1a2228" />
          <rect x="7" y="4" width="3" height="3" fill="#1a2228" />
          <rect x="3" y="5" width="1" height="1" fill="#c45c52" />
          <rect x="8" y="5" width="1" height="1" fill="#c45c52" />
        </svg>
      )
    case 'sink':
      return (
        <svg viewBox="0 0 14 10" width={s} height={s * 0.71} aria-hidden className="pixel-icon">
          <rect x="1" y="2" width="12" height="6" fill="#d8dde2" />
          <rect x="3" y="4" width="8" height="3" fill="#eef2f5" />
          <rect x="6" y="0" width="2" height="3" fill="#6d7a85" />
        </svg>
      )
    case 'toilet':
      return (
        <svg viewBox="0 0 10 12" width={s * 0.75} height={s} aria-hidden className="pixel-icon">
          <rect x="2" y="0" width="6" height="3" fill="#eef2f5" />
          <rect x="1" y="3" width="8" height="6" fill="#d8dde2" />
          <rect x="2" y="9" width="6" height="3" fill="#c5ced4" />
        </svg>
      )
    case 'shower':
      return (
        <svg viewBox="0 0 12 14" width={s * 0.75} height={s} aria-hidden className="pixel-icon">
          <rect x="1" y="0" width="10" height="14" fill="#d8dde2" />
          <rect x="2" y="1" width="8" height="12" fill="#eef2f5" />
          <rect x="4" y="3" width="1" height="1" fill="#4a90c4" />
          <rect x="7" y="5" width="1" height="1" fill="#4a90c4" />
          <rect x="5" y="8" width="1" height="1" fill="#4a90c4" />
        </svg>
      )
    case 'plant':
      return (
        <svg viewBox="0 0 10 12" width={s * 0.75} height={s} aria-hidden className="pixel-icon">
          <rect x="3" y="8" width="4" height="4" fill="#8b6914" />
          <rect x="4" y="6" width="2" height="2" fill="#6d5210" />
          <rect x="2" y="2" width="3" height="3" fill="#3d6b5f" />
          <rect x="5" y="1" width="3" height="3" fill="#4a8f72" />
          <rect x="4" y="4" width="2" height="2" fill="#3d6b5f" />
        </svg>
      )
    default:
      return (
        <svg viewBox="0 0 10 10" width={s * 0.7} height={s * 0.7} aria-hidden className="pixel-icon">
          <rect x="1" y="1" width="8" height="8" fill="#c5ced4" />
          <rect x="2" y="2" width="6" height="6" fill="#d4dbe0" />
          <rect x="4" y="4" width="2" height="2" fill="#9a3b32" />
        </svg>
      )
  }
}
