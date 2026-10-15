import type { RoomItem } from '../db'
import { db } from '../db'
import { syncMaintainTasks } from './maintain'

export type ItemIndex = {
  byId: Map<string, RoomItem>
  childrenOf: Map<string, RoomItem[]>
}

export function indexItems(items: RoomItem[]): ItemIndex {
  const byId = new Map(items.map((item) => [item.id, item]))
  const childrenOf = new Map<string, RoomItem[]>()
  for (const item of items) {
    const key = item.parentId || ''
    const list = childrenOf.get(key) ?? []
    list.push(item)
    childrenOf.set(key, list)
  }
  for (const list of childrenOf.values()) {
    list.sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'))
  }
  return { byId, childrenOf }
}

export function itemPath(index: ItemIndex, itemId: string): RoomItem[] {
  const path: RoomItem[] = []
  let current = index.byId.get(itemId)
  while (current) {
    path.unshift(current)
    current = current.parentId ? index.byId.get(current.parentId) : undefined
  }
  return path
}

export function descendantsCount(index: ItemIndex, itemId: string): number {
  const kids = index.childrenOf.get(itemId) ?? []
  return kids.reduce((total, child) => total + 1 + descendantsCount(index, child.id), 0)
}

export type FlatItem = {
  item: RoomItem
  depth: number
  path: string[]
}

export function flattenSubtree(index: ItemIndex, rootId: string): FlatItem[] {
  const rows: FlatItem[] = []
  const rootName = index.byId.get(rootId)?.name ?? ''

  function walk(parentId: string, depth: number, path: string[]) {
    for (const child of index.childrenOf.get(parentId) ?? []) {
      const nextPath = [...path, child.name]
      rows.push({ item: child, depth, path: nextPath })
      walk(child.id, depth + 1, nextPath)
    }
  }

  walk(rootId, 0, rootName ? [rootName] : [])
  return rows
}

export function collectSubtreeIds(index: ItemIndex, rootId: string): string[] {
  const ids: string[] = [rootId]
  for (const child of index.childrenOf.get(rootId) ?? []) {
    ids.push(...collectSubtreeIds(index, child.id))
  }
  return ids
}

export function clampRoomGrid(
  gridX: number,
  gridY: number,
  gridW: number,
  gridH: number,
  planCols: number,
  planRows: number,
) {
  const w = Math.max(1, Math.min(planCols, Math.round(gridW)))
  const h = Math.max(1, Math.min(planRows, Math.round(gridH)))
  const x = Math.max(0, Math.min(planCols - w, Math.round(gridX)))
  const y = Math.max(0, Math.min(planRows - h, Math.round(gridY)))
  return { gridX: x, gridY: y, gridW: w, gridH: h }
}

export const DEFAULT_PLAN_COLS = 12
export const DEFAULT_PLAN_ROWS = 8
export const MIN_PLAN = 4
export const MAX_PLAN = 32

export function clampPlanSize(cols: number, rows: number) {
  return {
    planCols: Math.max(MIN_PLAN, Math.min(MAX_PLAN, Math.round(cols) || DEFAULT_PLAN_COLS)),
    planRows: Math.max(MIN_PLAN, Math.min(MAX_PLAN, Math.round(rows) || DEFAULT_PLAN_ROWS)),
  }
}

export async function deleteRoomItemTree(roomId: string, itemId: string) {
  const items = await db.roomItems.where('roomId').equals(roomId).toArray()
  const index = indexItems(items)
  const ids = collectSubtreeIds(index, itemId)
  const maintains = await db.maintains.toArray()
  await db.transaction('rw', [db.roomItems, db.maintains], async () => {
    for (const plan of maintains) {
      if (plan.roomItemId && ids.includes(plan.roomItemId)) await db.maintains.delete(plan.id)
    }
    await db.roomItems.bulkDelete(ids)
  })
  await syncMaintainTasks()
}
