import { useEffect, useMemo, useState } from 'react'
import { pad2 } from '../lib/dates'

type DateSelectProps = {
  name?: string
  /** YYYY-MM-DD；受控 */
  value?: string
  /** YYYY-MM-DD；非受控初始值 */
  defaultValue?: string
  onChange?: (iso: string) => void
  required?: boolean
  /** YYYY-MM-DD */
  min?: string
  /** YYYY-MM-DD */
  max?: string
  /** 允许空（不选）；表单里提交为空字符串 */
  allowEmpty?: boolean
  className?: string
  id?: string
}

function daysInMonth(year: number, month: number) {
  return new Date(year, month, 0).getDate()
}

function parseIso(iso: string | undefined) {
  if (!iso || !/^\d{4}-\d{2}-\d{2}$/.test(iso)) return null
  const [y, m, d] = iso.split('-').map(Number)
  if (!y || !m || !d) return null
  return { y, m, d }
}

function toIso(year: number, month: number, day: number) {
  const maxD = daysInMonth(year, month)
  const d = Math.min(day, maxD)
  return `${year}-${pad2(month)}-${pad2(d)}`
}

function yearBounds(min?: string, max?: string) {
  const now = new Date().getFullYear()
  const minY = parseIso(min)?.y ?? Math.min(1920, now - 100)
  const maxY = parseIso(max)?.y ?? now + 30
  return { minY, maxY }
}

export function DateSelect({
  name,
  value,
  defaultValue = '',
  onChange,
  required,
  min,
  max,
  allowEmpty = !required,
  className,
  id,
}: DateSelectProps) {
  const controlled = value !== undefined
  const [inner, setInner] = useState(defaultValue)
  const iso = controlled ? (value ?? '') : inner

  useEffect(() => {
    if (!controlled) setInner(defaultValue)
  }, [controlled, defaultValue])

  const parts = parseIso(iso)
  const { minY, maxY } = useMemo(() => yearBounds(min, max), [min, max])

  const years = useMemo(() => {
    const list: number[] = []
    for (let y = maxY; y >= minY; y -= 1) list.push(y)
    return list
  }, [minY, maxY])

  const year = parts?.y ?? ''
  const month = parts?.m ?? ''
  const day = parts?.d ?? ''
  const dayMax =
    typeof year === 'number' && typeof month === 'number'
      ? daysInMonth(year, month)
      : 31

  function emit(next: string) {
    if (next) {
      if (min && next < min) return
      if (max && next > max) return
    }
    if (!controlled) setInner(next)
    onChange?.(next)
  }

  function setPart(kind: 'y' | 'm' | 'd', raw: string) {
    if (!raw) {
      emit('')
      return
    }
    const n = Number(raw)
    const nowY = new Date().getFullYear()
    const nextY = kind === 'y' ? n : (parts?.y ?? nowY)
    const nextM = kind === 'm' ? n : (parts?.m ?? 1)
    const nextD = kind === 'd' ? n : (parts?.d ?? 1)
    emit(toIso(nextY, nextM, nextD))
  }

  return (
    <div className={className ? `date-select ${className}` : 'date-select'} id={id}>
      {name ? (
        <input type="hidden" name={name} value={iso} required={required && !iso} readOnly />
      ) : null}
      <select
        aria-label="年"
        value={year === '' ? '' : String(year)}
        required={required}
        onChange={(e) => setPart('y', e.target.value)}
      >
        {allowEmpty ? <option value="">年</option> : null}
        {years.map((y) => (
          <option key={y} value={y}>
            {y}年
          </option>
        ))}
      </select>
      <select
        aria-label="月"
        value={month === '' ? '' : String(month)}
        required={required}
        onChange={(e) => setPart('m', e.target.value)}
      >
        {allowEmpty ? <option value="">月</option> : null}
        {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
          <option key={m} value={m}>
            {m}月
          </option>
        ))}
      </select>
      <select
        aria-label="日"
        value={day === '' ? '' : String(day)}
        required={required}
        onChange={(e) => setPart('d', e.target.value)}
      >
        {allowEmpty ? <option value="">日</option> : null}
        {Array.from({ length: dayMax }, (_, i) => i + 1).map((d) => (
          <option key={d} value={d}>
            {d}日
          </option>
        ))}
      </select>
    </div>
  )
}
