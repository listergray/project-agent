import { useLiveQuery } from 'dexie-react-hooks'
import { type FormEvent, useEffect } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Chapter } from '../components/Chapter'
import { Field, readForm } from '../components/Field'
import { Compass } from '../components/room/Compass'
import { FixturePanel } from '../components/room/FixturePanel'
import { RoomScene } from '../components/room/RoomScene'
import { db } from '../db'
import { FACING_LABELS } from '../lib/compass'
import {
  ROOM_FACINGS,
  ROOM_KIND_LABELS,
  cmToMeters,
  deleteRoom,
  formatPlanDims,
  metersInputValue,
  metersNumberToCm,
  metersToCells,
  readMetersAsCm,
  type RoomKind,
} from '../lib/homeLayout'
import { clampRoomGrid, DEFAULT_PLAN_COLS, DEFAULT_PLAN_ROWS } from '../lib/itemTree'
import { ensureRoomScene } from '../lib/roomScene'

export function RoomDetail() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const home = useLiveQuery(() => db.homes.get('main'))
  const room = useLiveQuery(() => (id ? db.rooms.get(id) : undefined), [id])
  const items =
    useLiveQuery(async () => {
      if (!id) return []
      const rows = await db.roomItems.where('roomId').equals(id).toArray()
      return rows.sort((a, b) => b.updatedAt - a.updatedAt)
    }, [id]) ?? []

  useEffect(() => {
    if (!room) return
    void ensureRoomScene(room.id, room.kind as RoomKind)
  }, [room?.id, room?.kind])

  if (room === undefined || home === undefined) {
    return (
      <Chapter title="房间" hint="正在翻开。">
        <p className="empty">读取中。</p>
      </Chapter>
    )
  }

  if (!room) {
    return (
      <Chapter title="房间" hint="此间未在册上。">
        <Link className="back" to="/home">
          返回小屋
        </Link>
      </Chapter>
    )
  }

  const row = room
  const planCols = home?.planCols ?? DEFAULT_PLAN_COLS
  const planRows = home?.planRows ?? DEFAULT_PLAN_ROWS
  const maxX = Math.max(0, planCols - 1)
  const maxY = Math.max(0, planRows - 1)
  const roomDims = formatPlanDims(row)
  const faceLabel = row.facing ? FACING_LABELS[row.facing] : ''

  async function saveRoom(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    const lengthRaw = String(fd.get('lengthM') ?? '').trim()
    const widthRaw = String(fd.get('widthM') ?? '').trim()
    const lengthCm = lengthRaw ? readMetersAsCm(lengthRaw) : metersNumberToCm(row.lengthCm || row.gridW)
    const widthCm = widthRaw ? readMetersAsCm(widthRaw) : metersNumberToCm(row.widthCm || row.gridH)
    const heightCm = readMetersAsCm(fd.get('heightM'))
    const lengthCells = metersToCells(
      lengthRaw || String(cmToMeters(lengthCm)),
      row.gridW,
      planCols,
    )
    const widthCells = metersToCells(
      widthRaw || String(cmToMeters(widthCm)),
      row.gridH,
      planRows,
    )
    const grid = clampRoomGrid(
      Number(fd.get('gridX') ?? row.gridX),
      Number(fd.get('gridY') ?? row.gridY),
      lengthCells,
      widthCells,
      planCols,
      planRows,
    )
    await db.rooms.update(row.id, {
      name: String(fd.get('name') ?? '').trim() || row.name,
      kind: String(fd.get('kind') ?? row.kind),
      facing: String(fd.get('facing') ?? ''),
      ...grid,
      lengthCm,
      widthCm,
      heightCm,
      note: String(fd.get('note') ?? '').trim(),
      updatedAt: Date.now(),
    })
  }

  async function removeRoom() {
    if (!window.confirm(`除去「${row.name}」及其中全部物品与构件？`)) return
    await deleteRoom(row.id)
    navigate('/home')
  }

  return (
    <Chapter
      title={row.name}
      hint={`${ROOM_KIND_LABELS[row.kind as RoomKind] ?? row.kind}${faceLabel ? ` · 朝${faceLabel}` : ''}${roomDims ? ` · ${roomDims}` : ''}。物件可无限嵌套。`}
      className="chapter-studio"
    >
      <Link className="back" to="/home">
        返回平面
      </Link>

      <Compass facing={row.facing} />

      <section className="section studio-section">
        <h2>场景</h2>
        <RoomScene roomId={row.id} roomKind={row.kind} items={items} />
      </section>

      <FixturePanel room={row} />

      <section className="section">
        <h2>此间</h2>
        <p className="section-lead">
          长宽高精确到 0.01 米；占格按米向上取整近似（一格≈一米）。
        </p>
        <form
          className="compose cols-3"
          onSubmit={(e) => void saveRoom(e)}
          key={`${row.id}|${row.lengthCm}|${row.widthCm}|${row.heightCm}|${row.facing}|${row.gridX}|${row.gridY}`}
        >
          <Field label="名称">
            <input name="name" defaultValue={row.name} />
          </Field>
          <Field label="类型">
            <select name="kind" defaultValue={row.kind}>
              {(Object.keys(ROOM_KIND_LABELS) as RoomKind[]).map((key) => (
                <option key={key} value={key}>
                  {ROOM_KIND_LABELS[key]}
                </option>
              ))}
            </select>
          </Field>
          <Field label="朝向">
            <select name="facing" defaultValue={row.facing || ''}>
              {ROOM_FACINGS.map((opt) => (
                <option key={opt.id || 'none'} value={opt.id}>
                  {opt.label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="长 m">
            <input
              name="lengthM"
              type="number"
              min="0.01"
              max={planCols}
              step="0.01"
              inputMode="decimal"
              required
              defaultValue={metersInputValue(row.lengthCm) || row.gridW.toFixed(2)}
            />
          </Field>
          <Field label="宽 m">
            <input
              name="widthM"
              type="number"
              min="0.01"
              max={planRows}
              step="0.01"
              inputMode="decimal"
              required
              defaultValue={metersInputValue(row.widthCm) || row.gridH.toFixed(2)}
            />
          </Field>
          <Field label="高 m">
            <input
              name="heightM"
              type="number"
              min="0"
              step="0.01"
              inputMode="decimal"
              placeholder="层高"
              defaultValue={metersInputValue(row.heightCm)}
            />
          </Field>
          <Field label="平面 X">
            <input name="gridX" type="number" min="0" max={maxX} defaultValue={row.gridX} />
          </Field>
          <Field label="平面 Y">
            <input name="gridY" type="number" min="0" max={maxY} defaultValue={row.gridY} />
          </Field>
          <Field label="备注">
            <input name="note" defaultValue={row.note} placeholder="可选" />
          </Field>
          <button className="btn span-3" type="submit">
            存
          </button>
        </form>
      </section>

      <section className="section">
        <button className="btn danger" type="button" onClick={() => void removeRoom()}>
          除去此间
        </button>
      </section>
    </Chapter>
  )
}
