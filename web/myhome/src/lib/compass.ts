/** 房间朝向（主采光 / 门窗朝向） */
export const FACING_OPTIONS = [
  { id: '', label: '未记' },
  { id: 'N', label: '北' },
  { id: 'NE', label: '东北' },
  { id: 'E', label: '东' },
  { id: 'SE', label: '东南' },
  { id: 'S', label: '南' },
  { id: 'SW', label: '西南' },
  { id: 'W', label: '西' },
  { id: 'NW', label: '西北' },
] as const

export type FacingId = (typeof FACING_OPTIONS)[number]['id']

export const FACING_LABELS: Record<string, string> = Object.fromEntries(
  FACING_OPTIONS.filter((o) => o.id).map((o) => [o.id, o.label]),
)

/** 朝向对应方位角（度，0=北，顺时针） */
export const FACING_DEG: Record<string, number> = {
  N: 0,
  NE: 45,
  E: 90,
  SE: 135,
  S: 180,
  SW: 225,
  W: 270,
  NW: 315,
}
