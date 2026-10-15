import { db } from '../db'
import { nid } from './dates'
import type { RoomKind } from './homeLayout'
import { ensureDefaultMaintains } from './maintain'

export type PropKey =
  | 'sofa'
  | 'tv'
  | 'fridge'
  | 'bed'
  | 'desk'
  | 'wardrobe'
  | 'table'
  | 'chair'
  | 'lamp'
  | 'shelf'
  | 'stove'
  | 'sink'
  | 'toilet'
  | 'shower'
  | 'plant'
  | 'generic'

export const PROP_LABELS: Record<PropKey, string> = {
  sofa: '沙发',
  tv: '电视',
  fridge: '冰箱',
  bed: '床',
  desk: '书桌',
  wardrobe: '衣柜',
  table: '桌子',
  chair: '椅子',
  lamp: '灯',
  shelf: '架子',
  stove: '灶',
  sink: '洗手台',
  toilet: '马桶',
  shower: '淋浴',
  plant: '绿植',
  generic: '物件',
}

export const PROP_KEYS = Object.keys(PROP_LABELS) as PropKey[]

export const NESTABLE_PROPS = new Set<PropKey>(['sofa', 'bed', 'desk', 'table', 'shelf', 'chair'])

type SceneSlot = {
  propKey: PropKey
  left: number
  top: number
  w: number
  h: number
}

const SCENES: Partial<Record<RoomKind, SceneSlot[]>> = {
  living: [
    { propKey: 'sofa', left: 6, top: 58, w: 30, h: 24 },
    { propKey: 'tv', left: 34, top: 14, w: 28, h: 20 },
    { propKey: 'table', left: 38, top: 52, w: 18, h: 14 },
    { propKey: 'shelf', left: 72, top: 18, w: 14, h: 38 },
    { propKey: 'plant', left: 8, top: 22, w: 10, h: 16 },
    { propKey: 'lamp', left: 82, top: 62, w: 10, h: 18 },
  ],
  kitchen: [
    { propKey: 'fridge', left: 8, top: 22, w: 18, h: 52 },
    { propKey: 'stove', left: 36, top: 48, w: 22, h: 22 },
    { propKey: 'table', left: 62, top: 54, w: 24, h: 16 },
    { propKey: 'shelf', left: 68, top: 16, w: 22, h: 28 },
  ],
  bedroom: [
    { propKey: 'bed', left: 12, top: 48, w: 46, h: 30 },
    { propKey: 'desk', left: 66, top: 38, w: 24, h: 20 },
    { propKey: 'wardrobe', left: 72, top: 10, w: 18, h: 36 },
    { propKey: 'lamp', left: 18, top: 18, w: 10, h: 16 },
    { propKey: 'chair', left: 58, top: 62, w: 14, h: 16 },
  ],
  bedroom2: [
    { propKey: 'bed', left: 14, top: 50, w: 42, h: 28 },
    { propKey: 'desk', left: 64, top: 36, w: 26, h: 22 },
    { propKey: 'wardrobe', left: 8, top: 12, w: 16, h: 34 },
    { propKey: 'shelf', left: 70, top: 14, w: 18, h: 24 },
  ],
  bathroom: [
    { propKey: 'sink', left: 12, top: 28, w: 20, h: 18 },
    { propKey: 'toilet', left: 42, top: 54, w: 16, h: 20 },
    { propKey: 'shower', left: 68, top: 18, w: 22, h: 36 },
  ],
}

const DEFAULT_SCENE: SceneSlot[] = [
  { propKey: 'table', left: 30, top: 40, w: 24, h: 18 },
  { propKey: 'chair', left: 58, top: 50, w: 16, h: 18 },
  { propKey: 'shelf', left: 10, top: 20, w: 18, h: 30 },
]

export function sceneSlots(kind: string) {
  return SCENES[kind as RoomKind] ?? DEFAULT_SCENE
}

export function guessPropKey(name: string): PropKey {
  const n = name.toLowerCase()
  if (/沙发|sofa|couch/.test(n)) return 'sofa'
  if (/电视|tv|显示器|屏幕/.test(n)) return 'tv'
  if (/冰箱|fridge/.test(n)) return 'fridge'
  if (/床|bed/.test(n)) return 'bed'
  if (/书桌|desk|电脑桌/.test(n)) return 'desk'
  if (/衣柜|wardrobe|衣橱/.test(n)) return 'wardrobe'
  if (/茶几|餐桌|table|桌子/.test(n)) return 'table'
  if (/椅|chair/.test(n)) return 'chair'
  if (/灯|lamp/.test(n)) return 'lamp'
  if (/架|shelf|书柜/.test(n)) return 'shelf'
  if (/灶|stove/.test(n)) return 'stove'
  if (/洗手|sink/.test(n)) return 'sink'
  if (/马桶|toilet/.test(n)) return 'toilet'
  if (/淋浴|shower|浴/.test(n)) return 'shower'
  if (/植物|plant|绿植/.test(n)) return 'plant'
  return 'generic'
}

export function defaultRoomItems(kind: RoomKind) {
  const packs: Partial<
    Record<RoomKind, Array<{ name: string; propKey: PropKey; category: string }>>
  > = {
    living: [
      { name: '沙发', propKey: 'sofa', category: '家具' },
      { name: '电视', propKey: 'tv', category: '电器' },
      { name: '茶几', propKey: 'table', category: '家具' },
    ],
    kitchen: [{ name: '冰箱', propKey: 'fridge', category: '电器' }],
    bedroom: [
      { name: '床', propKey: 'bed', category: '家具' },
      { name: '书桌', propKey: 'desk', category: '家具' },
    ],
    bedroom2: [{ name: '床', propKey: 'bed', category: '家具' }],
    bathroom: [{ name: '洗手台', propKey: 'sink', category: '其他' }],
  }
  return packs[kind] ?? []
}

export function slotForProp(kind: string, propKey: PropKey, index: number) {
  const slots = sceneSlots(kind).filter((s) => s.propKey === propKey)
  if (slots[index]) return slots[index]
  const base = slots[0]
  if (base) return { ...base, left: base.left + index * 8, top: base.top + index * 4 }
  return { propKey, left: 10 + index * 12, top: 40, w: 16, h: 16 }
}

export async function ensureRoomScene(roomId: string, kind: RoomKind) {
  const count = await db.roomItems.where('roomId').equals(roomId).count()
  if (count > 0) return
  const seeds = defaultRoomItems(kind)
  if (!seeds.length) return
  const now = Date.now()
  const ids = seeds.map(() => nid())
  await db.roomItems.bulkAdd(
    seeds.map((seed, index) => ({
      id: ids[index],
      roomId,
      parentId: '',
      propKey: seed.propKey,
      name: seed.name,
      category: seed.category,
      lengthCm: 0,
      widthCm: 0,
      heightCm: 0,
      planXM: -1,
      planYM: 0,
      planWM: 0,
      planDM: 0,
      note: '',
      updatedAt: now,
    })),
  )
  if (kind === 'bathroom') {
    const sinkIndex = seeds.findIndex((seed) => seed.propKey === 'sink')
    if (sinkIndex >= 0) await ensureDefaultMaintains()
  }
}
