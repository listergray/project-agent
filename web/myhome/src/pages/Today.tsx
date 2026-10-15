import { useLiveQuery } from 'dexie-react-hooks'
import { AnimatePresence, motion } from 'motion/react'
import { type FormEvent, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Chapter } from '../components/Chapter'
import { DateSelect } from '../components/DateSelect'
import { Field, readForm } from '../components/Field'
import { db, type Task } from '../db'
import {
  addDays,
  formatLedgerDayKey,
  nid,
  todayKey,
} from '../lib/dates'
import { hourLabel, writeDayHour } from '../lib/dayHours'
import { syncMaintainTasks, toggleMaintainTask } from '../lib/maintain'

const HOURS = Array.from({ length: 24 }, (_, h) => h)

export function Today() {
  const today = todayKey()
  const [viewDate, setViewDate] = useState(today)
  const isToday = viewDate === today
  const settings = useLiveQuery(() => db.settings.get('main'))
  const tasks = useLiveQuery(() => db.tasks.toArray()) ?? []
  const hourRows =
    useLiveQuery(() => db.dayHours.where('date').equals(viewDate).toArray()) ??
    []

  useEffect(() => {
    if (viewDate > today) setViewDate(today)
  }, [today, viewDate])

  useEffect(() => {
    if (isToday) void syncMaintainTasks(today)
  }, [today, isToday])

  const due = tasks.filter((t) => t.date === viewDate && !t.done)
  const overdue = isToday
    ? tasks.filter((t) => t.date < today && !t.done)
    : []
  const done = tasks.filter((t) => t.date === viewDate && t.done)
  const filledHours = hourRows.filter((r) => r.content.trim()).length

  async function addTask(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    const title = String(fd.get('title') ?? '').trim()
    if (!title) return
    await db.tasks.add({
      id: nid(),
      title,
      date: viewDate,
      done: false,
      sourceKind: '',
      sourceId: '',
      createdAt: Date.now(),
    })
    e.currentTarget.reset()
  }

  const dayLabel = formatLedgerDayKey(viewDate)
  const hint = isToday
    ? `${dayLabel}。${settings?.pathTitle ? `此路：${settings.pathTitle}。` : ''}当天该做的事，做完划掉即可。可翻看往日。`
    : `${dayLabel}。正在回看这一日的记载。`

  return (
    <Chapter index="贰" title="今日" hint={hint}>
      <nav className="day-nav" aria-label="择日">
        <button type="button" onClick={() => setViewDate(addDays(viewDate, -1))}>
          前一日
        </button>
        <span className="day-nav-label">
          {dayLabel}
          {isToday ? ' · 今日' : ''}
        </span>
        <button
          type="button"
          disabled={isToday}
          onClick={() => setViewDate(addDays(viewDate, 1))}
        >
          后一日
        </button>
        {!isToday ? (
          <button type="button" onClick={() => setViewDate(today)}>
            回到今日
          </button>
        ) : null}
        <label className="day-nav-pick">
          <span className="sr-only">跳至日期</span>
          <DateSelect
            value={viewDate}
            max={today}
            allowEmpty={false}
            onChange={(next) => {
              if (next && next <= today) setViewDate(next)
            }}
          />
        </label>
      </nav>

      <p className="section-lead">
        定期待办在 <Link to="/todos">待办</Link> 章维护；到期后会自动出现在下方。
      </p>
      <form className="compose" onSubmit={(e) => void addTask(e)}>
        <Field label="要做">
          <input
            name="title"
            required
            placeholder={
              isToday ? '写下一件今天该做的事' : '补记这一日该做的事'
            }
          />
        </Field>
        <button className="btn" type="submit">
          {isToday ? '列入今日' : '记入此日'}
        </button>
      </form>

      {overdue.length > 0 ? (
        <section className="section">
          <h2>过期未了</h2>
          <p className="section-lead">昨日留下的，仍算未完成。</p>
          <TaskList items={overdue} />
        </section>
      ) : null}

      <section className="section">
        <h2>{isToday ? '当为' : '未了'}</h2>
        {due.length === 0 ? (
          <p className="empty">{isToday ? '今日尚未落笔。' : '这一日没有未了之事。'}</p>
        ) : (
          <TaskList items={due} />
        )}
      </section>

      {done.length > 0 ? (
        <section className="section">
          <h2>已了</h2>
          <TaskList items={done} />
        </section>
      ) : null}

      <section className="section">
        <h2>一日二十四</h2>
        <p className="section-lead">
          将昼夜分为二十四格，记这一时辰做了什么。已记 {filledHours} / 24。
        </p>
        <HourLedger date={viewDate} rows={hourRows} markCurrent={isToday} />
      </section>
    </Chapter>
  )
}

function HourLedger({
  date,
  rows,
  markCurrent,
}: {
  date: string
  rows: Array<{ hour: number; content: string }>
  markCurrent: boolean
}) {
  const byHour = new Map(rows.map((r) => [r.hour, r.content]))
  const nowHour = new Date().getHours()
  const listRef = useRef<HTMLUListElement>(null)

  useEffect(() => {
    if (!markCurrent) return
    const el = listRef.current?.querySelector(`[data-hour="${nowHour}"]`)
    el?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  }, [nowHour, date, markCurrent])

  return (
    <ul className="hour-ledger" ref={listRef}>
      {HOURS.map((hour) => (
        <HourSlot
          key={`${date}-${hour}`}
          date={date}
          hour={hour}
          content={byHour.get(hour) ?? ''}
          current={markCurrent && hour === nowHour}
        />
      ))}
    </ul>
  )
}

function HourSlot({
  date,
  hour,
  content,
  current,
}: {
  date: string
  hour: number
  content: string
  current: boolean
}) {
  const [draft, setDraft] = useState(content)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    setDraft(content)
  }, [content, date, hour])

  async function commit() {
    if (draft.trim() === content.trim()) return
    setSaving(true)
    try {
      await writeDayHour(date, hour, draft)
    } finally {
      setSaving(false)
    }
  }

  return (
    <li
      className={current ? 'hour-slot current' : 'hour-slot'}
      data-hour={hour}
    >
      <span className="hour-slot-time" title={`${hour} 时`}>
        {hourLabel(hour)}
      </span>
      <input
        className="hour-slot-input"
        value={draft}
        placeholder={current ? '此时…' : '空'}
        aria-label={`${hourLabel(hour)} 事项`}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={() => void commit()}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.currentTarget.blur()
          }
        }}
      />
      {saving ? <span className="hour-slot-save">记</span> : null}
    </li>
  )
}

function TaskList({ items }: { items: Task[] }) {
  return (
    <ul className="ledger">
      <AnimatePresence>
        {items.map((task) => (
          <motion.li
            key={task.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, height: 0 }}
            layout
          >
            <div className="ledger-row">
              <button
                type="button"
                className={task.done ? 'ledger-check on' : 'ledger-check'}
                onClick={() => void toggleMaintainTask(task, !task.done)}
              >
                {task.done ? '已' : '未'}
              </button>
              <div className={task.done ? 'ledger-name done' : 'ledger-name'}>
                {task.title}
              </div>
              <div className="ledger-actions">
                <button type="button" onClick={() => void db.tasks.delete(task.id)}>
                  除去
                </button>
              </div>
            </div>
          </motion.li>
        ))}
      </AnimatePresence>
    </ul>
  )
}
