import { useLiveQuery } from 'dexie-react-hooks'
import { useState, type FormEvent } from 'react'
import { Chapter } from '../components/Chapter'
import { Field, readForm } from '../components/Field'
import { db, type HealthLog } from '../db'
import { nid, todayKey } from '../lib/dates'

export function Body() {
  const today = todayKey()
  const logs = useLiveQuery(() => db.healthLogs.orderBy('date').reverse().toArray()) ?? []
  const todayLog = logs.find((row) => row.date === today)
  const recent = logs.slice(0, 14)
  const weights = [...logs]
    .filter((row) => row.weightKg != null)
    .slice(0, 14)
    .reverse() as (HealthLog & { weightKg: number })[]

  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    const payload = {
      date: today,
      sleepHours: numOrNull(fd.get('sleepHours')),
      weightKg: numOrNull(fd.get('weightKg')),
      energy: numOrNull(fd.get('energy')),
      exerciseMin: numOrNull(fd.get('exerciseMin')),
      note: String(fd.get('note') ?? '').trim(),
    }
    if (todayLog) {
      await db.healthLogs.update(todayLog.id, payload)
    } else {
      await db.healthLogs.add({ id: nid(), ...payload })
    }
  }

  return (
    <Chapter index="肆" title="身体" hint="只记你自己能感觉到的：睡了多久，多重，有没有力气。">
      <form className="compose cols-3" onSubmit={(e) => void save(e)} key={todayLog?.id ?? 'new-log'}>
        <Field label="睡眠（小时）">
          <input
            name="sleepHours"
            type="number"
            min="0"
            max="24"
            step="0.1"
            defaultValue={todayLog?.sleepHours ?? ''}
          />
        </Field>
        <Field label="体重（公斤）">
          <input
            name="weightKg"
            type="number"
            min="0"
            step="0.1"
            defaultValue={todayLog?.weightKg ?? ''}
          />
        </Field>
        <Field label="运动（分钟）">
          <input
            name="exerciseMin"
            type="number"
            min="0"
            step="1"
            defaultValue={todayLog?.exerciseMin ?? ''}
          />
        </Field>
        <EnergyField defaultValue={todayLog?.energy ?? 3} />
        <Field label="一句" className="span-2">
          <input name="note" defaultValue={todayLog?.note ?? ''} placeholder="今日身体如何" />
        </Field>
        <button className="btn span-3" type="submit">
          记下今日
        </button>
      </form>

      {weights.length >= 2 ? (
        <section className="section">
          <h2>体重走势</h2>
          <Spark points={weights.map((row) => row.weightKg)} />
        </section>
      ) : null}

      <section className="section">
        <h2>近况</h2>
        {recent.length === 0 ? (
          <p className="empty">还没有身体记录。</p>
        ) : (
          <ul className="history">
            {recent.map((row) => (
              <li key={row.id}>
                <span>{row.date.slice(5)}</span>
                <span>
                  {[
                    row.sleepHours != null ? `睡 ${row.sleepHours} 时` : null,
                    row.weightKg != null ? `${row.weightKg} kg` : null,
                    row.energy != null ? `精力 ${row.energy}` : null,
                    row.exerciseMin != null ? `动 ${row.exerciseMin} 分` : null,
                    row.note,
                  ]
                    .filter(Boolean)
                    .join(' · ')}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </Chapter>
  )
}

function EnergyField({ defaultValue }: { defaultValue: number }) {
  const [value, setValue] = useState(defaultValue)

  return (
    <div className="field">
      <span className="field-label">精力</span>
      <input type="hidden" name="energy" value={value} />
      <div className="energy" role="group" aria-label="精力一至五">
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            type="button"
            className={n <= value ? 'on' : undefined}
            aria-label={`精力 ${n}`}
            onClick={() => setValue(n)}
          />
        ))}
      </div>
    </div>
  )
}

function Spark({ points }: { points: number[] }) {
  const min = Math.min(...points)
  const max = Math.max(...points)
  const span = max - min || 1
  const w = 320
  const h = 64
  const d = points
    .map((y, i) => {
      const x = (i / (points.length - 1)) * w
      const yy = h - 8 - ((y - min) / span) * (h - 16)
      return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${yy.toFixed(1)}`
    })
    .join(' ')

  return (
    <svg className="spark" viewBox={`0 0 ${w} ${h}`} aria-hidden>
      <path d={d} />
    </svg>
  )
}

function numOrNull(value: FormDataEntryValue | null) {
  const text = String(value ?? '').trim()
  if (!text) return null
  const n = Number(text)
  return Number.isFinite(n) ? n : null
}
