import { useLiveQuery } from 'dexie-react-hooks'
import { motion, useReducedMotion } from 'motion/react'
import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Chapter } from '../components/Chapter'
import { Field, readForm } from '../components/Field'
import { db, type LifeSquare } from '../db'
import { formatMoney } from '../lib/format'
import { LIFE_SQUARES, SCORE_HAN, type LifeSquareId } from '../lib/squares'

export function Nine() {
  const reduce = useReducedMotion()
  const [open, setOpen] = useState<LifeSquareId | null>(null)
  const rows = useLiveQuery(() => db.lifeSquares.toArray()) ?? []
  const byId = new Map(rows.map((row) => [row.id, row]))
  const echoes = useLedgerEchoes()
  const scored = LIFE_SQUARES.map((def) => ({
    def,
    row: byId.get(def.id),
    echo: echoes[def.id],
  }))
  const rated = scored.filter((cell) => (cell.row?.score ?? 0) > 0)
  const avg =
    rated.length > 0
      ? rated.reduce((sum, cell) => sum + (cell.row?.score ?? 0), 0) / rated.length
      : 0
  const weak = scored
    .filter((cell) => (cell.row?.score ?? 0) > 0 && (cell.row?.score ?? 0) <= 4)
    .map((cell) => cell.def.name)

  return (
    <Chapter
      index="陆"
      title="九宫"
      hint="人生平衡九格。分数是此刻的体感，不是考核。账本里已有的，会写在格下。"
    >
      <p className="muted">已评均分</p>
      <p className="total tabular">{rated.length ? avg.toFixed(1) : '—'}</p>
      <p className="muted">
        {rated.length ? `已评 ${rated.length} 格` : '尚未落笔'}
        {weak.length ? ` · 偏弱：${weak.join('、')}` : ''}
      </p>

      <div className="nine-board">
        {scored.map((cell, i) => {
          const score = cell.row?.score ?? 0
          const active = open === cell.def.id
          return (
            <motion.button
              key={cell.def.id}
              type="button"
              className={
                active
                  ? 'nine-cell on'
                  : score > 0 && score <= 4
                    ? 'nine-cell weak'
                    : 'nine-cell'
              }
              initial={reduce ? false : { opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04, duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
              onClick={() => setOpen(active ? null : cell.def.id)}
            >
              <span className="nine-name">{cell.def.name}</span>
              <span className="nine-score tabular">{SCORE_HAN[score]}</span>
              <span className="nine-prompt">{cell.def.prompt}</span>
              <span className="nine-echo">{cell.echo}</span>
            </motion.button>
          )
        })}
      </div>

      {open ? (
        <SquareEditor
          key={open}
          def={LIFE_SQUARES.find((s) => s.id === open)!}
          row={byId.get(open)}
          echo={echoes[open]}
          onClose={() => setOpen(null)}
        />
      ) : (
        <p className="section-lead" style={{ marginTop: '1.6rem' }}>
          点一格，写下分数与近况。
        </p>
      )}
    </Chapter>
  )
}

function SquareEditor({
  def,
  row,
  echo,
  onClose,
}: {
  def: (typeof LIFE_SQUARES)[number]
  row: LifeSquare | undefined
  echo: string
  onClose: () => void
}) {
  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    await db.lifeSquares.put({
      id: def.id,
      score: Number(fd.get('score') || 0),
      note: String(fd.get('note') ?? '').trim(),
      intention: String(fd.get('intention') ?? '').trim(),
      updatedAt: Date.now(),
    })
  }

  return (
    <section className="section">
      <h2>{def.name}</h2>
      <p className="section-lead">
        {def.prompt}
        {echo !== '账本尚空' ? ` · ${echo}` : ''}
      </p>
      <form className="compose cols-2" onSubmit={(e) => void save(e)}>
        <Field label="此刻分数">
          <select name="score" defaultValue={String(row?.score ?? 0)}>
            {SCORE_HAN.map((label, n) => (
              <option key={label} value={n}>
                {n === 0 ? '未评' : `${n} · ${label}`}
              </option>
            ))}
          </select>
        </Field>
        <Field label="此格通向">
          <Link className="nine-link" to={def.href}>
            {def.hrefLabel}
          </Link>
        </Field>
        <Field label="近况" className="span-2">
          <textarea name="note" defaultValue={row?.note ?? ''} placeholder="这一格现在怎样" />
        </Field>
        <Field label="下一季要顾" className="span-2">
          <input name="intention" defaultValue={row?.intention ?? ''} placeholder="可选" />
        </Field>
        <button className="btn" type="submit">
          记下
        </button>
        <button className="btn" type="button" onClick={onClose}>
          收起
        </button>
      </form>
    </section>
  )
}

function useLedgerEchoes(): Record<LifeSquareId, string> {
  const health = useLiveQuery(() => db.healthLogs.orderBy('date').reverse().first())
  const money = useLiveQuery(() => db.moneyAssets.toArray()) ?? []
  const digital = useLiveQuery(() => db.digitalAssets.toArray()) ?? []
  const things = useLiveQuery(() => db.possessions.toArray()) ?? []
  const skills = useLiveQuery(() => db.skillAssets.toArray()) ?? []
  const works = useLiveQuery(() => db.workRecords.toArray()) ?? []
  const people = useLiveQuery(() => db.people.toArray()) ?? []
  const goals = useLiveQuery(() => db.goals.toArray()) ?? []

  const net =
    money.reduce((s, r) => s + r.amount, 0) +
    digital.reduce((s, r) => s + r.estimatedValue, 0) +
    things.reduce((s, r) => s + r.estimatedValue, 0)
  const currentWork = works.filter((w) => !w.endedAt)
  const family = people.filter((p) => p.relation === '家人')
  const social = people.filter((p) => p.relation !== '家人')
  const lifeGoals = goals.filter((g) => g.status === 'active')

  const healthBits = health
    ? [
        health.sleepHours != null ? `睡 ${health.sleepHours} 时` : null,
        health.energy != null ? `精力 ${health.energy}` : null,
        health.exerciseMin != null ? `动 ${health.exerciseMin} 分` : null,
      ]
        .filter(Boolean)
        .join(' · ')
    : ''

  return {
    health: healthBits || '尚未记身体',
    career: currentWork.length
      ? `在任 ${currentWork.length} · 技能 ${skills.length}`
      : skills.length
        ? `技能 ${skills.length} 项`
        : '尚未记工作',
    wealth: net ? `净值 ${formatMoney(net)}` : '尚未估价',
    family: family.length ? `家人 ${family.length} 人` : '尚未记家人',
    social: social.length ? `所识 ${social.length} 人` : '尚未记友人',
    learning: skills.length ? `技能 ${skills.length} 项` : '尚未记技能',
    leisure: '以近况自记',
    inner: '以近况自记',
    purpose: lifeGoals.length ? `进行中志向 ${lifeGoals.length}` : '尚未立目标',
  }
}
