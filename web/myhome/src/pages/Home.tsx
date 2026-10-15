import { useLiveQuery } from 'dexie-react-hooks'
import { motion, useReducedMotion } from 'motion/react'
import { lazy, Suspense, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Chapter } from '../components/Chapter'
import { DateSelect } from '../components/DateSelect'
import { Field, readForm } from '../components/Field'
import { FloorPlanEditor } from '../components/room/FloorPlanEditor'
import { PlanLibrary } from '../components/room/PlanLibrary'
import { Compass } from '../components/room/Compass'
import { RoomMark } from '../components/room/DshMarks'
import { db } from '../db'
import {
  LAYOUT_LABELS,
  ROOM_KIND_LABELS,
  addCustomRoom,
  applyLayoutPreset,
  cmToMeters,
  formatPlanDims,
  readMetersAsCm,
  syncHomeToOpenPlan,
  updateHomePlanSize,
  type LayoutPresetId,
  type RoomKind,
} from '../lib/homeLayout'
import { DEFAULT_PLAN_COLS, DEFAULT_PLAN_ROWS, MAX_PLAN, MIN_PLAN } from '../lib/itemTree'

const House3D = lazy(() =>
  import('../components/room/House3D').then((mod) => ({ default: mod.House3D })),
)

const presets = Object.keys(LAYOUT_LABELS) as LayoutPresetId[]

const KIND_TONE: Partial<Record<RoomKind, string>> = {
  living: 'blue',
  bedroom: 'violet',
  bedroom2: 'violet',
  kitchen: 'amber',
  bathroom: 'teal',
  study: 'blue',
  balcony: 'teal',
  hall: 'slate',
  closet: 'slate',
  custom: 'slate',
}

export function Home() {
  const reduce = useReducedMotion()
  const [show3d, setShow3d] = useState(false)
  const [syncingPlan, setSyncingPlan] = useState(false)
  const home = useLiveQuery(() => db.homes.get('main'))
  const rooms =
    useLiveQuery(async () => {
      const rows = await db.rooms.where('homeId').equals('main').toArray()
      return rows.sort((a, b) => a.sortOrder - b.sortOrder)
    }) ?? []
  const fixtures = useLiveQuery(() => db.roomFixtures.toArray()) ?? []
  const planItems = useLiveQuery(() => db.roomItems.toArray()) ?? []
  const itemCounts =
    useLiveQuery(async () => {
      const items = await db.roomItems.toArray()
      const map = new Map<string, number>()
      for (const item of items) {
        map.set(item.roomId, (map.get(item.roomId) ?? 0) + 1)
      }
      return map
    }) ?? new Map<string, number>()

  if (!home) {
    return (
      <Chapter title="小屋" hint="正在翻开。">
        <p className="empty">读取中。</p>
      </Chapter>
    )
  }

  const row = home

  async function saveHome(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    await db.homes.update('main', {
      name: String(fd.get('name') ?? '').trim() || row.name,
      address: String(fd.get('address') ?? '').trim(),
      heightCm: readMetersAsCm(fd.get('heightM')),
      rentStartedAt: String(fd.get('rentStartedAt') ?? ''),
      note: String(fd.get('note') ?? '').trim(),
      updatedAt: Date.now(),
    })
  }

  async function saveBoardSize(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    await updateHomePlanSize(Number(fd.get('planCols')), Number(fd.get('planRows')))
  }

  async function switchLayout(preset: LayoutPresetId) {
    if (preset === row.layoutPreset) return
    const hasItems = (await db.roomItems.count()) > 0
    const msg = hasItems
      ? '换户型会清空各房间物品。确定？'
      : '按新户型重排房间。确定？'
    if (!window.confirm(msg)) return
    await applyLayoutPreset(preset, true)
  }

  async function addRoom(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    const name = String(fd.get('name') ?? '').trim()
    if (!name) return
    await addCustomRoom(name, String(fd.get('kind') ?? 'custom') as RoomKind)
    e.currentTarget.reset()
  }

  const planCols = row.planCols ?? DEFAULT_PLAN_COLS
  const planRows = row.planRows ?? DEFAULT_PLAN_ROWS
  const totalItems = [...itemCounts.values()].reduce((a, b) => a + b, 0)
  const homeDims = formatPlanDims(row)

  return (
    <Chapter
      index="柒"
      title={row.name || '我的小屋'}
      hint="选一间进去。物件可无限往下叠放，也能全部平铺展开。"
    >
      <section className="dsh-hero">
        <div className="dsh-hero-card accent">
          <p className="dsh-kicker">HOME</p>
          <h2 className="dsh-hero-title">点一间。走进去。</h2>
          <p className="dsh-hero-copy">
            {rooms.length} 间 · {totalItems} 件物 · {homeDims || `${planCols}×${planRows} m`}
          </p>
          <RoomMark kind="living" accent />
        </div>
        <div className="dsh-hero-card">
          <p className="dsh-kicker">LAYOUT</p>
          <p className="dsh-hero-copy strong">
            当前 {LAYOUT_LABELS[row.layoutPreset as LayoutPresetId] ?? '自定义'}
          </p>
          <p className="dsh-hero-copy">
            {row.address || '地址未记'}
            {row.note ? ` · ${row.note}` : ''}
          </p>
          <div className="dsh-pills">
            {presets.map((preset) => (
              <button
                key={preset}
                type="button"
                className={row.layoutPreset === preset ? 'dsh-pill on' : 'dsh-pill'}
                onClick={() => void switchLayout(preset)}
              >
                {LAYOUT_LABELS[preset]}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="section dsh-section">
        <div className="dsh-section-head">
          <div>
            <h2>房间</h2>
            <p className="section-lead">按房间浏览，点进配置物品。</p>
          </div>
        </div>
        <div className="dsh-grid">
          {rooms.map((room, i) => {
            const count = itemCounts.get(room.id) ?? 0
            const kind = room.kind as RoomKind
            const roomDims = formatPlanDims(room)
            const face = room.facing
              ? { N: '北', NE: '东北', E: '东', SE: '东南', S: '南', SW: '西南', W: '西', NW: '西北' }[
                  room.facing
                ]
              : ''
            return (
              <motion.div
                key={room.id}
                initial={reduce ? false : { opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04, duration: 0.35 }}
              >
                <Link
                  to={`/home/room/${room.id}`}
                  className={`dsh-card tone-${KIND_TONE[kind] ?? 'slate'}`}
                >
                  <div className="dsh-card-top">
                    <span className="dsh-kicker">{ROOM_KIND_LABELS[kind] ?? room.kind}</span>
                    <RoomMark kind={room.kind} />
                  </div>
                  <p className="dsh-meta">
                    {count > 0 ? `${count} 件物` : '空着'}
                    {face ? ` · 朝${face}` : ''}
                    {roomDims ? ` · ${roomDims}` : ''}
                  </p>
                  <h3 className="dsh-card-title">{room.name}</h3>
                  <p className="dsh-card-desc">
                    {room.note || `${room.gridW}×${room.gridH} 格 · 点进查看`}
                  </p>
                  <span className="dsh-card-link">进入此间 →</span>
                </Link>
              </motion.div>
            )
          })}
        </div>
      </section>

      <section className="section dsh-section">
        <div className="dsh-section-head">
          <div>
            <h2>OpenPlan 户型</h2>
            <p className="section-lead">
              接入 OpenPlan3D：画墙、门窗、楼梯与家具，2D/3D 切换；工程写入本机账本。
            </p>
          </div>
          <div className="dsh-pills">
            <button
              type="button"
              className="dsh-pill"
              disabled={syncingPlan || !rooms?.length}
              onClick={() => {
                setSyncingPlan(true)
                void syncHomeToOpenPlan()
                  .then(() => {
                    window.location.assign('/home/design')
                  })
                  .finally(() => setSyncingPlan(false))
              }}
            >
              {syncingPlan ? '生成中…' : '按平面生成专业户型'}
            </button>
            <Link to="/home/design" className="dsh-pill on">
              打开专业编辑器
            </Link>
          </div>
        </div>
      </section>

      <section className="section dsh-section">
        <h2>平面图</h2>
        <p className="section-lead">
          一格＝一米（正方格）。上北下南。可改背板长宽；房间尺寸可精确到 0.01 米。
        </p>
        <Compass />
        <form
          className="compose cols-3 plan-size-bar"
          onSubmit={(e) => void saveBoardSize(e)}
          key={`board|${planCols}|${planRows}`}
        >
          <Field label="背板宽 m（东西）">
            <input
              name="planCols"
              type="number"
              min={MIN_PLAN}
              max={MAX_PLAN}
              step="1"
              required
              defaultValue={planCols}
            />
          </Field>
          <Field label="背板深 m（南北）">
            <input
              name="planRows"
              type="number"
              min={MIN_PLAN}
              max={MAX_PLAN}
              step="1"
              required
              defaultValue={planRows}
            />
          </Field>
          <button className="btn" type="submit">
            改背板
          </button>
        </form>
        <div className="floor-workspace">
          <FloorPlanEditor
            rooms={rooms}
            fixtures={fixtures}
            planItems={planItems}
            planCols={planCols}
            planRows={planRows}
            itemCounts={itemCounts}
          />
          <PlanLibrary />
        </div>
      </section>

      <section className="section dsh-section">
        <div className="dsh-section-head">
          <div>
            <h2>3D 看屋</h2>
            <p className="section-lead">根据平面与门窗构件生成简易立体模型。</p>
          </div>
          <button
            type="button"
            className={show3d ? 'dsh-pill on' : 'dsh-pill'}
            onClick={() => setShow3d((v) => !v)}
          >
            {show3d ? '收起' : '展开'}
          </button>
        </div>
        {show3d ? (
          <Suspense fallback={<p className="empty">载入 3D…</p>}>
            <House3D rooms={rooms} fixtures={fixtures} planCols={planCols} planRows={planRows} />
          </Suspense>
        ) : null}
      </section>

      <details className="dsh-settings">
        <summary>租房信息 · 加房间</summary>
        <form
          className="compose cols-3"
          onSubmit={(e) => void saveHome(e)}
          key={`${row.name}|${row.address}|${row.rentStartedAt}|${row.heightCm}`}
        >
          <Field label="称呼" className="span-2">
            <input name="name" defaultValue={row.name} placeholder="我的小屋" />
          </Field>
          <Field label="起租">
            <DateSelect name="rentStartedAt" defaultValue={row.rentStartedAt} />
          </Field>
          <Field label="地址" className="span-3">
            <input name="address" defaultValue={row.address} placeholder="租住在哪" />
          </Field>
          <Field label="层高 m">
            <input
              name="heightM"
              type="number"
              min="0"
              step="0.01"
              inputMode="decimal"
              placeholder="可选"
              defaultValue={cmToMeters(row.heightCm) || ''}
            />
          </Field>
          <Field label="备注" className="span-2">
            <input name="note" defaultValue={row.note} placeholder="可选" />
          </Field>
          <button className="btn span-3" type="submit">
            存档
          </button>
        </form>

        <form className="compose cols-2" onSubmit={(e) => void addRoom(e)}>
          <Field label="加一间">
            <input name="name" required placeholder="如：储物间" />
          </Field>
          <Field label="类型">
            <select name="kind" defaultValue="custom">
              {(Object.keys(ROOM_KIND_LABELS) as RoomKind[]).map((key) => (
                <option key={key} value={key}>
                  {ROOM_KIND_LABELS[key]}
                </option>
              ))}
            </select>
          </Field>
          <button className="btn span-2" type="submit">
            添一间
          </button>
        </form>
      </details>
    </Chapter>
  )
}
