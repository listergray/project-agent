import dayjs from 'dayjs'

export function formatDateTime(millis?: number | null): string {
  if (!millis) return '-'
  return dayjs(millis).format('YYYY-MM-DD HH:mm:ss')
}

export function formatDate(millis?: number | null): string {
  if (!millis) return '-'
  return dayjs(millis).format('YYYY-MM-DD')
}

export function formatDuration(ms?: number | null): string {
  if (!ms || ms < 0) return '-'
  if (ms < 1000) return `${ms}ms`
  const seconds = Math.floor(ms / 1000)
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ${seconds % 60}s`
  const hours = Math.floor(minutes / 60)
  return `${hours}h ${minutes % 60}m`
}

export function formatBytes(bytes?: number | null): string {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`
}
