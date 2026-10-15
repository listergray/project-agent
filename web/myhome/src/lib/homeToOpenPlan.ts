import type { Home, Room, RoomFixture, RoomItem } from '../db'
import { CM_PER_CELL } from './homeLayout'

type Point = { x: number; y: number }

type Wall = {
  id: string
  start: Point
  end: Point
  thickness: number
  height: number
  color: string
}

type Door = {
  id: string
  wallId: string
  position: number
  width: number
  height: number
  type: 'single' | 'double' | 'sliding' | 'french' | 'pocket' | 'bifold' | 'opening' | 'garage'
  swingDirection: 'left' | 'right'
  flipSide: boolean
}

type Window = {
  id: string
  wallId: string
  position: number
  width: number
  height: number
  sillHeight: number
  type: 'standard' | 'fixed' | 'casement' | 'sliding' | 'bay'
}

type FurnitureItem = {
  id: string
  catalogId: string
  position: Point
  rotation: number
  scale: { x: number; y: number; z: number }
  width?: number
  depth?: number
  height?: number
}

export type OpenPlanProject = {
  id: string
  name: string
  description?: string
  floors: Array<{
    id: string
    name: string
    level: number
    walls: Wall[]
    rooms: Array<{
      id: string
      name: string
      walls: string[]
      floorTexture: string
      area: number
      color?: string
    }>
    doors: Door[]
    windows: Window[]
    furniture: FurnitureItem[]
    stairs: []
    columns: []
    guides: []
    measurements: []
    annotations: []
    textAnnotations: []
    groups: []
  }>
  activeFloorId: string
  createdAt: string
  updatedAt: string
}

function uid(): string {
  return Math.random().toString(36).slice(2, 10)
}

function round(n: number) {
  return Math.round(n)
}

type Rect = {
  id: string
  name: string
  kind: string
  x: number
  y: number
  w: number
  h: number
}

function roomRect(room: Room): Rect {
  const w = room.lengthCm > 0 ? room.lengthCm : Math.max(1, room.gridW) * CM_PER_CELL
  const h = room.widthCm > 0 ? room.widthCm : Math.max(1, room.gridH) * CM_PER_CELL
  return {
    id: room.id,
    name: room.name,
    kind: room.kind,
    x: round(room.gridX * CM_PER_CELL),
    y: round(room.gridY * CM_PER_CELL),
    w: round(w),
    h: round(h),
  }
}

/** Canonical edge key so shared walls collapse to one. */
function edgeKey(a: Point, b: Point): string {
  const sameH = a.y === b.y
  const sameV = a.x === b.x
  if (sameH) {
    const y = a.y
    const x1 = Math.min(a.x, b.x)
    const x2 = Math.max(a.x, b.x)
    return `H:${y}:${x1}:${x2}`
  }
  if (sameV) {
    const x = a.x
    const y1 = Math.min(a.y, b.y)
    const y2 = Math.max(a.y, b.y)
    return `V:${x}:${y1}:${y2}`
  }
  // diagonal fallback
  const p1 = `${a.x},${a.y}`
  const p2 = `${b.x},${b.y}`
  return p1 < p2 ? `${p1}|${p2}` : `${p2}|${p1}`
}

function parseEdge(key: string): { start: Point; end: Point; axis: 'H' | 'V' | 'D' } {
  if (key.startsWith('H:')) {
    const [, y, x1, x2] = key.split(':').map(Number) as unknown as [string, number, number, number]
    return { start: { x: x1, y }, end: { x: x2, y }, axis: 'H' }
  }
  if (key.startsWith('V:')) {
    const [, x, y1, y2] = key.split(':').map(Number) as unknown as [string, number, number, number]
    return { start: { x, y: y1 }, end: { x, y: y2 }, axis: 'V' }
  }
  const [a, b] = key.split('|')
  const [ax, ay] = a.split(',').map(Number)
  const [bx, by] = b.split(',').map(Number)
  return { start: { x: ax, y: ay }, end: { x: bx, y: by }, axis: 'D' }
}

const PROP_TO_CATALOG: Record<string, string> = {
  sofa: 'sofa',
  loveseat: 'loveseat',
  armchair: 'armchair',
  table: 'coffee_table',
  coffee: 'coffee_table',
  tv: 'tv_stand',
  television: 'tv_stand',
  bed: 'bed_queen',
  desk: 'desk',
  chair: 'office_chair',
  fridge: 'fridge',
  stove: 'stove',
  sink: 'sink_b',
  toilet: 'toilet',
  bathtub: 'bathtub',
  shower: 'shower',
  wardrobe: 'wardrobe',
  bookshelf: 'bookshelf',
  plant: 'planter_box',
}

function catalogForItem(item: RoomItem): string | null {
  const key = (item.propKey || '').toLowerCase()
  if (PROP_TO_CATALOG[key]) return PROP_TO_CATALOG[key]
  const name = item.name
  if (name.includes('沙发')) return 'sofa'
  if (name.includes('茶几')) return 'coffee_table'
  if (name.includes('电视')) return 'tv_stand'
  if (name.includes('床')) return name.includes('单') ? 'bed_twin' : 'bed_queen'
  if (name.includes('洗手') || name.includes('水槽')) return 'sink_b'
  if (name.includes('马桶')) return 'toilet'
  if (name.includes('冰箱')) return 'fridge'
  if (name.includes('灶')) return 'stove'
  if (name.includes('书桌')) return 'desk'
  return null
}

function fixtureDoorType(kind: RoomFixture['kind']): Door['type'] {
  if (kind === 'sliding') return 'sliding'
  if (kind === 'french') return 'french'
  if (kind === 'entrance') return 'single'
  return 'single'
}

/**
 * Build an OpenPlan3D project from the simple home grid plan.
 * Coordinates: cm, origin top-left (north-west), +y southward.
 */
export function homeToOpenPlan(input: {
  home: Home
  rooms: Room[]
  items?: RoomItem[]
  fixtures?: RoomFixture[]
}): OpenPlanProject {
  const { home } = input
  const rooms = [...input.rooms].sort((a, b) => a.sortOrder - b.sortOrder)
  const items = input.items ?? []
  const fixtures = input.fixtures ?? []
  const wallHeight = home.heightCm > 0 ? home.heightCm : 280
  const thickness = 12

  const rects = rooms.map(roomRect)
  const edgeMeta = new Map<
    string,
    { count: number; roomIds: string[]; sides: Array<'N' | 'E' | 'S' | 'W'> }
  >()

  for (const r of rects) {
    const edges: Array<{ key: string; side: 'N' | 'E' | 'S' | 'W' }> = [
      { key: edgeKey({ x: r.x, y: r.y }, { x: r.x + r.w, y: r.y }), side: 'N' },
      { key: edgeKey({ x: r.x + r.w, y: r.y }, { x: r.x + r.w, y: r.y + r.h }), side: 'E' },
      { key: edgeKey({ x: r.x, y: r.y + r.h }, { x: r.x + r.w, y: r.y + r.h }), side: 'S' },
      { key: edgeKey({ x: r.x, y: r.y }, { x: r.x, y: r.y + r.h }), side: 'W' },
    ]
    for (const e of edges) {
      const cur = edgeMeta.get(e.key) ?? { count: 0, roomIds: [], sides: [] }
      cur.count += 1
      cur.roomIds.push(r.id)
      cur.sides.push(e.side)
      edgeMeta.set(e.key, cur)
    }
  }

  const walls: Wall[] = []
  const wallByKey = new Map<string, Wall>()
  for (const [key] of edgeMeta) {
    const { start, end } = parseEdge(key)
    const wall: Wall = {
      id: uid(),
      start,
      end,
      thickness,
      height: wallHeight,
      color: '#444444',
    }
    walls.push(wall)
    wallByKey.set(key, wall)
  }

  // Named rooms for OpenPlan (area in m²)
  const opRooms = rects.map((r) => {
    const keys = [
      edgeKey({ x: r.x, y: r.y }, { x: r.x + r.w, y: r.y }),
      edgeKey({ x: r.x + r.w, y: r.y }, { x: r.x + r.w, y: r.y + r.h }),
      edgeKey({ x: r.x, y: r.y + r.h }, { x: r.x + r.w, y: r.y + r.h }),
      edgeKey({ x: r.x, y: r.y }, { x: r.x, y: r.y + r.h }),
    ]
    return {
      id: uid(),
      name: r.name,
      walls: keys.map((k) => wallByKey.get(k)!.id),
      floorTexture: 'hardwood',
      area: Math.round(((r.w * r.h) / 10000) * 10) / 10,
      color:
        r.kind === 'kitchen'
          ? '#fef3c7'
          : r.kind === 'bathroom'
            ? '#e0f2fe'
            : r.kind.startsWith('bedroom')
              ? '#ede9fe'
              : '#ecfdf5',
    }
  })

  const doors: Door[] = []
  const windows: Window[] = []
  const rectById = new Map(rects.map((r) => [r.id, r]))

  // Fixtures → doors / windows on matching room wall
  for (const fx of fixtures) {
    const rect = rectById.get(fx.roomId)
    if (!rect) continue
    let key = ''
    let wallLen = 0
    if (fx.wall === 'N') {
      key = edgeKey({ x: rect.x, y: rect.y }, { x: rect.x + rect.w, y: rect.y })
      wallLen = rect.w
    } else if (fx.wall === 'S') {
      key = edgeKey({ x: rect.x, y: rect.y + rect.h }, { x: rect.x + rect.w, y: rect.y + rect.h })
      wallLen = rect.w
    } else if (fx.wall === 'E') {
      key = edgeKey({ x: rect.x + rect.w, y: rect.y }, { x: rect.x + rect.w, y: rect.y + rect.h })
      wallLen = rect.h
    } else {
      key = edgeKey({ x: rect.x, y: rect.y }, { x: rect.x, y: rect.y + rect.h })
      wallLen = rect.h
    }
    const wall = wallByKey.get(key)
    if (!wall || wallLen <= 0) continue
    const widthCm = Math.max(40, Math.round(fx.widthM * 100) || 90)
    const pos = Math.min(0.9, Math.max(0.1, (fx.offsetM * 100 + widthCm / 2) / wallLen))
    if (fx.kind === 'window') {
      windows.push({
        id: uid(),
        wallId: wall.id,
        position: pos,
        width: widthCm,
        height: Math.max(60, Math.round(fx.heightM * 100) || 120),
        sillHeight: Math.max(0, Math.round(fx.sillM * 100) || 90),
        type: 'standard',
      })
    } else {
      doors.push({
        id: uid(),
        wallId: wall.id,
        position: pos,
        width: widthCm,
        height: Math.max(180, Math.round(fx.heightM * 100) || 210),
        type: fixtureDoorType(fx.kind),
        swingDirection: 'left',
        flipSide: false,
      })
    }
  }

  // If no entrance fixture, put one on the longest south outer wall (else west)
  if (!fixtures.some((f) => f.kind === 'entrance')) {
    const maxY = Math.max(...rects.map((r) => r.y + r.h), 0)
    const minX = Math.min(...rects.map((r) => r.x), 0)
    let best: { wall: Wall; score: number } | null = null
    for (const [key, meta] of edgeMeta) {
      if (meta.count !== 1) continue
      const { start, end, axis } = parseEdge(key)
      const len = axis === 'H' ? Math.abs(end.x - start.x) : Math.abs(end.y - start.y)
      if (len < 80) continue
      const isSouth = axis === 'H' && start.y === maxY
      const isWest = axis === 'V' && start.x === minX
      const score = (isSouth ? 1_000_000 : 0) + (isWest ? 100_000 : 0) + len
      const wall = wallByKey.get(key)!
      if (!best || score > best.score) best = { wall, score }
    }
    if (best) {
      doors.push({
        id: uid(),
        wallId: best.wall.id,
        position: 0.45,
        width: 90,
        height: 210,
        type: 'single',
        swingDirection: 'left',
        flipSide: false,
      })
    }
  }

  // Default doors on internal walls between rooms (if no fixtures at all)
  if (fixtures.length === 0) {
    for (const [key, meta] of edgeMeta) {
      if (meta.count !== 2) continue
      const { start, end, axis } = parseEdge(key)
      const len = axis === 'H' ? Math.abs(end.x - start.x) : Math.abs(end.y - start.y)
      if (len < 100) continue
      const wall = wallByKey.get(key)!
      if (doors.some((d) => d.wallId === wall.id)) continue
      doors.push({
        id: uid(),
        wallId: wall.id,
        position: 0.5,
        width: Math.min(90, Math.round(len * 0.35)),
        height: 210,
        type: 'single',
        swingDirection: 'left',
        flipSide: false,
      })
    }
  }

  // Default windows on outer walls of living / bedroom if none recorded
  if (!fixtures.some((f) => f.kind === 'window')) {
    for (const r of rects) {
      if (!(r.kind === 'living' || r.kind.startsWith('bedroom'))) continue
      const northKey = edgeKey({ x: r.x, y: r.y }, { x: r.x + r.w, y: r.y })
      const meta = edgeMeta.get(northKey)
      if (meta?.count !== 1) continue
      const wall = wallByKey.get(northKey)!
      if (windows.some((w) => w.wallId === wall.id)) continue
      windows.push({
        id: uid(),
        wallId: wall.id,
        position: 0.5,
        width: Math.min(180, Math.round(r.w * 0.4)),
        height: 120,
        sillHeight: 90,
        type: 'standard',
      })
    }
  }

  const furniture: FurnitureItem[] = []

  function place(
    catalogId: string,
    x: number,
    y: number,
    rotation = 0,
    size?: { width?: number; depth?: number; height?: number },
  ) {
    furniture.push({
      id: uid(),
      catalogId,
      position: { x: round(x), y: round(y) },
      rotation,
      scale: { x: 1, y: 1, z: 1 },
      ...size,
    })
  }

  for (const item of items) {
    const rect = rectById.get(item.roomId)
    if (!rect) continue
    const catalogId = catalogForItem(item)
    if (!catalogId) continue
    let x: number
    let y: number
    if (item.planXM >= 0 && item.planWM > 0) {
      x = rect.x + item.planXM * 100 + (item.planWM * 100) / 2
      y = rect.y + item.planYM * 100 + (item.planDM * 100) / 2
    } else {
      // Default slots by kind inside room
      const cx = rect.x + rect.w / 2
      const cy = rect.y + rect.h / 2
      if (catalogId === 'sofa') {
        x = cx
        y = rect.y + rect.h * 0.62
      } else if (catalogId === 'coffee_table') {
        x = cx
        y = rect.y + rect.h * 0.45
      } else if (catalogId === 'tv_stand') {
        x = cx
        y = rect.y + rect.h * 0.18
      } else if (catalogId === 'sink_b' || catalogId === 'sink_k') {
        x = rect.x + rect.w * 0.7
        y = rect.y + rect.h * 0.35
      } else {
        x = cx
        y = cy
      }
    }
    place(catalogId, x, y, 0, {
      width: item.lengthCm > 0 ? item.lengthCm : undefined,
      depth: item.widthCm > 0 ? item.widthCm : undefined,
      height: item.heightCm > 0 ? item.heightCm : undefined,
    })
  }

  // Typical beds for empty bedrooms
  for (const r of rects) {
    if (!r.kind.startsWith('bedroom')) continue
    const hasBed = furniture.some(
      (f) =>
        (f.catalogId === 'bed_queen' || f.catalogId === 'bed_twin') &&
        f.position.x >= r.x &&
        f.position.x <= r.x + r.w &&
        f.position.y >= r.y &&
        f.position.y <= r.y + r.h,
    )
    if (hasBed) continue
    place(
      r.kind === 'bedroom2' ? 'bed_twin' : 'bed_queen',
      r.x + r.w * 0.55,
      r.y + r.h * 0.45,
      0,
    )
  }

  // Kitchen defaults if empty
  for (const r of rects) {
    if (r.kind !== 'kitchen') continue
    const hasKitchen = furniture.some(
      (f) =>
        (f.catalogId === 'fridge' || f.catalogId === 'stove' || f.catalogId === 'sink_k') &&
        f.position.x >= r.x &&
        f.position.x <= r.x + r.w,
    )
    if (hasKitchen) continue
    place('fridge', r.x + 50, r.y + 50, 0)
    place('stove', r.x + r.w * 0.45, r.y + 45, 0)
    place('sink_k', r.x + r.w * 0.75, r.y + 45, 0)
  }

  // Bathroom toilet if only sink listed
  for (const r of rects) {
    if (r.kind !== 'bathroom') continue
    const hasToilet = furniture.some(
      (f) =>
        f.catalogId === 'toilet' &&
        f.position.x >= r.x &&
        f.position.x <= r.x + r.w &&
        f.position.y >= r.y &&
        f.position.y <= r.y + r.h,
    )
    if (!hasToilet) place('toilet', r.x + 60, r.y + r.h * 0.65, 0)
  }

  const floorId = uid()
  const now = new Date().toISOString()
  return {
    id: uid(),
    name: home.name || '我的小屋',
    description: home.note || undefined,
    floors: [
      {
        id: floorId,
        name: '一层',
        level: 0,
        walls,
        rooms: opRooms,
        doors,
        windows,
        furniture,
        stairs: [],
        columns: [],
        guides: [],
        measurements: [],
        annotations: [],
        textAnnotations: [],
        groups: [],
      },
    ],
    activeFloorId: floorId,
    createdAt: now,
    updatedAt: now,
  }
}

export function serializeOpenPlan(project: OpenPlanProject): string {
  return JSON.stringify(project)
}
