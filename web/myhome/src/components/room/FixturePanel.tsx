import { useLiveQuery } from 'dexie-react-hooks'
import { useState, type FormEvent } from 'react'
import { Field, readForm } from '../Field'
import { db, type FixtureKind, type Room, type WallSide } from '../../db'
import {
  FIXTURE_KINDS,
  FIXTURE_LABELS,
  WALL_LABELS,
  WALL_SIDES,
  addFixture,
  defaultFixtureSize,
  deleteFixture,
  wallLengthM,
} from '../../lib/fixtures'
import { cmToMeters } from '../../lib/homeLayout'

type Props = {
  room: Room
}

export function FixturePanel({ room }: Props) {
  const fixtures =
    useLiveQuery(async () => {
      const rows = await db.roomFixtures.where('roomId').equals(room.id).toArray()
      return rows.sort((a, b) => a.updatedAt - b.updatedAt)
    }, [room.id]) ?? []

  const [editId, setEditId] = useState<string | null>(null)
  const editing = editId ? fixtures.find((f) => f.id === editId) : null

  async function create(kind: FixtureKind) {
    const id = await addFixture(room.id, { kind })
    setEditId(id)
  }

  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!editing) return
    const fd = readForm(e)
    const kind = String(fd.get('kind') ?? editing.kind) as FixtureKind
    await db.roomFixtures.update(editing.id, {
      kind,
      name: String(fd.get('name') ?? '').trim() || FIXTURE_LABELS[kind],
      wall: String(fd.get('wall') ?? editing.wall) as WallSide,
      offsetM: Number(fd.get('offsetM')) || 0,
      widthM: Number(fd.get('widthM')) || defaultFixtureSize(kind).widthM,
      heightM: Number(fd.get('heightM')) || defaultFixtureSize(kind).heightM,
      sillM: Number(fd.get('sillM')) || 0,
      note: String(fd.get('note') ?? '').trim(),
      updatedAt: Date.now(),
    })
  }

  const roomH = cmToMeters(room.heightCm) || 2.8

  return (
    <section className="section fixture-panel">
      <h2>房屋构件</h2>
      <p className="section-lead">记入户门、房门、窗等；挂在四面墙上，供平面与 3D 展示。</p>

      <div className="fixture-kind-row">
        {FIXTURE_KINDS.map((kind) => (
          <button
            key={kind}
            type="button"
            className="dsh-pill"
            onClick={() => void create(kind)}
          >
            + {FIXTURE_LABELS[kind]}
          </button>
        ))}
      </div>

      {fixtures.length === 0 ? (
        <p className="empty">此间尚未记门窗。</p>
      ) : (
        <ul className="fixture-list">
          {fixtures.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                className={editId === item.id ? 'fixture-row on' : 'fixture-row'}
                onClick={() => setEditId(editId === item.id ? null : item.id)}
              >
                <span className="fixture-row-kind">{FIXTURE_LABELS[item.kind]}</span>
                <span className="fixture-row-name">{item.name}</span>
                <span className="fixture-row-meta">
                  {WALL_LABELS[item.wall]} · {item.widthM.toFixed(2)}×{item.heightM.toFixed(2)} m
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {editing ? (
        <form className="compose cols-3" onSubmit={(e) => void save(e)} key={editing.id}>
          <Field label="名称">
            <input name="name" defaultValue={editing.name} />
          </Field>
          <Field label="类型">
            <select name="kind" defaultValue={editing.kind}>
              {FIXTURE_KINDS.map((kind) => (
                <option key={kind} value={kind}>
                  {FIXTURE_LABELS[kind]}
                </option>
              ))}
            </select>
          </Field>
          <Field label="墙面">
            <select name="wall" defaultValue={editing.wall}>
              {WALL_SIDES.map((wall) => (
                <option key={wall} value={wall}>
                  {WALL_LABELS[wall]}（约 {wallLengthM(room, wall).toFixed(2)} m）
                </option>
              ))}
            </select>
          </Field>
          <Field label="沿墙起点 m">
            <input
              name="offsetM"
              type="number"
              min="0"
              step="0.01"
              defaultValue={editing.offsetM}
            />
          </Field>
          <Field label="宽 m">
            <input
              name="widthM"
              type="number"
              min="0.1"
              step="0.01"
              defaultValue={editing.widthM}
            />
          </Field>
          <Field label="高 m">
            <input
              name="heightM"
              type="number"
              min="0.1"
              step="0.01"
              max={roomH || 4}
              defaultValue={editing.heightM}
            />
          </Field>
          <Field label="距地 m">
            <input
              name="sillM"
              type="number"
              min="0"
              step="0.01"
              defaultValue={editing.sillM}
            />
          </Field>
          <Field label="备注" className="span-2">
            <input name="note" defaultValue={editing.note} placeholder="可选" />
          </Field>
          <button className="btn" type="submit">
            存构件
          </button>
          <button
            className="btn danger"
            type="button"
            onClick={() => {
              void deleteFixture(editing.id).then(() => setEditId(null))
            }}
          >
            除去
          </button>
        </form>
      ) : null}
    </section>
  )
}
