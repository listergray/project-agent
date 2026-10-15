import { useLiveQuery } from 'dexie-react-hooks'
import { type FormEvent } from 'react'
import { Chapter } from '../components/Chapter'
import { DateSelect } from '../components/DateSelect'
import { Field, readForm } from '../components/Field'
import { db, HORIZON_LABELS, type Goal, type GoalHorizon, type GoalStatus } from '../db'
import { nid } from '../lib/dates'
import { ROUTE_A } from '../lib/route'
import { LIFE_SQUARES, type LifeSquareId } from '../lib/squares'

const horizons = Object.keys(HORIZON_LABELS) as GoalHorizon[]

export function Goals() {
  const settings = useLiveQuery(() => db.settings.get('main'))
  const goals =
    useLiveQuery(async () => {
      const rows = await db.goals.toArray()
      return rows.sort((a, b) => b.createdAt - a.createdAt)
    }) ?? []

  async function addGoal(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    const title = String(fd.get('title') ?? '').trim()
    if (!title) return
    await db.goals.add({
      id: nid(),
      title,
      horizon: String(fd.get('horizon') ?? 'year') as GoalHorizon,
      status: 'active',
      square: String(fd.get('square') ?? '') as LifeSquareId | '',
      note: String(fd.get('note') ?? '').trim(),
      targetDate: String(fd.get('targetDate') ?? ''),
      createdAt: Date.now(),
    })
    e.currentTarget.reset()
  }

  return (
    <Chapter index="叁" title="目标" hint="和今日的琐事分开。写下此后要去的方向。">
      <section className="path-now">
        <p className="muted">当前路线</p>
        <h2>{settings?.pathTitle || ROUTE_A.title}</h2>
        <p className="section-lead">{settings?.pathLine || ROUTE_A.line}</p>
        <ul className="path-why">
          {ROUTE_A.why.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      </section>

      <form className="compose cols-3" onSubmit={(e) => void addGoal(e)}>
        <Field label="志向" className="span-2">
          <input name="title" required placeholder="如：把一套房子住成家" />
        </Field>
        <Field label="远近">
          <select name="horizon" defaultValue="year">
            {horizons.map((key) => (
              <option key={key} value={key}>
                {HORIZON_LABELS[key]}
              </option>
            ))}
          </select>
        </Field>
        <Field label="希望抵达">
          <DateSelect name="targetDate" />
        </Field>
        <Field label="落在哪一格">
          <select name="square" defaultValue="">
            <option value="">不归格</option>
            {LIFE_SQUARES.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="说明" className="span-2">
          <input name="note" placeholder="可选" />
        </Field>
        <button className="btn span-3" type="submit">
          立下
        </button>
      </form>

      {horizons.map((horizon) => {
        const rows = goals.filter((g) => g.horizon === horizon)
        return (
          <section className="section" key={horizon}>
            <h2>{HORIZON_LABELS[horizon]}</h2>
            {rows.length === 0 ? (
              <p className="empty">此处还空着。</p>
            ) : (
              <ul className="ledger">
                {rows.map((goal) => (
                  <GoalRow key={goal.id} goal={goal} />
                ))}
              </ul>
            )}
          </section>
        )
      })}
    </Chapter>
  )
}

function GoalRow({ goal }: { goal: Goal }) {
  const statuses: { id: GoalStatus; label: string }[] = [
    { id: 'active', label: '进行' },
    { id: 'paused', label: '搁置' },
    { id: 'done', label: '已达' },
  ]

  return (
    <li>
      <div className="ledger-row">
        <div>
          <div className="ledger-name">{goal.title}</div>
          <div className="ledger-meta">
            {goal.square ? `${LIFE_SQUARES.find((s) => s.id === goal.square)?.name ?? ''} · ` : ''}
            {goal.targetDate ? `${goal.targetDate} · ` : ''}
            {goal.note || '无说明'}
          </div>
          <div className="status-row">
            {statuses.map((s) => (
              <button
                key={s.id}
                type="button"
                aria-pressed={goal.status === s.id}
                onClick={() => void db.goals.update(goal.id, { status: s.id })}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>
        <div className="ledger-meta">{goal.status === 'done' ? '已达' : goal.status === 'paused' ? '搁置' : ''}</div>
        <div className="ledger-actions">
          <button type="button" onClick={() => void db.goals.delete(goal.id)}>
            除去
          </button>
        </div>
      </div>
    </li>
  )
}
