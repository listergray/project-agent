import { useLiveQuery } from 'dexie-react-hooks'
import { type FormEvent, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Chapter } from '../components/Chapter'
import { DateSelect } from '../components/DateSelect'
import { Field, readForm } from '../components/Field'
import { db } from '../db'
import { formatShortDate, nid, todayKey } from '../lib/dates'
import {
  isMaintainDue,
  maintainDueDate,
  markMaintainDone,
  syncMaintainTasks,
} from '../lib/maintain'

export function Todos() {
  const today = todayKey()
  const plans = useLiveQuery(async () => {
    const rows = await db.maintains.toArray()
    return rows.sort((a, b) => b.updatedAt - a.updatedAt)
  }) ?? []
  const rooms = useLiveQuery(() => db.rooms.toArray()) ?? []
  const items = useLiveQuery(() => db.roomItems.toArray()) ?? []

  useEffect(() => {
    void syncMaintainTasks(today)
  }, [today])

  const roomMap = new Map(rooms.map((room) => [room.id, room.name]))
  const itemMap = new Map(items.map((item) => [item.id, item.name]))
  const due = plans.filter((plan) => plan.enabled && isMaintainDue(plan, today))
  const upcoming = plans.filter((plan) => plan.enabled && !isMaintainDue(plan, today))

  async function addPlan(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    const title = String(fd.get('title') ?? '').trim()
    if (!title) return
    const everyDays = Math.max(1, Number(fd.get('everyDays') ?? 7))
    const now = Date.now()
    await db.maintains.add({
      id: nid(),
      title,
      everyDays,
      lastDoneAt: String(fd.get('lastDoneAt') ?? '').trim() || today,
      roomItemId: '',
      roomId: '',
      note: String(fd.get('note') ?? '').trim(),
      enabled: true,
      updatedAt: now,
    })
    await syncMaintainTasks()
    e.currentTarget.reset()
  }

  async function savePlan(planId: string, e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    await db.maintains.update(planId, {
      title: String(fd.get('title') ?? '').trim(),
      everyDays: Math.max(1, Number(fd.get('everyDays') ?? 7)),
      lastDoneAt: String(fd.get('lastDoneAt') ?? '').trim(),
      note: String(fd.get('note') ?? '').trim(),
      enabled: fd.get('enabled') === 'on',
      updatedAt: Date.now(),
    })
    await syncMaintainTasks()
  }

  return (
    <Chapter index="待" title="待办" hint="定期要做的事，单独记在这里；到期后自动列入今日。">
      <p className="section-lead">
        与「今日」分开：此处管周期与计划，今日只管当天执行。
        <Link to="/today"> 去今日 </Link>
      </p>

      <form className="compose cols-3" onSubmit={(e) => void addPlan(e)}>
        <Field label="事项" className="span-2">
          <input name="title" required placeholder="如：清理洗手台、换滤芯" />
        </Field>
        <Field label="每隔（天）">
          <input name="everyDays" type="number" min="1" defaultValue={7} />
        </Field>
        <Field label="上次完成">
          <DateSelect name="lastDoneAt" defaultValue={today} allowEmpty={false} />
        </Field>
        <Field label="备注" className="span-2">
          <input name="note" placeholder="可选" />
        </Field>
        <button className="btn span-3" type="submit">
          立一项
        </button>
      </form>

      {due.length > 0 ? (
        <section className="section">
          <h2>到期</h2>
          <p className="section-lead">已写入今日待办，做完后在此或今日划掉。</p>
          <PlanList
            plans={due}
            today={today}
            roomMap={roomMap}
            itemMap={itemMap}
            onSave={savePlan}
            dueTone
          />
        </section>
      ) : null}

      <section className="section">
        <h2>周期中</h2>
        {upcoming.length === 0 && due.length === 0 ? (
          <p className="empty">尚未立下定期待办。</p>
        ) : upcoming.length === 0 ? (
          <p className="empty">其余项尚未到期。</p>
        ) : (
          <PlanList plans={upcoming} today={today} roomMap={roomMap} itemMap={itemMap} onSave={savePlan} />
        )}
      </section>
    </Chapter>
  )
}

type PlanListProps = {
  plans: Array<{
    id: string
    title: string
    everyDays: number
    lastDoneAt: string
    roomItemId: string
    roomId: string
    note: string
    enabled: boolean
  }>
  today: string
  roomMap: Map<string, string>
  itemMap: Map<string, string>
  onSave: (id: string, e: FormEvent<HTMLFormElement>) => void
  dueTone?: boolean
}

function PlanList({ plans, today, roomMap, itemMap, onSave, dueTone }: PlanListProps) {
  return (
    <ul className="ledger todo-plans">
      {plans.map((plan) => {
        const next = maintainDueDate(plan, today)
        const meta = [
          `每 ${plan.everyDays} 天`,
          plan.lastDoneAt ? `上次 ${formatShortDate(plan.lastDoneAt)}` : '未记上次',
          next ? `下次 ${formatShortDate(next)}` : '',
          plan.roomId && roomMap.get(plan.roomId) ? roomMap.get(plan.roomId) : '',
          plan.roomItemId && itemMap.get(plan.roomItemId) ? itemMap.get(plan.roomItemId) : '',
          plan.note,
        ]
          .filter(Boolean)
          .join(' · ')

        return (
          <li key={plan.id} className={dueTone ? 'todo-due' : undefined}>
            <details className="todo-plan">
              <summary>
                <span className="ledger-name">{plan.title}</span>
                <span className="ledger-meta">{meta}</span>
              </summary>
              <form className="compose cols-2 todo-plan-form" onSubmit={(e) => void onSave(plan.id, e)}>
                <Field label="事项" className="span-2">
                  <input name="title" defaultValue={plan.title} required />
                </Field>
                <Field label="每隔（天）">
                  <input name="everyDays" type="number" min="1" defaultValue={plan.everyDays} />
                </Field>
                <Field label="上次完成">
                  <DateSelect name="lastDoneAt" defaultValue={plan.lastDoneAt} />
                </Field>
                <Field label="备注" className="span-2">
                  <input name="note" defaultValue={plan.note} />
                </Field>
                <label className="todo-enabled span-2">
                  <input name="enabled" type="checkbox" defaultChecked={plan.enabled} />
                  启用
                </label>
                <button className="btn" type="submit">
                  存
                </button>
                <button className="btn" type="button" onClick={() => void markMaintainDone(plan.id)}>
                  刚做完
                </button>
                {plan.roomId ? (
                  <Link className="btn" to={`/home/room/${plan.roomId}`}>
                    去房间
                  </Link>
                ) : (
                  <span />
                )}
                <button
                  className="btn danger span-2"
                  type="button"
                  onClick={() => {
                    void (async () => {
                      await db.maintains.delete(plan.id)
                      await syncMaintainTasks()
                    })()
                  }}
                >
                  除去
                </button>
              </form>
            </details>
          </li>
        )
      })}
    </ul>
  )
}
