import {
  db,
  type FixtureKind,
  type PlanComponent,
  type PlanComponentFamily,
  type Room,
  type WallSide,
} from '../db'
import { nid } from './dates'
import { defaultFixtureSize, FIXTURE_KINDS, FIXTURE_LABELS, wallLengthM } from './fixtures'
import { cmToMeters } from './homeLayout'
import { PROP_KEYS, PROP_LABELS, type PropKey } from './roomScene'

export const PLAN_COMPONENT_MIME = 'application/x-wodesuoyou-plan-component'

const FIXTURE_COLORS: Record<FixtureKind, string> = {
  entrance: '#fbbf24',
  door: '#fbbf24',
  window: '#38bdf8',
  sliding: '#a78bfa',
  french: '#38bdf8',
}

const PROP_COLORS: Partial<Record<PropKey, string>> = {
  bed: '#c4b5fd',
  sofa: '#93c5fd',
  desk: '#fdba74',
  table: '#fdba74',
  wardrobe: '#a5b4fc',
  fridge: '#67e8f9',
  chair: '#86efac',
  plant: '#4ade80',
  generic: '#94a3b8',
}

function defaultPropFootprint(typeKey: string): { widthM: number; depthM: number; heightM: number } {
  if (typeKey === 'bed') return { widthM: 2, depthM: 1.5, heightM: 0.5 }
  if (typeKey === 'sofa') return { widthM: 2, depthM: 0.9, heightM: 0.8 }
  if (typeKey === 'desk') return { widthM: 1.2, depthM: 0.6, heightM: 0.75 }
  if (typeKey === 'wardrobe') return { widthM: 1.2, depthM: 0.6, heightM: 2 }
  if (typeKey === 'fridge') return { widthM: 0.7, depthM: 0.7, heightM: 1.8 }
  if (typeKey === 'bag' || typeKey === 'backpack') return { widthM: 0.4, depthM: 0.3, heightM: 0.45 }
  return { widthM: 0.6, depthM: 0.6, heightM: 0.5 }
}

export function defaultCatalogSeed(): Omit<PlanComponent, 'id' | 'updatedAt'>[] {
  const fixtures = FIXTURE_KINDS.map((kind, index) => {
    const size = defaultFixtureSize(kind)
    return {
      name: FIXTURE_LABELS[kind],
      family: 'fixture' as const,
      typeKey: kind,
      widthM: size.widthM,
      depthM: 0.1,
      heightM: size.heightM,
      sillM: size.sillM,
      category: '构件',
      color: FIXTURE_COLORS[kind],
      note: '',
      sortOrder: index,
      builtin: true,
    }
  })
  const props: Array<{ name: string; typeKey: string; category: string }> = [
    { name: '床', typeKey: 'bed', category: '家具' },
    { name: '沙发', typeKey: 'sofa', category: '家具' },
    { name: '书桌', typeKey: 'desk', category: '家具' },
    { name: '书包', typeKey: 'bag', category: '随身' },
    { name: '物件', typeKey: 'generic', category: '其他' },
  ]
  return [
    ...fixtures,
    ...props.map((p, index) => {
      const foot = defaultPropFootprint(p.typeKey)
      return {
        name: p.name,
        family: 'prop' as const,
        typeKey: p.typeKey,
        widthM: foot.widthM,
        depthM: foot.depthM,
        heightM: foot.heightM,
        sillM: 0,
        category: p.category,
        color: PROP_COLORS[p.typeKey as PropKey] ?? '#94a3b8',
        note: '',
        sortOrder: 100 + index,
        builtin: true,
      }
    }),
  ]
}

export async function ensurePlanCatalog() {
  const count = await db.planComponents.count()
  if (count > 0) return
  const now = Date.now()
  await db.planComponents.bulkAdd(
    defaultCatalogSeed().map((row) => ({
      ...row,
      id: nid(),
      updatedAt: now,
    })),
  )
}

export async function addPlanComponent(
  partial: Partial<PlanComponent> & Pick<PlanComponent, 'name' | 'family'>,
) {
  const family = partial.family
  const typeKey =
    partial.typeKey?.trim() ||
    (family === 'fixture' ? 'window' : 'generic')
  const fixtureSize =
    family === 'fixture' && FIXTURE_KINDS.includes(typeKey as FixtureKind)
      ? defaultFixtureSize(typeKey as FixtureKind)
      : null
  const propFoot = family === 'prop' ? defaultPropFootprint(typeKey) : null
  const maxOrder = (await db.planComponents.toArray()).reduce(
    (m, row) => Math.max(m, row.sortOrder),
    0,
  )
  const id = nid()
  await db.planComponents.add({
    id,
    name: partial.name.trim() || '未命名',
    family,
    typeKey,
    widthM: partial.widthM ?? fixtureSize?.widthM ?? propFoot?.widthM ?? 0.6,
    depthM: partial.depthM ?? propFoot?.depthM ?? 0.1,
    heightM: partial.heightM ?? fixtureSize?.heightM ?? propFoot?.heightM ?? 0.5,
    sillM: partial.sillM ?? fixtureSize?.sillM ?? 0,
    category: partial.category?.trim() || (family === 'fixture' ? '构件' : '物件'),
    color:
      partial.color ||
      (family === 'fixture'
        ? FIXTURE_COLORS[typeKey as FixtureKind] ?? '#fbbf24'
        : PROP_COLORS[typeKey as PropKey] ?? '#94a3b8'),
    note: partial.note?.trim() ?? '',
    sortOrder: partial.sortOrder ?? maxOrder + 1,
    builtin: false,
    updatedAt: Date.now(),
  })
  return id
}

export async function deletePlanComponent(id: string) {
  await db.planComponents.delete(id)
}

export function roomMeters(room: Room) {
  return {
    lengthM: cmToMeters(room.lengthCm ?? 0) || room.gridW,
    widthM: cmToMeters(room.widthCm ?? 0) || room.gridH,
  }
}

/** 在房间局部坐标（米，原点在西北角）选最近墙，并算沿墙偏移 */
export function snapFixtureToWall(
  room: Room,
  localXM: number,
  localYM: number,
  widthM: number,
): { wall: WallSide; offsetM: number } {
  const { lengthM, widthM: depthM } = roomMeters(room)
  const dN = localYM
  const dS = depthM - localYM
  const dW = localXM
  const dE = lengthM - localXM
  const nearest = Math.min(dN, dS, dW, dE)
  let wall: WallSide = 'N'
  if (nearest === dS) wall = 'S'
  else if (nearest === dW) wall = 'W'
  else if (nearest === dE) wall = 'E'

  const wallLen = wallLengthM(room, wall)
  const raw =
    wall === 'N' || wall === 'S'
      ? localXM - widthM / 2
      : localYM - widthM / 2
  const offsetM = Math.max(0, Math.min(wallLen - widthM, raw))
  return { wall, offsetM }
}

export function itemOnPlan(item: {
  planXM?: number
  planWM?: number
}): boolean {
  return (item.planWM ?? 0) > 0 && (item.planXM ?? -1) >= 0
}

export function propPlanStyle(
  item: { planXM: number; planYM: number; planWM: number; planDM: number },
  room: Room,
): { left: string; top: string; width: string; height: string } {
  const { lengthM, widthM } = roomMeters(room)
  const w = Math.max(0.15, item.planWM) / lengthM
  const h = Math.max(0.15, item.planDM) / widthM
  const left = Math.max(0, Math.min(1 - w, item.planXM / lengthM))
  const top = Math.max(0, Math.min(1 - h, item.planYM / widthM))
  return {
    left: `${left * 100}%`,
    top: `${top * 100}%`,
    width: `${w * 100}%`,
    height: `${h * 100}%`,
  }
}

export async function placeComponentOnRoom(
  component: PlanComponent,
  room: Room,
  localXM: number,
  localYM: number,
) {
  if (component.family === 'fixture') {
    const kind = (FIXTURE_KINDS.includes(component.typeKey as FixtureKind)
      ? component.typeKey
      : 'window') as FixtureKind
    const widthM = component.widthM || defaultFixtureSize(kind).widthM
    const { wall, offsetM } = snapFixtureToWall(room, localXM, localYM, widthM)
    const id = nid()
    await db.roomFixtures.add({
      id,
      roomId: room.id,
      kind,
      name: component.name,
      wall,
      offsetM,
      widthM,
      heightM: component.heightM || defaultFixtureSize(kind).heightM,
      sillM: component.sillM,
      note: '',
      updatedAt: Date.now(),
    })
    return { kind: 'fixture' as const, id }
  }

  const { lengthM, widthM } = roomMeters(room)
  const planWM = Math.min(component.widthM || 0.6, lengthM)
  const planDM = Math.min(component.depthM || 0.6, widthM)
  const planXM = Math.max(0, Math.min(lengthM - planWM, localXM - planWM / 2))
  const planYM = Math.max(0, Math.min(widthM - planDM, localYM - planDM / 2))
  const propKey = component.typeKey.trim() || 'generic'
  const id = nid()
  await db.roomItems.add({
    id,
    roomId: room.id,
    parentId: '',
    propKey,
    name: component.name,
    category: component.category || '物件',
    lengthCm: Math.round(planWM * 100),
    widthCm: Math.round(planDM * 100),
    heightCm: Math.round((component.heightM || 0) * 100),
    planXM,
    planYM,
    planWM,
    planDM,
    note: '',
    updatedAt: Date.now(),
  })
  return { kind: 'prop' as const, id }
}

export function familyLabel(family: PlanComponentFamily) {
  return family === 'fixture' ? '构件' : '物件'
}

export function typeKeyOptions(family: PlanComponentFamily): Array<{ id: string; label: string }> {
  if (family === 'fixture') {
    return FIXTURE_KINDS.map((k) => ({ id: k, label: FIXTURE_LABELS[k] }))
  }
  return [
    ...PROP_KEYS.map((k) => ({ id: k, label: PROP_LABELS[k] })),
    { id: 'bag', label: '书包' },
  ]
}
