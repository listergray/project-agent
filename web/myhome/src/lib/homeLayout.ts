import { db, type Room } from '../db'
import { nid } from './dates'
import {
  clampPlanSize,
  clampRoomGrid,
  DEFAULT_PLAN_COLS,
  DEFAULT_PLAN_ROWS,
  MAX_PLAN,
} from './itemTree'

export type LayoutPresetId = 'studio' | 'one-bedroom' | 'two-bedroom'

export type RoomKind =
  | 'living'
  | 'bedroom'
  | 'bedroom2'
  | 'kitchen'
  | 'bathroom'
  | 'balcony'
  | 'study'
  | 'closet'
  | 'hall'
  | 'custom'

export const LAYOUT_LABELS: Record<LayoutPresetId, string> = {
  studio: '开间',
  'one-bedroom': '一居室',
  'two-bedroom': '两室一厅',
}

export const ROOM_KIND_LABELS: Record<RoomKind, string> = {
  living: '客厅',
  bedroom: '卧室',
  bedroom2: '次卧',
  kitchen: '厨房',
  bathroom: '卫生间',
  balcony: '阳台',
  study: '书房',
  closet: '储物',
  hall: '玄关',
  custom: '房间',
}

export const ITEM_CATEGORIES = ['家具', '电器', '书籍', '装饰', '工具', '其他'] as const
export type ItemCategory = (typeof ITEM_CATEGORIES)[number]

/** 平面一格 = 1 米 */
export const CM_PER_CELL = 100

/** 由表单读厘米尺寸；空或非法 → 0（未记） */
export function readDimCm(value: FormDataEntryValue | null | undefined): number {
  const raw = String(value ?? '').trim()
  if (!raw) return 0
  const n = Number(raw)
  if (!Number.isFinite(n) || n < 0) return 0
  return Math.round(n * 10) / 10
}

/** 由表单读米，存为厘米（精确到 0.01 m） */
export function readMetersAsCm(value: FormDataEntryValue | null | undefined): number {
  const raw = String(value ?? '').trim()
  if (!raw) return 0
  const n = Number(raw)
  if (!Number.isFinite(n) || n < 0) return 0
  return Math.round(n * 100)
}

/** 米数字 → 厘米（精确到 0.01 m） */
export function metersNumberToCm(m: number): number {
  if (!Number.isFinite(m) || m < 0) return 0
  return Math.round(m * 100)
}

/** 米 → 格数（一格≈一米，向上取整占格，至少 1） */
export function metersToCells(
  value: FormDataEntryValue | null | undefined,
  fallback: number,
  max = MAX_PLAN,
): number {
  const raw = String(value ?? '').trim()
  const n = raw ? Number(raw) : fallback
  if (!Number.isFinite(n) || n <= 0) return Math.max(1, Math.min(max, Math.ceil(fallback) || 1))
  return Math.max(1, Math.min(max, Math.ceil(n - 1e-9)))
}

export function cmToMeters(cm: number): number {
  if (!cm) return 0
  return Math.round(cm) / 100
}

/** 两位小数米数字符串，供表单 defaultValue */
export function metersInputValue(cm: number): string {
  if (!cm) return ''
  return cmToMeters(cm).toFixed(2)
}

/** 由平面占格推算长宽（厘米）；高保持传入值 */
export function dimsFromCells(cols: number, rows: number, heightCm = 0) {
  return {
    lengthCm: Math.max(0, Math.round(cols)) * CM_PER_CELL,
    widthCm: Math.max(0, Math.round(rows)) * CM_PER_CELL,
    heightCm: heightCm > 0 ? heightCm : 0,
  }
}

/** 物件：长×宽×高 cm */
export function formatItemDims(item: {
  lengthCm?: number
  widthCm?: number
  heightCm?: number
}): string {
  const L = item.lengthCm ?? 0
  const W = item.widthCm ?? 0
  const H = item.heightCm ?? 0
  if (!L && !W && !H) return ''
  const part = (n: number) => (n > 0 ? String(n) : '—')
  return `${part(L)}×${part(W)}×${part(H)} cm`
}

/** 小屋 / 房间：按米显示，两位小数 */
export function formatPlanDims(item: {
  lengthCm?: number
  widthCm?: number
  heightCm?: number
}): string {
  const L = cmToMeters(item.lengthCm ?? 0)
  const W = cmToMeters(item.widthCm ?? 0)
  const H = cmToMeters(item.heightCm ?? 0)
  if (!L && !W && !H) return ''
  const part = (n: number) => (n > 0 ? n.toFixed(2) : '—')
  if (H > 0) return `${part(L)}×${part(W)}×${part(H)} m`
  return `${part(L)}×${part(W)} m`
}

export const ROOM_FACINGS = [
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

type RoomSeed = Omit<
  Room,
  'id' | 'homeId' | 'updatedAt' | 'lengthCm' | 'widthCm' | 'heightCm' | 'facing'
> & {
  lengthCm?: number
  widthCm?: number
  heightCm?: number
  facing?: string
}

const PRESETS: Record<LayoutPresetId, RoomSeed[]> = {
  studio: [{ name: '开间', kind: 'living', gridX: 0, gridY: 0, gridW: 12, gridH: 8, note: '', sortOrder: 0 }],
  'one-bedroom': [
    { name: '客厅', kind: 'living', gridX: 0, gridY: 0, gridW: 7, gridH: 5, note: '', sortOrder: 0 },
    { name: '卧室', kind: 'bedroom', gridX: 7, gridY: 0, gridW: 5, gridH: 5, note: '', sortOrder: 1 },
    { name: '厨房', kind: 'kitchen', gridX: 0, gridY: 5, gridW: 7, gridH: 3, note: '', sortOrder: 2 },
    { name: '卫生间', kind: 'bathroom', gridX: 7, gridY: 5, gridW: 5, gridH: 3, note: '', sortOrder: 3 },
  ],
  'two-bedroom': [
    { name: '客厅', kind: 'living', gridX: 0, gridY: 0, gridW: 7, gridH: 5, note: '', sortOrder: 0 },
    { name: '卧室', kind: 'bedroom', gridX: 7, gridY: 0, gridW: 5, gridH: 5, note: '', sortOrder: 1 },
    { name: '次卧', kind: 'bedroom2', gridX: 0, gridY: 5, gridW: 4, gridH: 3, note: '', sortOrder: 2 },
    { name: '厨房', kind: 'kitchen', gridX: 4, gridY: 5, gridW: 4, gridH: 3, note: '', sortOrder: 3 },
    { name: '卫生间', kind: 'bathroom', gridX: 8, gridY: 5, gridW: 4, gridH: 3, note: '', sortOrder: 4 },
  ],
}

export function presetRooms(preset: LayoutPresetId): RoomSeed[] {
  return PRESETS[preset].map((row) => ({ ...row }))
}

export async function ensureHome() {
  const home = await db.homes.get('main')
  if (!home) {
    const now = Date.now()
    await db.homes.add({
      id: 'main',
      name: '我的小屋',
      address: '',
      layoutPreset: 'two-bedroom',
      planCols: DEFAULT_PLAN_COLS,
      planRows: DEFAULT_PLAN_ROWS,
      ...dimsFromCells(DEFAULT_PLAN_COLS, DEFAULT_PLAN_ROWS),
      northOffsetDeg: 0,
      rentStartedAt: '',
      note: '两室一厅，一厨一卫',
      openPlanJson: '',
      updatedAt: now,
    })
    await applyLayoutPreset('two-bedroom', false)
    return
  }

  if (home.planCols == null || home.planRows == null) {
    await db.homes.update('main', {
      planCols: home.planCols ?? DEFAULT_PLAN_COLS,
      planRows: home.planRows ?? DEFAULT_PLAN_ROWS,
      updatedAt: Date.now(),
    })
  }

  if (home.openPlanJson == null) {
    await db.homes.update('main', { openPlanJson: '', updatedAt: Date.now() })
  }

  const items = await db.roomItems.count()
  if (home.layoutPreset === 'one-bedroom' && items === 0) {
    await applyLayoutPreset('two-bedroom', true)
    await db.homes.update('main', { note: '两室一厅，一厨一卫', updatedAt: Date.now() })
  }
}

/** 根据简易平面（房间 / 门窗 / 物件）生成 OpenPlan3D 工程并写入账本 */
export async function syncHomeToOpenPlan() {
  const { homeToOpenPlan, serializeOpenPlan } = await import('./homeToOpenPlan')
  const home = await db.homes.get('main')
  if (!home) return null
  const rooms = await db.rooms.where('homeId').equals('main').toArray()
  if (rooms.length === 0) return null
  const roomIds = rooms.map((r) => r.id)
  const items = (await db.roomItems.toArray()).filter((i) => roomIds.includes(i.roomId))
  const fixtures = (await db.roomFixtures.toArray()).filter((f) => roomIds.includes(f.roomId))
  const project = homeToOpenPlan({ home, rooms, items, fixtures })
  const json = serializeOpenPlan(project)
  await db.homes.update('main', { openPlanJson: json, updatedAt: Date.now() })
  return project
}

export async function applyLayoutPreset(preset: LayoutPresetId, replace: boolean) {
  const now = Date.now()
  const seeds = presetRooms(preset)

  if (replace) {
    const oldRooms = await db.rooms.where('homeId').equals('main').toArray()
    for (const room of oldRooms) {
      await db.roomItems.where('roomId').equals(room.id).delete()
    }
    await db.rooms.where('homeId').equals('main').delete()
  }

  const existing = await db.rooms.where('homeId').equals('main').count()
  if (existing > 0 && !replace) return

  await db.rooms.bulkAdd(
    seeds.map((seed) => ({
      ...seed,
      id: nid(),
      homeId: 'main',
      ...dimsFromCells(seed.gridW, seed.gridH, seed.heightCm ?? 0),
      facing: seed.facing ?? '',
      updatedAt: now,
    })),
  )
  const home = await db.homes.get('main')
  const planCols = home?.planCols ?? DEFAULT_PLAN_COLS
  const planRows = home?.planRows ?? DEFAULT_PLAN_ROWS
  await db.homes.update('main', {
    layoutPreset: preset,
    ...dimsFromCells(planCols, planRows, home?.heightCm ?? 0),
    updatedAt: now,
  })
}

export async function clampRoomsToPlan(homeId: string, planCols: number, planRows: number) {
  const rooms = await db.rooms.where('homeId').equals(homeId).toArray()
  const now = Date.now()
  for (const room of rooms) {
    const grid = clampRoomGrid(room.gridX, room.gridY, room.gridW, room.gridH, planCols, planRows)
    // 只钳制占格，不覆盖精确长宽（厘米可带小数米）
    if (
      grid.gridX !== room.gridX ||
      grid.gridY !== room.gridY ||
      grid.gridW !== room.gridW ||
      grid.gridH !== room.gridH
    ) {
      await db.rooms.update(room.id, { ...grid, updatedAt: now })
    }
  }
}

export async function updateHomePlanSize(planCols: number, planRows: number) {
  const size = clampPlanSize(planCols, planRows)
  const home = await db.homes.get('main')
  await db.homes.update('main', {
    ...size,
    ...dimsFromCells(size.planCols, size.planRows, home?.heightCm ?? 0),
    updatedAt: Date.now(),
  })
  await clampRoomsToPlan('main', size.planCols, size.planRows)
  return size
}

export async function addCustomRoom(name: string, kind: RoomKind = 'custom') {
  const home = await db.homes.get('main')
  const planCols = home?.planCols ?? DEFAULT_PLAN_COLS
  const planRows = home?.planRows ?? DEFAULT_PLAN_ROWS
  const count = await db.rooms.where('homeId').equals('main').count()
  const now = Date.now()
  const grid = clampRoomGrid(0, Math.min(planRows - 3, count * 2), 4, 3, planCols, planRows)
  const id = nid()
  await db.rooms.add({
    id,
    homeId: 'main',
    name: name.trim() || '新房间',
    kind,
    ...grid,
    ...dimsFromCells(grid.gridW, grid.gridH),
    facing: '',
    note: '',
    sortOrder: count,
    updatedAt: now,
  })
  return id
}

export async function placeRoomAt(
  gridX: number,
  gridY: number,
  opts?: { name?: string; kind?: RoomKind; gridW?: number; gridH?: number },
) {
  const home = await db.homes.get('main')
  const planCols = home?.planCols ?? DEFAULT_PLAN_COLS
  const planRows = home?.planRows ?? DEFAULT_PLAN_ROWS
  const count = await db.rooms.where('homeId').equals('main').count()
  const grid = clampRoomGrid(
    gridX,
    gridY,
    opts?.gridW ?? 3,
    opts?.gridH ?? 3,
    planCols,
    planRows,
  )
  const id = nid()
  await db.rooms.add({
    id,
    homeId: 'main',
    name: opts?.name?.trim() || `房间 ${count + 1}`,
    kind: opts?.kind ?? 'custom',
    ...grid,
    ...dimsFromCells(grid.gridW, grid.gridH),
    facing: '',
    note: '',
    sortOrder: count,
    updatedAt: Date.now(),
  })
  return id
}

export async function updateRoomGrid(
  roomId: string,
  gridX: number,
  gridY: number,
  gridW: number,
  gridH: number,
) {
  const home = await db.homes.get('main')
  const planCols = home?.planCols ?? DEFAULT_PLAN_COLS
  const planRows = home?.planRows ?? DEFAULT_PLAN_ROWS
  const room = await db.rooms.get(roomId)
  if (!room) return null
  const grid = clampRoomGrid(gridX, gridY, gridW, gridH, planCols, planRows)
  const sizeChanged = grid.gridW !== room.gridW || grid.gridH !== room.gridH
  // 仅拖拽改占格大小时，才把长宽同步为整米；纯移动保留精确尺寸
  const patch = sizeChanged
    ? { ...grid, ...dimsFromCells(grid.gridW, grid.gridH, room.heightCm ?? 0), updatedAt: Date.now() }
    : { ...grid, updatedAt: Date.now() }
  await db.rooms.update(roomId, patch)
  return grid
}

/** 批量只改位置（整体平移），不改长宽 */
export async function translateRooms(
  moves: Array<{ id: string; gridX: number; gridY: number }>,
) {
  const home = await db.homes.get('main')
  const planCols = home?.planCols ?? DEFAULT_PLAN_COLS
  const planRows = home?.planRows ?? DEFAULT_PLAN_ROWS
  const now = Date.now()
  await db.transaction('rw', db.rooms, async () => {
    for (const move of moves) {
      const room = await db.rooms.get(move.id)
      if (!room) continue
      const grid = clampRoomGrid(
        move.gridX,
        move.gridY,
        room.gridW,
        room.gridH,
        planCols,
        planRows,
      )
      await db.rooms.update(move.id, {
        gridX: grid.gridX,
        gridY: grid.gridY,
        updatedAt: now,
      })
    }
  })
}

/** 按米精确设置房间长宽高（0.01 m）；占格按米向上取整近似 */
export async function updateRoomMeters(
  roomId: string,
  lengthM: number,
  widthM: number,
  heightCm?: number,
  facing?: string,
) {
  const room = await db.rooms.get(roomId)
  if (!room) return null
  const home = await db.homes.get('main')
  const planCols = home?.planCols ?? DEFAULT_PLAN_COLS
  const planRows = home?.planRows ?? DEFAULT_PLAN_ROWS
  const lengthCm = metersNumberToCm(lengthM)
  const widthCm = metersNumberToCm(widthM)
  const grid = clampRoomGrid(
    room.gridX,
    room.gridY,
    Math.max(1, Math.ceil(lengthM - 1e-9)) || room.gridW,
    Math.max(1, Math.ceil(widthM - 1e-9)) || room.gridH,
    planCols,
    planRows,
  )
  const h = heightCm === undefined ? room.heightCm ?? 0 : heightCm
  const patch: Partial<Room> = {
    ...grid,
    lengthCm,
    widthCm,
    heightCm: h,
    updatedAt: Date.now(),
  }
  if (facing !== undefined) patch.facing = facing
  await db.rooms.update(roomId, patch)
  return patch
}

export async function deleteRoom(roomId: string) {
  await db.transaction('rw', [db.rooms, db.roomItems, db.maintains, db.roomFixtures], async () => {
    const items = await db.roomItems.where('roomId').equals(roomId).toArray()
    const itemIds = new Set(items.map((item) => item.id))
    const plans = await db.maintains.where('roomId').equals(roomId).toArray()
    for (const plan of plans) await db.maintains.delete(plan.id)
    for (const plan of await db.maintains.toArray()) {
      if (plan.roomItemId && itemIds.has(plan.roomItemId)) await db.maintains.delete(plan.id)
    }
    await db.roomFixtures.where('roomId').equals(roomId).delete()
    await db.roomItems.where('roomId').equals(roomId).delete()
    await db.rooms.delete(roomId)
  })
}
