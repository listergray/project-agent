import { db } from '../db'
import { pad2 } from './dates'

export function dayHourId(date: string, hour: number) {
  return `${date}-${pad2(hour)}`
}

export function hourLabel(hour: number) {
  const next = (hour + 1) % 24
  return `${pad2(hour)}–${pad2(next)}`
}

/** 写入一格；空内容则除去该格 */
export async function writeDayHour(date: string, hour: number, content: string) {
  const id = dayHourId(date, hour)
  const text = content.trim()
  if (!text) {
    await db.dayHours.delete(id)
    return
  }
  await db.dayHours.put({
    id,
    date,
    hour,
    content: text,
    updatedAt: Date.now(),
  })
}
