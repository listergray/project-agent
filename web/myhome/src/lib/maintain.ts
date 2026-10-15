import { db, type Maintain, type Task } from '../db'
import { addDays, nid, todayKey } from './dates'

export const MAINTAIN_SOURCE = 'maintain'

export function maintainDueDate(
  plan: Pick<Maintain, 'everyDays' | 'lastDoneAt' | 'enabled'>,
  today = todayKey(),
) {
  if (!plan.enabled || !plan.everyDays || plan.everyDays <= 0) return null
  if (!plan.lastDoneAt) return today
  return addDays(plan.lastDoneAt, plan.everyDays)
}

export function isMaintainDue(
  plan: Pick<Maintain, 'everyDays' | 'lastDoneAt' | 'enabled'>,
  today = todayKey(),
) {
  const due = maintainDueDate(plan, today)
  return due !== null && due <= today
}

async function pendingMaintainTask(planId: string) {
  return db.tasks
    .filter((t) => t.sourceKind === MAINTAIN_SOURCE && t.sourceId === planId && !t.done)
    .first()
}

async function clearPendingMaintainTasks(planId: string) {
  const rows = await db.tasks
    .filter((t) => t.sourceKind === MAINTAIN_SOURCE && t.sourceId === planId && !t.done)
    .toArray()
  await Promise.all(rows.map((row) => db.tasks.delete(row.id)))
}

export async function syncMaintainTasks(today = todayKey()) {
  const plans = await db.maintains.toArray()

  for (const plan of plans) {
    if (!plan.enabled || !plan.everyDays || plan.everyDays <= 0) {
      await clearPendingMaintainTasks(plan.id)
      continue
    }

    const due = maintainDueDate(plan, today)
    if (!due || due > today) {
      await clearPendingMaintainTasks(plan.id)
      continue
    }

    const existing = await pendingMaintainTask(plan.id)
    if (existing) {
      if (existing.date !== due || existing.title !== plan.title) {
        await db.tasks.update(existing.id, { date: due, title: plan.title })
      }
      continue
    }

    await db.tasks.add({
      id: nid(),
      title: plan.title,
      date: due,
      done: false,
      sourceKind: MAINTAIN_SOURCE,
      sourceId: plan.id,
      createdAt: Date.now(),
    })
  }
}

export async function completeMaintainTask(task: Task) {
  if (task.sourceKind !== MAINTAIN_SOURCE || !task.sourceId) return
  await db.maintains.update(task.sourceId, {
    lastDoneAt: task.date,
    updatedAt: Date.now(),
  })
}

export async function toggleMaintainTask(task: Task, done: boolean) {
  if (done) await completeMaintainTask(task)
  await db.tasks.update(task.id, { done })
  if (done) await syncMaintainTasks()
}

export async function markMaintainDone(planId: string, date = todayKey()) {
  await db.maintains.update(planId, { lastDoneAt: date, updatedAt: Date.now() })
  await syncMaintainTasks(date)
}

export async function linkMaintainFromItem(item: {
  id: string
  roomId: string
  name: string
  propKey: string
}) {
  const existing = await db.maintains.where('roomItemId').equals(item.id).first()
  if (existing) return existing.id

  const title =
    item.propKey === 'sink' || /洗手|sink/.test(item.name) ? '清理洗手台' : `${item.name} · 维护`
  const everyDays = item.propKey === 'sink' || /洗手|sink/.test(item.name) ? 7 : 30
  const id = nid()
  const now = Date.now()

  await db.maintains.add({
    id,
    title,
    everyDays,
    lastDoneAt: todayKey(),
    roomItemId: item.id,
    roomId: item.roomId,
    note: '',
    enabled: true,
    updatedAt: now,
  })
  await syncMaintainTasks()
  return id
}

export async function ensureDefaultMaintains() {
  const items = await db.roomItems.toArray()
  for (const item of items) {
    if (item.propKey !== 'sink' && !/洗手|sink/.test(item.name)) continue
    const count = await db.maintains.where('roomItemId').equals(item.id).count()
    if (count === 0) {
      await linkMaintainFromItem({
        id: item.id,
        roomId: item.roomId,
        name: item.name,
        propKey: item.propKey || 'sink',
      })
    }
  }
}
