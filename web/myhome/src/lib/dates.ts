const NUM = '〇一二三四五六七八九'

export function nid() {
  return crypto.randomUUID()
}

export function todayKey(d = new Date()) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export function addDays(iso: string, days: number) {
  const [y, m, d] = iso.split('-').map(Number)
  const date = new Date(y, m - 1, d)
  date.setDate(date.getDate() + days)
  return todayKey(date)
}

export function dayKeyToDate(iso: string) {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d)
}

export function formatLedgerDayKey(iso: string) {
  return formatLedgerDate(dayKeyToDate(iso))
}

function toHansDay(n: number) {
  if (n <= 10) return n === 10 ? '十' : NUM[n]
  if (n < 20) return `十${NUM[n - 10]}`
  const tens = Math.floor(n / 10)
  const ones = n % 10
  return `${NUM[tens]}十${ones ? NUM[ones] : ''}`
}

export function formatLedgerDate(date: Date) {
  const year = String(date.getFullYear())
    .split('')
    .map((ch) => NUM[Number(ch)])
    .join('')
  return `${year}年${toHansDay(date.getMonth() + 1)}月${toHansDay(date.getDate())}日`
}

export function formatShortDate(iso: string) {
  if (!iso) return '未记'
  const [, m, d] = iso.split('-')
  return `${Number(m)}月${Number(d)}日`
}

export function pad2(n: number) {
  return String(n).padStart(2, '0')
}

export function formatPeriod(startedAt: string, endedAt: string) {
  if (!startedAt && !endedAt) return ''
  if (startedAt && !endedAt) return `${startedAt} 至今`
  if (!startedAt) return endedAt
  return `${startedAt} – ${endedAt}`
}

export function daysUntilBirthday(iso: string, from = new Date()) {
  if (!iso) return null
  const parts = iso.split('-').map(Number)
  const month = parts.length === 3 ? parts[1] : parts[0]
  const day = parts.length === 3 ? parts[2] : parts[1]
  if (!month || !day) return null
  const year = from.getFullYear()
  const next = new Date(year, month - 1, day)
  next.setHours(0, 0, 0, 0)
  const start = new Date(from)
  start.setHours(0, 0, 0, 0)
  if (next < start) next.setFullYear(year + 1)
  return Math.round((next.getTime() - start.getTime()) / 86_400_000)
}
