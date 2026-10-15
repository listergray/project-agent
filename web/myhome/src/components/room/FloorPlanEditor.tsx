import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type DragEvent as ReactDragEvent,
  type PointerEvent as ReactPointerEvent,
} from 'react'
import { Link } from 'react-router-dom'
import { Field } from '../Field'
import { db, type Room, type RoomFixture, type RoomItem, type WallSide } from '../../db'
import {
  ROOM_FACINGS,
  ROOM_KIND_LABELS,
  deleteRoom,
  formatPlanDims,
  metersInputValue,
  placeRoomAt,
  readMetersAsCm,
  translateRooms,
  updateRoomGrid,
  updateRoomMeters,
  type RoomKind,
} from '../../lib/homeLayout'
import { FACING_LABELS } from '../../lib/compass'
import { FIXTURE_LABELS, fixturePlanStyle, wallLengthM } from '../../lib/fixtures'
import {
  itemOnPlan,
  placeComponentOnRoom,
  PLAN_COMPONENT_MIME,
  propPlanStyle,
  roomMeters,
} from '../../lib/planCatalog'
import { clampRoomGrid } from '../../lib/itemTree'

type Props = {
  rooms: Room[]
  fixtures?: RoomFixture[]
  planItems?: RoomItem[]
  planCols: number
  planRows: number
  itemCounts: Map<string, number>
}

type GridRect = { gridX: number; gridY: number; gridW: number; gridH: number }
type ResizeEdge = 'e' | 's' | 'se' | 'w' | 'n' | 'ne' | 'sw' | 'nw'
type PropRect = { planXM: number; planYM: number; planWM: number; planDM: number }
type FixtureRect = { wall: WallSide; offsetM: number; widthM: number }

type DragMode =
  | {
      type: 'move'
      roomIds: string[]
      originX: number
      originY: number
      starts: Record<string, GridRect>
    }
  | { type: 'resize'; roomId: string; edge: ResizeEdge; start: GridRect }
  | {
      type: 'prop-move'
      itemId: string
      roomId: string
      start: PropRect
      originClientX: number
      originClientY: number
    }
  | {
      type: 'prop-resize'
      itemId: string
      roomId: string
      edge: ResizeEdge
      start: PropRect
      originClientX: number
      originClientY: number
    }
  | {
      type: 'fixture-move'
      fixtureId: string
      roomId: string
      start: FixtureRect
      originClientX: number
      originClientY: number
    }
  | {
      type: 'fixture-resize'
      fixtureId: string
      roomId: string
      edge: 'start' | 'end'
      start: FixtureRect
      originClientX: number
      originClientY: number
    }
  | null

const HANDLES: Array<[ResizeEdge, string]> = [
  ['n', 'floor-handle n'],
  ['s', 'floor-handle s'],
  ['e', 'floor-handle e'],
  ['w', 'floor-handle w'],
  ['ne', 'floor-handle ne'],
  ['nw', 'floor-handle nw'],
  ['se', 'floor-handle se'],
  ['sw', 'floor-handle sw'],
]

const MIN_PROP_M = 0.2
const MIN_FIXTURE_M = 0.3

function liveRect(room: Room, drafts: Record<string, GridRect>): GridRect {
  return (
    drafts[room.id] ?? {
      gridX: room.gridX,
      gridY: room.gridY,
      gridW: room.gridW,
      gridH: room.gridH,
    }
  )
}

function liveProp(item: RoomItem, drafts: Record<string, PropRect>): PropRect {
  return (
    drafts[item.id] ?? {
      planXM: item.planXM,
      planYM: item.planYM,
      planWM: item.planWM,
      planDM: item.planDM,
    }
  )
}

function liveFixture(f: RoomFixture, drafts: Record<string, FixtureRect>): FixtureRect {
  return (
    drafts[f.id] ?? {
      wall: f.wall,
      offsetM: f.offsetM,
      widthM: f.widthM,
    }
  )
}

function clampGroupDelta(
  starts: GridRect[],
  dx: number,
  dy: number,
  planCols: number,
  planRows: number,
) {
  let minDx = -Infinity
  let maxDx = Infinity
  let minDy = -Infinity
  let maxDy = Infinity
  for (const s of starts) {
    minDx = Math.max(minDx, -s.gridX)
    maxDx = Math.min(maxDx, planCols - s.gridW - s.gridX)
    minDy = Math.max(minDy, -s.gridY)
    maxDy = Math.min(maxDy, planRows - s.gridH - s.gridY)
  }
  return {
    dx: Math.max(minDx, Math.min(maxDx, Math.round(dx))),
    dy: Math.max(minDy, Math.min(maxDy, Math.round(dy))),
  }
}

function clampPropRect(rect: PropRect, lengthM: number, depthM: number): PropRect {
  const planWM = Math.max(MIN_PROP_M, Math.min(lengthM, rect.planWM))
  const planDM = Math.max(MIN_PROP_M, Math.min(depthM, rect.planDM))
  return {
    planWM,
    planDM,
    planXM: Math.max(0, Math.min(lengthM - planWM, rect.planXM)),
    planYM: Math.max(0, Math.min(depthM - planDM, rect.planYM)),
  }
}

function resizePropRect(
  start: PropRect,
  edge: ResizeEdge,
  dx: number,
  dy: number,
  lengthM: number,
  depthM: number,
): PropRect {
  let { planXM, planYM, planWM, planDM } = start
  if (edge.includes('e')) planWM = start.planWM + dx
  if (edge.includes('s')) planDM = start.planDM + dy
  if (edge.includes('w')) {
    planXM = start.planXM + dx
    planWM = start.planWM - dx
  }
  if (edge.includes('n')) {
    planYM = start.planYM + dy
    planDM = start.planDM - dy
  }
  if (planWM < MIN_PROP_M) {
    if (edge.includes('w')) planXM = start.planXM + start.planWM - MIN_PROP_M
    planWM = MIN_PROP_M
  }
  if (planDM < MIN_PROP_M) {
    if (edge.includes('n')) planYM = start.planYM + start.planDM - MIN_PROP_M
    planDM = MIN_PROP_M
  }
  return clampPropRect({ planXM, planYM, planWM, planDM }, lengthM, depthM)
}

function alongWallDelta(
  wall: WallSide,
  dxM: number,
  dyM: number,
): number {
  if (wall === 'N' || wall === 'S') return dxM
  return dyM
}

export function FloorPlanEditor({
  rooms,
  fixtures = [],
  planItems = [],
  planCols,
  planRows,
  itemCounts,
}: Props) {
  const boardRef = useRef<HTMLDivElement>(null)
  const draftsRef = useRef<Record<string, GridRect>>({})
  const propDraftsRef = useRef<Record<string, PropRect>>({})
  const fixtureDraftsRef = useRef<Record<string, FixtureRect>>({})
  const dragRef = useRef<DragMode>(null)
  const selectedRef = useRef<Set<string>>(new Set())

  const [selectedIds, setSelectedIds] = useState<Set<string>>(() => new Set())
  const [selectedPropId, setSelectedPropId] = useState<string | null>(null)
  const [selectedFixtureId, setSelectedFixtureId] = useState<string | null>(null)
  const [drafts, setDrafts] = useState<Record<string, GridRect>>({})
  const [propDrafts, setPropDrafts] = useState<Record<string, PropRect>>({})
  const [fixtureDrafts, setFixtureDrafts] = useState<Record<string, FixtureRect>>({})
  const [dragging, setDragging] = useState(false)
  const [dropHint, setDropHint] = useState(false)
  const [nameDraft, setNameDraft] = useState('')
  const [kindDraft, setKindDraft] = useState<RoomKind>('custom')
  const [facingDraft, setFacingDraft] = useState('')
  const [lengthDraft, setLengthDraft] = useState('')
  const [widthDraft, setWidthDraft] = useState('')
  const [heightDraft, setHeightDraft] = useState('')
  const [propWMDraft, setPropWMDraft] = useState('')
  const [propDMDraft, setPropDMDraft] = useState('')
  const [fixOffsetDraft, setFixOffsetDraft] = useState('')
  const [fixWidthDraft, setFixWidthDraft] = useState('')

  const selectedList = rooms.filter((room) => selectedIds.has(room.id))
  const selected = selectedList.length === 1 ? selectedList[0] : null
  const selectedProp = selectedPropId
    ? (planItems.find((item) => item.id === selectedPropId) ?? null)
    : null
  const selectedFixture = selectedFixtureId
    ? (fixtures.find((f) => f.id === selectedFixtureId) ?? null)
    : null

  useEffect(() => {
    draftsRef.current = drafts
  }, [drafts])
  useEffect(() => {
    propDraftsRef.current = propDrafts
  }, [propDrafts])
  useEffect(() => {
    fixtureDraftsRef.current = fixtureDrafts
  }, [fixtureDrafts])
  useEffect(() => {
    selectedRef.current = selectedIds
  }, [selectedIds])

  useEffect(() => {
    if (!selected) return
    setNameDraft(selected.name)
    setKindDraft(selected.kind as RoomKind)
    setFacingDraft(selected.facing || '')
    setLengthDraft(metersInputValue(selected.lengthCm) || selected.gridW.toFixed(2))
    setWidthDraft(metersInputValue(selected.widthCm) || selected.gridH.toFixed(2))
    setHeightDraft(metersInputValue(selected.heightCm))
  }, [
    selected?.id,
    selected?.name,
    selected?.kind,
    selected?.facing,
    selected?.heightCm,
    selected?.lengthCm,
    selected?.widthCm,
    selected?.gridW,
    selected?.gridH,
  ])

  useEffect(() => {
    if (!selectedProp) return
    const live = liveProp(selectedProp, propDrafts)
    setPropWMDraft(live.planWM.toFixed(2))
    setPropDMDraft(live.planDM.toFixed(2))
  }, [selectedProp?.id, selectedProp?.planWM, selectedProp?.planDM, propDrafts])

  useEffect(() => {
    if (!selectedFixture) return
    const live = liveFixture(selectedFixture, fixtureDrafts)
    setFixOffsetDraft(live.offsetM.toFixed(2))
    setFixWidthDraft(live.widthM.toFixed(2))
  }, [selectedFixture?.id, selectedFixture?.offsetM, selectedFixture?.widthM, fixtureDrafts])

  const cellFromPoint = useCallback(
    (clientX: number, clientY: number) => {
      const board = boardRef.current
      if (!board) return { x: 0, y: 0 }
      const rect = board.getBoundingClientRect()
      const x = Math.floor(((clientX - rect.left) / rect.width) * planCols)
      const y = Math.floor(((clientY - rect.top) / rect.height) * planRows)
      return {
        x: Math.max(0, Math.min(planCols - 1, x)),
        y: Math.max(0, Math.min(planRows - 1, y)),
      }
    },
    [planCols, planRows],
  )

  const metersPerPixel = useCallback(
    (room: Room) => {
      const board = boardRef.current
      if (!board) return { x: 0.01, y: 0.01 }
      const rect = board.getBoundingClientRect()
      const { lengthM, widthM } = roomMeters(room)
      const r = liveRect(room, draftsRef.current)
      return {
        x: (planCols / rect.width) * (lengthM / Math.max(1, r.gridW)),
        y: (planRows / rect.height) * (widthM / Math.max(1, r.gridH)),
      }
    },
    [planCols, planRows],
  )

  const roomAtPoint = useCallback(
    (clientX: number, clientY: number) => {
      const board = boardRef.current
      if (!board) return null
      const rect = board.getBoundingClientRect()
      const fx = ((clientX - rect.left) / rect.width) * planCols
      const fy = ((clientY - rect.top) / rect.height) * planRows
      for (const room of rooms) {
        const r = liveRect(room, draftsRef.current)
        if (fx >= r.gridX && fx < r.gridX + r.gridW && fy >= r.gridY && fy < r.gridY + r.gridH) {
          const { lengthM, widthM } = roomMeters(room)
          const localXM = ((fx - r.gridX) / r.gridW) * lengthM
          const localYM = ((fy - r.gridY) / r.gridH) * widthM
          return { room, localXM, localYM, rect: r }
        }
      }
      return null
    },
    [rooms, planCols, planRows],
  )

  const patchDrafts = useCallback((next: Record<string, GridRect>) => {
    setDrafts((prev) => {
      const updated = { ...prev, ...next }
      draftsRef.current = updated
      return updated
    })
  }, [])

  const patchPropDrafts = useCallback((next: Record<string, PropRect>) => {
    setPropDrafts((prev) => {
      const updated = { ...prev, ...next }
      propDraftsRef.current = updated
      return updated
    })
  }, [])

  const patchFixtureDrafts = useCallback((next: Record<string, FixtureRect>) => {
    setFixtureDrafts((prev) => {
      const updated = { ...prev, ...next }
      fixtureDraftsRef.current = updated
      return updated
    })
  }, [])

  const clearDrafts = useCallback((roomIds: string[]) => {
    setDrafts((prev) => {
      const copy = { ...prev }
      for (const id of roomIds) delete copy[id]
      draftsRef.current = copy
      return copy
    })
  }, [])

  useEffect(() => {
    function onMove(event: PointerEvent) {
      const drag = dragRef.current
      if (!drag) return

      if (drag.type === 'prop-move' || drag.type === 'prop-resize') {
        const room = rooms.find((r) => r.id === drag.roomId)
        if (!room) return
        const { lengthM, widthM } = roomMeters(room)
        const mpp = metersPerPixel(room)
        const dx = (event.clientX - drag.originClientX) * mpp.x
        const dy = (event.clientY - drag.originClientY) * mpp.y
        if (drag.type === 'prop-move') {
          patchPropDrafts({
            [drag.itemId]: clampPropRect(
              {
                ...drag.start,
                planXM: drag.start.planXM + dx,
                planYM: drag.start.planYM + dy,
              },
              lengthM,
              widthM,
            ),
          })
        } else {
          patchPropDrafts({
            [drag.itemId]: resizePropRect(drag.start, drag.edge, dx, dy, lengthM, widthM),
          })
        }
        return
      }

      if (drag.type === 'fixture-move' || drag.type === 'fixture-resize') {
        const room = rooms.find((r) => r.id === drag.roomId)
        if (!room) return
        const mpp = metersPerPixel(room)
        const dxM = (event.clientX - drag.originClientX) * mpp.x
        const dyM = (event.clientY - drag.originClientY) * mpp.y
        const delta = alongWallDelta(drag.start.wall, dxM, dyM)
        const wallLen = wallLengthM(room, drag.start.wall)
        if (drag.type === 'fixture-move') {
          const widthM = Math.max(MIN_FIXTURE_M, drag.start.widthM)
          const offsetM = Math.max(0, Math.min(wallLen - widthM, drag.start.offsetM + delta))
          patchFixtureDrafts({
            [drag.fixtureId]: { ...drag.start, offsetM, widthM },
          })
        } else if (drag.edge === 'end') {
          const widthM = Math.max(
            MIN_FIXTURE_M,
            Math.min(wallLen - drag.start.offsetM, drag.start.widthM + delta),
          )
          patchFixtureDrafts({
            [drag.fixtureId]: { ...drag.start, widthM },
          })
        } else {
          const right = drag.start.offsetM + drag.start.widthM
          const offsetM = Math.max(0, Math.min(right - MIN_FIXTURE_M, drag.start.offsetM + delta))
          patchFixtureDrafts({
            [drag.fixtureId]: {
              ...drag.start,
              offsetM,
              widthM: right - offsetM,
            },
          })
        }
        return
      }

      const cell = cellFromPoint(event.clientX, event.clientY)

      if (drag.type === 'move') {
        const rawDx = cell.x - drag.originX
        const rawDy = cell.y - drag.originY
        const starts = drag.roomIds.map((id) => drag.starts[id]).filter(Boolean)
        const { dx, dy } = clampGroupDelta(starts, rawDx, rawDy, planCols, planRows)
        const next: Record<string, GridRect> = {}
        for (const id of drag.roomIds) {
          const start = drag.starts[id]
          if (!start) continue
          next[id] = {
            ...start,
            gridX: start.gridX + dx,
            gridY: start.gridY + dy,
          }
        }
        patchDrafts(next)
        return
      }

      const { start, edge } = drag
      let { gridX, gridY, gridW, gridH } = start
      if (edge.includes('e')) gridW = Math.max(1, cell.x - start.gridX + 1)
      if (edge.includes('s')) gridH = Math.max(1, cell.y - start.gridY + 1)
      if (edge.includes('w')) {
        const right = start.gridX + start.gridW
        gridX = Math.min(cell.x, right - 1)
        gridW = right - gridX
      }
      if (edge.includes('n')) {
        const bottom = start.gridY + start.gridH
        gridY = Math.min(cell.y, bottom - 1)
        gridH = bottom - gridY
      }
      patchDrafts({
        [drag.roomId]: clampRoomGrid(gridX, gridY, gridW, gridH, planCols, planRows),
      })
    }

    async function onUp() {
      const drag = dragRef.current
      if (!drag) return
      dragRef.current = null
      setDragging(false)

      if (drag.type === 'prop-move' || drag.type === 'prop-resize') {
        const draft = propDraftsRef.current[drag.itemId]
        if (!draft) return
        await db.roomItems.update(drag.itemId, {
          planXM: draft.planXM,
          planYM: draft.planYM,
          planWM: draft.planWM,
          planDM: draft.planDM,
          lengthCm: Math.round(draft.planWM * 100),
          widthCm: Math.round(draft.planDM * 100),
          updatedAt: Date.now(),
        })
        // 保留草稿直到 live 数据追上，避免回弹
        return
      }

      if (drag.type === 'fixture-move' || drag.type === 'fixture-resize') {
        const draft = fixtureDraftsRef.current[drag.fixtureId]
        if (!draft) return
        await db.roomFixtures.update(drag.fixtureId, {
          wall: draft.wall,
          offsetM: draft.offsetM,
          widthM: draft.widthM,
          updatedAt: Date.now(),
        })
        return
      }

      if (drag.type === 'move') {
        const moves = drag.roomIds.map((id) => {
          const next = draftsRef.current[id] ?? drag.starts[id]
          return { id, gridX: next.gridX, gridY: next.gridY }
        })
        void translateRooms(moves).then(() => clearDrafts(drag.roomIds))
        return
      }

      const next = draftsRef.current[drag.roomId] ?? drag.start
      void updateRoomGrid(drag.roomId, next.gridX, next.gridY, next.gridW, next.gridH).then(() => {
        clearDrafts([drag.roomId])
      })
    }

    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerup', onUp)
    return () => {
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerup', onUp)
    }
  }, [
    cellFromPoint,
    planCols,
    planRows,
    patchDrafts,
    patchPropDrafts,
    patchFixtureDrafts,
    clearDrafts,
    rooms,
    metersPerPixel,
  ])

  // live 数据追上后清掉草稿，避免永久覆盖
  useEffect(() => {
    setPropDrafts((prev) => {
      let changed = false
      const next = { ...prev }
      for (const [id, draft] of Object.entries(prev)) {
        const item = planItems.find((row) => row.id === id)
        if (
          item &&
          Math.abs(item.planXM - draft.planXM) < 0.001 &&
          Math.abs(item.planYM - draft.planYM) < 0.001 &&
          Math.abs(item.planWM - draft.planWM) < 0.001 &&
          Math.abs(item.planDM - draft.planDM) < 0.001
        ) {
          delete next[id]
          changed = true
        }
      }
      if (!changed) return prev
      propDraftsRef.current = next
      return next
    })
  }, [planItems])

  useEffect(() => {
    setFixtureDrafts((prev) => {
      let changed = false
      const next = { ...prev }
      for (const [id, draft] of Object.entries(prev)) {
        const row = fixtures.find((f) => f.id === id)
        if (
          row &&
          row.wall === draft.wall &&
          Math.abs(row.offsetM - draft.offsetM) < 0.001 &&
          Math.abs(row.widthM - draft.widthM) < 0.001
        ) {
          delete next[id]
          changed = true
        }
      }
      if (!changed) return prev
      fixtureDraftsRef.current = next
      return next
    })
  }, [fixtures])

  function clearComponentSelection() {
    setSelectedPropId(null)
    setSelectedFixtureId(null)
  }

  function beginMove(room: Room, event: ReactPointerEvent) {
    if ((event.target as HTMLElement).closest('.floor-prop, .floor-fixture, .floor-handle')) return
    event.preventDefault()
    event.stopPropagation()
    clearComponentSelection()
    const additive = event.shiftKey || event.metaKey || event.ctrlKey
    let ids = selectedRef.current

    if (additive) {
      const next = new Set(ids)
      if (next.has(room.id)) next.delete(room.id)
      else next.add(room.id)
      setSelectedIds(next)
      selectedRef.current = next
      ids = next
      if (!ids.has(room.id) || ids.size === 0) return
    } else if (!ids.has(room.id)) {
      ids = new Set([room.id])
      setSelectedIds(ids)
      selectedRef.current = ids
    }

    const roomIds = [...ids]
    const starts: Record<string, GridRect> = {}
    for (const id of roomIds) {
      const row = rooms.find((r) => r.id === id)
      if (!row) continue
      starts[id] = liveRect(row, draftsRef.current)
    }
    const cell = cellFromPoint(event.clientX, event.clientY)
    dragRef.current = {
      type: 'move',
      roomIds,
      originX: cell.x,
      originY: cell.y,
      starts,
    }
    setDragging(true)
    event.currentTarget.setPointerCapture?.(event.pointerId)
  }

  function beginResize(room: Room, edge: ResizeEdge, event: ReactPointerEvent) {
    event.preventDefault()
    event.stopPropagation()
    clearComponentSelection()
    setSelectedIds(new Set([room.id]))
    selectedRef.current = new Set([room.id])
    const start = liveRect(room, draftsRef.current)
    dragRef.current = { type: 'resize', roomId: room.id, edge, start }
    setDragging(true)
    ;(event.target as HTMLElement).setPointerCapture?.(event.pointerId)
  }

  function beginPropMove(item: RoomItem, event: ReactPointerEvent) {
    event.preventDefault()
    event.stopPropagation()
    setSelectedIds(new Set())
    selectedRef.current = new Set()
    setSelectedFixtureId(null)
    setSelectedPropId(item.id)
    const start = liveProp(item, propDraftsRef.current)
    dragRef.current = {
      type: 'prop-move',
      itemId: item.id,
      roomId: item.roomId,
      start,
      originClientX: event.clientX,
      originClientY: event.clientY,
    }
    setDragging(true)
    ;(event.currentTarget as HTMLElement).setPointerCapture?.(event.pointerId)
  }

  function beginPropResize(item: RoomItem, edge: ResizeEdge, event: ReactPointerEvent) {
    event.preventDefault()
    event.stopPropagation()
    setSelectedIds(new Set())
    selectedRef.current = new Set()
    setSelectedFixtureId(null)
    setSelectedPropId(item.id)
    const start = liveProp(item, propDraftsRef.current)
    dragRef.current = {
      type: 'prop-resize',
      itemId: item.id,
      roomId: item.roomId,
      edge,
      start,
      originClientX: event.clientX,
      originClientY: event.clientY,
    }
    setDragging(true)
    ;(event.target as HTMLElement).setPointerCapture?.(event.pointerId)
  }

  function beginFixtureMove(fixture: RoomFixture, event: ReactPointerEvent) {
    event.preventDefault()
    event.stopPropagation()
    setSelectedIds(new Set())
    selectedRef.current = new Set()
    setSelectedPropId(null)
    setSelectedFixtureId(fixture.id)
    const start = liveFixture(fixture, fixtureDraftsRef.current)
    dragRef.current = {
      type: 'fixture-move',
      fixtureId: fixture.id,
      roomId: fixture.roomId,
      start,
      originClientX: event.clientX,
      originClientY: event.clientY,
    }
    setDragging(true)
    ;(event.currentTarget as HTMLElement).setPointerCapture?.(event.pointerId)
  }

  function beginFixtureResize(
    fixture: RoomFixture,
    edge: 'start' | 'end',
    event: ReactPointerEvent,
  ) {
    event.preventDefault()
    event.stopPropagation()
    setSelectedIds(new Set())
    selectedRef.current = new Set()
    setSelectedPropId(null)
    setSelectedFixtureId(fixture.id)
    const start = liveFixture(fixture, fixtureDraftsRef.current)
    dragRef.current = {
      type: 'fixture-resize',
      fixtureId: fixture.id,
      roomId: fixture.roomId,
      edge,
      start,
      originClientX: event.clientX,
      originClientY: event.clientY,
    }
    setDragging(true)
    ;(event.target as HTMLElement).setPointerCapture?.(event.pointerId)
  }

  function onBoardPointerDown(event: ReactPointerEvent<HTMLDivElement>) {
    if (dragging || dragRef.current) return
    const target = event.target as HTMLElement
    const onBlank =
      target === event.currentTarget ||
      target.classList.contains('floor-grid-bg') ||
      target.classList.contains('floor-grid-cell')
    if (!onBlank) return
    setSelectedIds(new Set())
    selectedRef.current = new Set()
    clearComponentSelection()
  }

  function onDragOver(event: ReactDragEvent) {
    if (
      ![...event.dataTransfer.types].includes(PLAN_COMPONENT_MIME) &&
      ![...event.dataTransfer.types].includes('text/plain')
    ) {
      return
    }
    event.preventDefault()
    event.dataTransfer.dropEffect = 'copy'
    setDropHint(true)
  }

  function onDragLeave(event: ReactDragEvent) {
    if (event.currentTarget === event.target) setDropHint(false)
  }

  async function onDrop(event: ReactDragEvent) {
    event.preventDefault()
    setDropHint(false)
    const componentId =
      event.dataTransfer.getData(PLAN_COMPONENT_MIME) || event.dataTransfer.getData('text/plain')
    if (!componentId) return
    const component = await db.planComponents.get(componentId)
    if (!component) return
    const hit = roomAtPoint(event.clientX, event.clientY)
    if (!hit) {
      window.alert('请拖到某个房间上。')
      return
    }
    const placed = await placeComponentOnRoom(component, hit.room, hit.localXM, hit.localYM)
    setSelectedIds(new Set())
    selectedRef.current = new Set()
    if (placed.kind === 'prop') {
      setSelectedFixtureId(null)
      setSelectedPropId(placed.id)
    } else {
      setSelectedPropId(null)
      setSelectedFixtureId(placed.id)
    }
  }

  async function addRoom() {
    const id = await placeRoomAt(0, 0)
    setSelectedIds(new Set([id]))
    selectedRef.current = new Set([id])
    clearComponentSelection()
  }

  function selectAll() {
    const next = new Set(rooms.map((r) => r.id))
    setSelectedIds(next)
    selectedRef.current = next
    clearComponentSelection()
  }

  function clearSelection() {
    setSelectedIds(new Set())
    selectedRef.current = new Set()
    clearComponentSelection()
  }

  async function saveSelectedMeta() {
    if (!selected) return
    const lengthM = Number(lengthDraft) || selected.gridW
    const widthM = Number(widthDraft) || selected.gridH
    await updateRoomMeters(
      selected.id,
      lengthM,
      widthM,
      readMetersAsCm(heightDraft),
      facingDraft,
    )
    await db.rooms.update(selected.id, {
      name: nameDraft.trim() || selected.name,
      kind: kindDraft,
      updatedAt: Date.now(),
    })
    clearDrafts([selected.id])
  }

  async function saveSelectedPropSize() {
    if (!selectedProp) return
    const room = rooms.find((r) => r.id === selectedProp.roomId)
    if (!room) return
    const { lengthM, widthM } = roomMeters(room)
    const current = liveProp(selectedProp, propDraftsRef.current)
    const next = clampPropRect(
      {
        ...current,
        planWM: Number(propWMDraft) || current.planWM,
        planDM: Number(propDMDraft) || current.planDM,
      },
      lengthM,
      widthM,
    )
    patchPropDrafts({ [selectedProp.id]: next })
    await db.roomItems.update(selectedProp.id, {
      ...next,
      lengthCm: Math.round(next.planWM * 100),
      widthCm: Math.round(next.planDM * 100),
      updatedAt: Date.now(),
    })
  }

  async function saveSelectedFixtureSize() {
    if (!selectedFixture) return
    const room = rooms.find((r) => r.id === selectedFixture.roomId)
    if (!room) return
    const current = liveFixture(selectedFixture, fixtureDraftsRef.current)
    const wallLen = wallLengthM(room, current.wall)
    const widthM = Math.max(
      MIN_FIXTURE_M,
      Math.min(wallLen, Number(fixWidthDraft) || current.widthM),
    )
    const offsetM = Math.max(
      0,
      Math.min(wallLen - widthM, Number(fixOffsetDraft) || current.offsetM),
    )
    const next = { ...current, offsetM, widthM }
    patchFixtureDrafts({ [selectedFixture.id]: next })
    await db.roomFixtures.update(selectedFixture.id, {
      offsetM,
      widthM,
      updatedAt: Date.now(),
    })
  }

  async function removeSelected() {
    if (selectedList.length === 0) return
    if (selectedList.length === 1) {
      const row = selectedList[0]
      const count = itemCounts.get(row.id) ?? 0
      const msg =
        count > 0
          ? `除去「${row.name}」及其中 ${count} 件物？`
          : `除去「${row.name}」？`
      if (!window.confirm(msg)) return
      await deleteRoom(row.id)
    } else {
      const msg = `除去选中的 ${selectedList.length} 间及其物品？`
      if (!window.confirm(msg)) return
      for (const row of selectedList) await deleteRoom(row.id)
    }
    clearSelection()
  }

  async function removeSelectedProp() {
    if (!selectedProp) return
    if (!window.confirm(`从平面除去「${selectedProp.name}」？`)) return
    await db.roomItems.delete(selectedProp.id)
    setPropDrafts((prev) => {
      const copy = { ...prev }
      delete copy[selectedProp.id]
      propDraftsRef.current = copy
      return copy
    })
    setSelectedPropId(null)
  }

  async function removeSelectedFixture() {
    if (!selectedFixture) return
    if (!window.confirm(`除去「${selectedFixture.name}」？`)) return
    await db.roomFixtures.delete(selectedFixture.id)
    setFixtureDrafts((prev) => {
      const copy = { ...prev }
      delete copy[selectedFixture.id]
      fixtureDraftsRef.current = copy
      return copy
    })
    setSelectedFixtureId(null)
  }

  const selectedRect = selected ? liveRect(selected, drafts) : null
  const visibleProps = planItems.filter(itemOnPlan)

  return (
    <div className="floor-editor">
      <p className="section-lead">
        一格＝一米。组件可拖挪、拖边改大小；门窗沿墙滑动。Shift / Ctrl 多选房间。
      </p>

      <div className="floor-toolbar">
        <button type="button" className="dsh-pill on" onClick={() => void addRoom()}>
          添房间
        </button>
        <button type="button" className="dsh-pill" onClick={selectAll}>
          全选
        </button>
        <button type="button" className="dsh-pill" onClick={clearSelection}>
          清除选择
        </button>
        {selectedIds.size > 0 ? (
          <span className="floor-toolbar-meta">已选 {selectedIds.size} 间</span>
        ) : null}
      </div>

      <div
        ref={boardRef}
        className={[
          'floor-plan dsh-floor floor-board',
          dragging ? 'dragging' : '',
          dropHint ? 'drop-ready' : '',
        ]
          .filter(Boolean)
          .join(' ')}
        aria-label="可编辑房屋平面"
        style={
          {
            '--plan-cols': planCols,
            '--plan-rows': planRows,
          } as CSSProperties
        }
        onPointerDown={onBoardPointerDown}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={(e) => void onDrop(e)}
      >
        <div className="floor-grid-bg" aria-hidden>
          {Array.from({ length: planCols * planRows }, (_, i) => (
            <span key={i} className="floor-grid-cell" />
          ))}
        </div>

        {rooms.map((room) => {
          const rect = liveRect(room, drafts)
          const on = selectedIds.has(room.id)
          const count = itemCounts.get(room.id) ?? 0
          const { lengthM, widthM } = roomMeters(room)
          return (
            <div
              key={room.id}
              className={on ? 'floor-room edit on' : 'floor-room edit'}
              style={{
                left: `${(rect.gridX / planCols) * 100}%`,
                top: `${(rect.gridY / planRows) * 100}%`,
                width: `${(rect.gridW / planCols) * 100}%`,
                height: `${(rect.gridH / planRows) * 100}%`,
              }}
              onPointerDown={(event) => beginMove(room, event)}
            >
              <div className="floor-room-body">
                <span className="floor-room-name">{room.name}</span>
                <span className="floor-room-meta">
                  {formatPlanDims(
                    drafts[room.id]
                      ? {
                          lengthCm: rect.gridW * 100,
                          widthCm: rect.gridH * 100,
                          heightCm: room.heightCm,
                        }
                      : room,
                  )}
                  {room.facing && FACING_LABELS[room.facing]
                    ? ` · 朝${FACING_LABELS[room.facing]}`
                    : ''}
                  {count > 0 ? ` · ${count} 件` : ''}
                </span>
                <Link
                  to={`/home/room/${room.id}`}
                  className="floor-room-enter"
                  onPointerDown={(event) => event.stopPropagation()}
                  onClick={(event) => event.stopPropagation()}
                >
                  进入
                </Link>
              </div>
              {fixtures
                .filter((f) => f.roomId === room.id)
                .map((f) => {
                  const live = liveFixture(f, fixtureDrafts)
                  const drawn = { ...f, ...live }
                  const onFix = selectedFixtureId === f.id
                  return (
                    <button
                      key={f.id}
                      type="button"
                      className={[
                        'floor-fixture',
                        `kind-${f.kind}`,
                        `wall-${live.wall}`,
                        onFix ? 'on' : '',
                      ]
                        .filter(Boolean)
                        .join(' ')}
                      title={`${FIXTURE_LABELS[f.kind]} · ${f.name}`}
                      style={fixturePlanStyle(drawn, lengthM, widthM)}
                      onPointerDown={(event) => beginFixtureMove(f, event)}
                    >
                      {onFix ? (
                        <>
                          <span
                            className="floor-fixture-handle start"
                            onPointerDown={(event) => beginFixtureResize(f, 'start', event)}
                          />
                          <span
                            className="floor-fixture-handle end"
                            onPointerDown={(event) => beginFixtureResize(f, 'end', event)}
                          />
                        </>
                      ) : null}
                    </button>
                  )
                })}
              {visibleProps
                .filter((item) => item.roomId === room.id)
                .map((item) => {
                  const live = liveProp(item, propDrafts)
                  const onProp = selectedPropId === item.id
                  return (
                    <div
                      key={item.id}
                      role="button"
                      tabIndex={0}
                      className={onProp ? 'floor-prop on' : 'floor-prop'}
                      title={`${item.name} · 拖挪 / 选中后拖边改大小`}
                      style={propPlanStyle(live, room)}
                      onPointerDown={(event) => beginPropMove(item, event)}
                    >
                      <span>{item.name}</span>
                      {onProp
                        ? HANDLES.map(([edge, className]) => (
                            <span
                              key={edge}
                              className={`${className} prop-handle`}
                              onPointerDown={(event) => beginPropResize(item, edge, event)}
                            />
                          ))
                        : null}
                    </div>
                  )
                })}
              {on && selectedIds.size === 1
                ? HANDLES.map(([edge, className]) => (
                    <span
                      key={edge}
                      className={className}
                      onPointerDown={(event) => beginResize(room, edge, event)}
                    />
                  ))
                : null}
            </div>
          )
        })}
      </div>

      {selectedProp ? (
        <div className="floor-inspector">
          <p className="dsh-kicker">平面物件</p>
          <p className="section-lead">{selectedProp.name} · 拖本体移动，拖角/边改大小</p>
          <div className="compose cols-3">
            <Field label="宽 m（东西）">
              <input
                type="number"
                min="0.2"
                step="0.01"
                value={propWMDraft}
                onChange={(e) => setPropWMDraft(e.target.value)}
              />
            </Field>
            <Field label="深 m（南北）">
              <input
                type="number"
                min="0.2"
                step="0.01"
                value={propDMDraft}
                onChange={(e) => setPropDMDraft(e.target.value)}
              />
            </Field>
            <button className="btn" type="button" onClick={() => void saveSelectedPropSize()}>
              存尺寸
            </button>
            <Link className="btn" to={`/home/room/${selectedProp.roomId}`}>
              进入房间
            </Link>
            <button className="btn danger" type="button" onClick={() => void removeSelectedProp()}>
              从平面除去
            </button>
          </div>
        </div>
      ) : selectedFixture ? (
        <div className="floor-inspector">
          <p className="dsh-kicker">门窗构件</p>
          <p className="section-lead">
            {selectedFixture.name} · 沿墙拖动；两端手柄改宽度
          </p>
          <div className="compose cols-3">
            <Field label="沿墙偏移 m">
              <input
                type="number"
                min="0"
                step="0.01"
                value={fixOffsetDraft}
                onChange={(e) => setFixOffsetDraft(e.target.value)}
              />
            </Field>
            <Field label="宽度 m">
              <input
                type="number"
                min="0.3"
                step="0.01"
                value={fixWidthDraft}
                onChange={(e) => setFixWidthDraft(e.target.value)}
              />
            </Field>
            <button className="btn" type="button" onClick={() => void saveSelectedFixtureSize()}>
              存尺寸
            </button>
            <button
              className="btn danger"
              type="button"
              onClick={() => void removeSelectedFixture()}
            >
              除去
            </button>
          </div>
        </div>
      ) : selected && selectedRect ? (
        <div className="floor-inspector">
          <p className="dsh-kicker">SELECTED</p>
          <div className="compose cols-3">
            <Field label="名称">
              <input value={nameDraft} onChange={(e) => setNameDraft(e.target.value)} />
            </Field>
            <Field label="类型">
              <select
                value={kindDraft}
                onChange={(e) => setKindDraft(e.target.value as RoomKind)}
              >
                {(Object.keys(ROOM_KIND_LABELS) as RoomKind[]).map((key) => (
                  <option key={key} value={key}>
                    {ROOM_KIND_LABELS[key]}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="朝向">
              <select value={facingDraft} onChange={(e) => setFacingDraft(e.target.value)}>
                {ROOM_FACINGS.map((opt) => (
                  <option key={opt.id || 'none'} value={opt.id}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="长 m">
              <input
                type="number"
                min="0.01"
                max={planCols}
                step="0.01"
                inputMode="decimal"
                value={lengthDraft}
                onChange={(e) => setLengthDraft(e.target.value)}
              />
            </Field>
            <Field label="宽 m">
              <input
                type="number"
                min="0.01"
                max={planRows}
                step="0.01"
                inputMode="decimal"
                value={widthDraft}
                onChange={(e) => setWidthDraft(e.target.value)}
              />
            </Field>
            <Field label="高 m">
              <input
                type="number"
                min="0"
                step="0.01"
                inputMode="decimal"
                placeholder="层高"
                value={heightDraft}
                onChange={(e) => setHeightDraft(e.target.value)}
              />
            </Field>
            <button className="btn" type="button" onClick={() => void saveSelectedMeta()}>
              存属性
            </button>
            <Link className="btn" to={`/home/room/${selected.id}`}>
              进入此间
            </Link>
            <button className="btn danger" type="button" onClick={() => void removeSelected()}>
              除去
            </button>
          </div>
        </div>
      ) : selectedIds.size > 1 ? (
        <div className="floor-inspector">
          <p className="dsh-kicker">MULTI</p>
          <p className="section-lead">已选 {selectedIds.size} 间，拖其中任意一间可整体平移。</p>
          <div className="compose cols-3">
            <button className="btn danger" type="button" onClick={() => void removeSelected()}>
              除去所选
            </button>
          </div>
        </div>
      ) : (
        <p className="section-lead">点「添房间」新增；从组件库拖到房间后，可再拖动与改大小。</p>
      )}
    </div>
  )
}
