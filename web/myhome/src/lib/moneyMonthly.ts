import { db, type MoneyAsset } from '../db'
import { pad2, todayKey } from './dates'

const MAX_CATCH_UP = 24

function clampDay(year: number, month: number, day: number) {
  const last = new Date(year, month, 0).getDate()
  return Math.min(Math.max(1, day), last)
}

/** Build YYYY-MM-DD for `day` within year/month (1-based month). */
export function monthlyDate(year: number, month: number, day: number) {
  const d = clampDay(year, month, day)
  return `${year}-${pad2(month)}-${pad2(d)}`
}

/** Next monthly due date after `fromIso` (exclusive), on `day` of month. */
export function nextMonthlyDue(fromIso: string, day: number) {
  const [y, m] = fromIso.split('-').map(Number)
  let year = y
  let month = m + 1
  if (month > 12) {
    month = 1
    year += 1
  }
  return monthlyDate(year, month, day)
}

export function moneyMonthlyDay(asset: Pick<MoneyAsset, 'monthlyDay'>) {
  const n = Math.round(asset.monthlyDay || 1)
  return Math.min(28, Math.max(1, n || 1))
}

/** Next due date string, or '' if monthly add is off. */
export function peekNextMoneyMonthly(
  asset: Pick<MoneyAsset, 'monthlyAdd' | 'monthlyDay' | 'lastMonthlyAt'>,
  today = todayKey(),
) {
  if (!asset.monthlyAdd || asset.monthlyAdd <= 0) return ''
  const day = moneyMonthlyDay(asset)
  if (asset.lastMonthlyAt) return nextMonthlyDue(asset.lastMonthlyAt, day)
  const [y, m] = today.split('-').map(Number)
  return monthlyDate(y, m, day)
}

function dueMonthlyDates(
  asset: Pick<MoneyAsset, 'monthlyAdd' | 'monthlyDay' | 'lastMonthlyAt'>,
  today: string,
): string[] {
  if (!asset.monthlyAdd || asset.monthlyAdd <= 0) return []
  const day = moneyMonthlyDay(asset)
  const due: string[] = []

  let cursor = asset.lastMonthlyAt
  if (!cursor) {
    const [y, m] = today.split('-').map(Number)
    const thisDue = monthlyDate(y, m, day)
    if (today < thisDue) return []
    // Pretend last apply was previous month so thisDue is first due
    let py = y
    let pm = m - 1
    if (pm < 1) {
      pm = 12
      py -= 1
    }
    cursor = monthlyDate(py, pm, day)
  }

  let next = nextMonthlyDue(cursor, day)
  while (next <= today && due.length < MAX_CATCH_UP) {
    due.push(next)
    next = nextMonthlyDue(next, day)
  }
  return due
}

/** Apply all due monthly increments. Returns how many assets were updated. */
export async function syncMoneyMonthly(today = todayKey()) {
  const rows = await db.moneyAssets.toArray()
  let touched = 0
  for (const row of rows) {
    const dates = dueMonthlyDates(row, today)
    if (!dates.length) continue
    const add = row.monthlyAdd * dates.length
    await db.moneyAssets.update(row.id, {
      amount: Math.round((row.amount + add) * 100) / 100,
      lastMonthlyAt: dates[dates.length - 1],
      updatedAt: Date.now(),
    })
    touched += 1
  }
  return touched
}
