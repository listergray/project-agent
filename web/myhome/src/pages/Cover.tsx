import { useLiveQuery } from 'dexie-react-hooks'
import { motion, useReducedMotion } from 'motion/react'
import { lazy, Suspense, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { CountUp } from '../bits/CountUp'
import { db } from '../db'
import { pad2 } from '../lib/dates'
import { formatDayCount, useLife } from '../lib/life'

const ShanShui = lazy(() =>
  import('../bits/ShanShui').then((mod) => ({ default: mod.ShanShui })),
)

const chapters = [
  { to: '/assets', index: '壹', name: '资产', desc: '数字、实物与技能', tone: 'blue' },
  { to: '/today', index: '贰', name: '今日', desc: '当天要做的事', tone: 'slate' },
  { to: '/todos', index: '待', name: '待办', desc: '定期维护与周期计划', tone: 'teal' },
  { to: '/goals', index: '叁', name: '目标', desc: '此后要去的地方', tone: 'violet' },
  { to: '/body', index: '肆', name: '身体', desc: '此身此刻的状况', tone: 'teal' },
  { to: '/people', index: '伍', name: '交际', desc: '我所识的人', tone: 'slate' },
  { to: '/nine', index: '陆', name: '九宫', desc: '人生平衡自查', tone: 'violet' },
  { to: '/home', index: '柒', name: '小屋', desc: '租房与房间里的物', tone: 'amber' },
  { to: '/settings', index: '册', name: '册上', desc: '生辰、寿数与备份', tone: 'slate' },
]

function canWebGL() {
  try {
    const canvas = document.createElement('canvas')
    return Boolean(canvas.getContext('webgl2') || canvas.getContext('webgl'))
  } catch {
    return false
  }
}

export function Cover() {
  const reduce = useReducedMotion()
  const settings = useLiveQuery(() => db.settings.get('main'))
  const life = useLife(settings?.birthDate, settings?.expectedYears)
  const [liveDays, setLiveDays] = useState(false)
  const [use3d, setUse3d] = useState(false)
  const ctaTo = life.ready ? '#contents' : '/settings'
  const ctaLabel = life.ready ? '翻开账本' : '先写下生辰'

  useEffect(() => {
    setUse3d(!reduce && canWebGL())
  }, [reduce])

  useEffect(() => {
    if (!life.ready || life.expired) {
      setLiveDays(true)
      return
    }
    setLiveDays(false)
    const id = window.setTimeout(() => setLiveDays(true), 2200)
    return () => window.clearTimeout(id)
  }, [life.ready, life.expired, settings?.birthDate])

  return (
    <div className="site-cover">
      <section className="cover-hero">
        {use3d ? (
          <Suspense fallback={null}>
            <div className="cover-visual-bg" aria-hidden>
              <ShanShui />
            </div>
          </Suspense>
        ) : null}
        <div className="cover-hero-grid">
          <motion.div
            className="dsh-hero-card accent"
            initial={reduce ? false : { opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
          >
            <p className="dsh-kicker">我的所有</p>
            <h1 className="cover-days tabular">
              {life.ready && !life.expired ? (
                <>
                  {liveDays ? formatDayCount(life.remainingDays) : <CountUp to={life.remainingDays} />}
                  <span className="unit">日</span>
                </>
              ) : life.expired ? (
                '所记寿数已尽'
              ) : (
                '尚未写入生辰'
              )}
            </h1>
            <p className="dsh-hero-copy">剩余的日子，是真正拥有的部分。</p>
            {life.ready && !life.expired ? (
              <p className="cover-hms tabular" aria-live="polite">
                还余 {pad2(life.hours)} 时 {pad2(life.minutes)} 分 {pad2(life.seconds)} 秒
              </p>
            ) : null}
            {life.ready ? (
              <div className="life-rule" aria-hidden>
                <i style={{ width: `${Math.max(4, life.remainingRatio * 100)}%` }} />
              </div>
            ) : null}
          </motion.div>

          <motion.div
            className="dsh-hero-card"
            initial={reduce ? false : { opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.08, ease: [0.16, 1, 0.3, 1] }}
          >
            <p className="dsh-kicker">LEDGER</p>
            <p className="dsh-hero-copy strong">翻开账本，记下此身所有。</p>
            {settings?.pathTitle ? (
              <p className="dsh-hero-copy">
                此路 · {settings.pathTitle}
                {settings.pathLine ? ` · ${settings.pathLine}` : ''}
              </p>
            ) : (
              <p className="dsh-hero-copy">金钱、时间、身体、交际、目标，皆在此册。</p>
            )}
            {ctaTo.startsWith('#') ? (
              <a className="dsh-pill on" href={ctaTo}>
                {ctaLabel} ↗
              </a>
            ) : (
              <Link className="dsh-pill on" to={ctaTo}>
                {ctaLabel} ↗
              </Link>
            )}
          </motion.div>
        </div>
      </section>

      <nav id="contents" className="cover-catalog">
        <div className="cover-catalog-head">
          <div>
            <p className="dsh-kicker">CHAPTERS</p>
            <h2 className="cover-catalog-title">账本目录</h2>
            <p className="section-lead">选一章，开始记录。</p>
          </div>
        </div>
        <div className="dsh-grid cover-chapters">
          {chapters.map((item, i) => (
            <motion.div
              key={item.to}
              initial={reduce ? false : { opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ delay: i * 0.04, duration: 0.4 }}
            >
              <Link to={item.to} className={`dsh-card tone-${item.tone}`}>
                <div className="dsh-card-top">
                  <span className="dsh-kicker">{item.index}</span>
                </div>
                <p className="dsh-meta">{item.desc}</p>
                <h3 className="dsh-card-title">{item.name}</h3>
                <span className="dsh-card-link">进入 →</span>
              </Link>
            </motion.div>
          ))}
        </div>
      </nav>
    </div>
  )
}
