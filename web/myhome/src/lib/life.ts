import { useEffect, useState } from 'react'

export type LifeClock = {
  ready: boolean
  expired: boolean
  remainingDays: number
  hours: number
  minutes: number
  seconds: number
  livedRatio: number
  remainingRatio: number
}

export function computeLife(
  birthDate: string,
  expectedYears: number,
  nowMs: number,
): LifeClock {
  const empty: LifeClock = {
    ready: false,
    expired: false,
    remainingDays: 0,
    hours: 0,
    minutes: 0,
    seconds: 0,
    livedRatio: 0,
    remainingRatio: 1,
  }
  if (!birthDate) return empty

  const birth = new Date(`${birthDate}T00:00:00`)
  if (Number.isNaN(birth.getTime())) return empty

  const end = new Date(birth)
  end.setFullYear(end.getFullYear() + expectedYears)

  const remainingMs = end.getTime() - nowMs
  const totalMs = end.getTime() - birth.getTime()
  const livedMs = nowMs - birth.getTime()
  const livedRatio = totalMs > 0 ? Math.min(1, Math.max(0, livedMs / totalMs)) : 0

  if (remainingMs <= 0) {
    return {
      ready: true,
      expired: true,
      remainingDays: 0,
      hours: 0,
      minutes: 0,
      seconds: 0,
      livedRatio: 1,
      remainingRatio: 0,
    }
  }

  const remainingDays = Math.floor(remainingMs / 86_400_000)
  const rem = remainingMs % 86_400_000
  const hours = Math.floor(rem / 3_600_000)
  const minutes = Math.floor((rem % 3_600_000) / 60_000)
  const seconds = Math.floor((rem % 60_000) / 1000)

  return {
    ready: true,
    expired: false,
    remainingDays,
    hours,
    minutes,
    seconds,
    livedRatio,
    remainingRatio: 1 - livedRatio,
  }
}

export function useLife(birthDate: string | undefined, expectedYears: number | undefined) {
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), 1000)
    return () => window.clearInterval(id)
  }, [])

  return computeLife(birthDate ?? '', expectedYears ?? 80, now)
}

export function formatDayCount(n: number) {
  return n.toLocaleString('zh-CN')
}
