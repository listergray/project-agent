import { useLiveQuery } from 'dexie-react-hooks'
import { AnimatePresence, motion } from 'motion/react'
import { useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { Link, Navigate, useParams } from 'react-router-dom'
import { Chapter } from '../components/Chapter'
import { DateSelect } from '../components/DateSelect'
import { Field, readForm } from '../components/Field'
import {
  DIGITAL_LABELS,
  LEVEL_LABELS,
  MONEY_LABELS,
  POSSESSION_LABELS,
  SKILL_LABELS,
  WORK_LABELS,
  db,
  type DigitalAsset,
  type DigitalCategory,
  type MoneyAsset,
  type MoneyCategory,
  type Possession,
  type PossessionCategory,
  type SkillAsset,
  type SkillCategory,
  type SkillLevel,
  type WorkKind,
  type WorkRecord,
} from '../db'
import { ASSET_KINDS, isAssetKind } from '../lib/assetKinds'
import { formatPeriod, formatShortDate, nid } from '../lib/dates'
import { formatMoney } from '../lib/format'
import { peekNextMoneyMonthly, syncMoneyMonthly } from '../lib/moneyMonthly'

const moneyCats = Object.keys(MONEY_LABELS) as MoneyCategory[]
const thingCats = Object.keys(POSSESSION_LABELS) as PossessionCategory[]
const digitalCats = Object.keys(DIGITAL_LABELS) as DigitalCategory[]
const skillCats = Object.keys(SKILL_LABELS) as SkillCategory[]
const skillLevels = Object.keys(LEVEL_LABELS) as SkillLevel[]
const workKinds = Object.keys(WORK_LABELS) as WorkKind[]

export function Assets() {
  const { kind } = useParams()
  const money = useLiveQuery(() => db.moneyAssets.orderBy('updatedAt').reverse().toArray()) ?? []
  const things = useLiveQuery(() => db.possessions.orderBy('updatedAt').reverse().toArray()) ?? []
  const digital = useLiveQuery(() => db.digitalAssets.orderBy('updatedAt').reverse().toArray()) ?? []
  const skills = useLiveQuery(() => db.skillAssets.orderBy('updatedAt').reverse().toArray()) ?? []
  const works = useLiveQuery(() => db.workRecords.orderBy('startedAt').reverse().toArray()) ?? []

  useEffect(() => {
    void syncMoneyMonthly()
  }, [])

  const moneySum = money.reduce((sum, row) => sum + row.amount, 0)
  const thingSum = things.reduce((sum, row) => sum + row.estimatedValue, 0)
  const digitalSum = digital.reduce((sum, row) => sum + row.estimatedValue, 0)

  if (kind && !isAssetKind(kind)) return <Navigate to="/assets" replace />

  if (!kind) {
    return (
      <Chapter index="壹" title="资产" hint="金钱、数字、实物可估价；技能与工作同属你所拥有的。点开一栏记账。">
        <p className="muted">可估价合计</p>
        <p className="total tabular">{formatMoney(moneySum + digitalSum + thingSum)}</p>
        <p className="muted">
          金钱 {formatMoney(moneySum)} · 数字 {formatMoney(digitalSum)} · 实物 {formatMoney(thingSum)}
          {skills.length ? ` · 技能 ${skills.length} 项` : ''}
          {works.length ? ` · 工作 ${works.length} 条` : ''}
        </p>
        <ul className="toc-list asset-index">
          {ASSET_KINDS.map((item) => (
            <li key={item.id}>
              <Link to={`/assets/${item.id}`}>
                <span className="toc-index">栏</span>
                <span className="toc-name">{item.name}</span>
                <span className="toc-desc">{item.hint}</span>
              </Link>
            </li>
          ))}
        </ul>
      </Chapter>
    )
  }

  const meta = ASSET_KINDS.find((item) => item.id === kind)!

  return (
    <Chapter index="壹" title={meta.name} hint={meta.hint}>
      {kind === 'money' ? (
        <>
          <p className="muted">本栏合计</p>
          <p className="total tabular">{formatMoney(moneySum)}</p>
          <MoneyForm />
          <AssetList empty="尚无登记。先记下第一笔。">
            {money.map((row) => (
              <MoneyRow key={row.id} item={row} />
            ))}
          </AssetList>
        </>
      ) : null}
      {kind === 'digital' ? (
        <>
          <p className="muted">本栏估值</p>
          <p className="total tabular">{formatMoney(digitalSum)}</p>
          <DigitalForm />
          <AssetList empty="还没有写下任何数字资产。">
            {digital.map((row) => (
              <DigitalRow key={row.id} item={row} />
            ))}
          </AssetList>
        </>
      ) : null}
      {kind === 'things' ? (
        <>
          <p className="muted">本栏估值</p>
          <p className="total tabular">{formatMoney(thingSum)}</p>
          <ThingForm />
          <AssetList empty="还没有写下任何物件。">
            {things.map((row) => (
              <ThingRow key={row.id} item={row} />
            ))}
          </AssetList>
        </>
      ) : null}
      {kind === 'skills' ? (
        <>
          <p className="muted">已记</p>
          <p className="total tabular">{skills.length} 项</p>
          <SkillForm />
          <AssetList empty="还没有写下任何技能。">
            {skills.map((row) => (
              <SkillRow key={row.id} item={row} />
            ))}
          </AssetList>
        </>
      ) : null}
      {kind === 'work' ? (
        <>
          <p className="muted">已记</p>
          <p className="total tabular">{works.length} 条</p>
          <WorkForm />
          <AssetList empty="还没有写下任何工作。">
            {works.map((row) => (
              <WorkRow key={row.id} item={row} />
            ))}
          </AssetList>
        </>
      ) : null}
    </Chapter>
  )
}

function AssetList({ empty, children }: { empty: string; children: ReactNode }) {
  const items = Array.isArray(children) ? children : children ? [children] : []
  if (items.length === 0) return <p className="empty">{empty}</p>
  return <ul className="ledger">{children}</ul>
}

function MoneyForm() {
  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    const name = String(fd.get('name') ?? '').trim()
    if (!name) return
    await db.moneyAssets.add({
      id: nid(),
      name,
      category: String(fd.get('category') ?? 'cash') as MoneyCategory,
      amount: Number(fd.get('amount') || 0),
      note: String(fd.get('note') ?? '').trim(),
      monthlyAdd: Math.max(0, Number(fd.get('monthlyAdd') || 0)),
      monthlyDay: Math.min(28, Math.max(1, Math.round(Number(fd.get('monthlyDay') || 1)))),
      lastMonthlyAt: '',
      updatedAt: Date.now(),
    })
    e.currentTarget.reset()
  }

  return (
    <form className="compose cols-3" onSubmit={(e) => void onSubmit(e)}>
      <Field label="名称">
        <input name="name" required placeholder="如：工资卡" />
      </Field>
      <Field label="类别">
        <select name="category" defaultValue="deposit">
          {moneyCats.map((key) => (
            <option key={key} value={key}>
              {MONEY_LABELS[key]}
            </option>
          ))}
        </select>
      </Field>
      <Field label="金额">
        <input name="amount" type="number" min="0" step="0.01" defaultValue="0" />
      </Field>
      <Field label="每月递增">
        <input name="monthlyAdd" type="number" min="0" step="0.01" defaultValue="0" placeholder="0 为关闭" />
      </Field>
      <Field label="每月几号">
        <input name="monthlyDay" type="number" min="1" max="28" defaultValue="1" />
      </Field>
      <Field label="备注" className="span-1">
        <input name="note" placeholder="可选" />
      </Field>
      <button className="btn span-3" type="submit">
        记一笔
      </button>
    </form>
  )
}

function DigitalForm() {
  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    const name = String(fd.get('name') ?? '').trim()
    if (!name) return
    await db.digitalAssets.add({
      id: nid(),
      name,
      category: String(fd.get('category') ?? 'account') as DigitalCategory,
      estimatedValue: Number(fd.get('estimatedValue') || 0),
      account: String(fd.get('account') ?? '').trim(),
      note: String(fd.get('note') ?? '').trim(),
      updatedAt: Date.now(),
    })
    e.currentTarget.reset()
  }

  return (
    <form className="compose cols-3" onSubmit={(e) => void onSubmit(e)}>
      <Field label="名称">
        <input name="name" required placeholder="如：主域名 / 交易所" />
      </Field>
      <Field label="类别">
        <select name="category" defaultValue="account">
          {digitalCats.map((key) => (
            <option key={key} value={key}>
              {DIGITAL_LABELS[key]}
            </option>
          ))}
        </select>
      </Field>
      <Field label="估值">
        <input name="estimatedValue" type="number" min="0" step="0.01" defaultValue="0" />
      </Field>
      <Field label="账号或地址">
        <input name="account" placeholder="邮箱、钱包、网址" />
      </Field>
      <Field label="备注" className="span-2">
        <input name="note" placeholder="可选" />
      </Field>
      <button className="btn span-3" type="submit">
        记一项
      </button>
    </form>
  )
}

function ThingForm() {
  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    const name = String(fd.get('name') ?? '').trim()
    if (!name) return
    await db.possessions.add({
      id: nid(),
      name,
      category: String(fd.get('category') ?? 'other') as PossessionCategory,
      estimatedValue: Number(fd.get('estimatedValue') || 0),
      acquiredAt: String(fd.get('acquiredAt') ?? ''),
      note: String(fd.get('note') ?? '').trim(),
      updatedAt: Date.now(),
    })
    e.currentTarget.reset()
  }

  return (
    <form className="compose cols-3" onSubmit={(e) => void onSubmit(e)}>
      <Field label="名称">
        <input name="name" required placeholder="如：相机" />
      </Field>
      <Field label="类别">
        <select name="category" defaultValue="electronics">
          {thingCats.map((key) => (
            <option key={key} value={key}>
              {POSSESSION_LABELS[key]}
            </option>
          ))}
        </select>
      </Field>
      <Field label="估值">
        <input name="estimatedValue" type="number" min="0" step="0.01" defaultValue="0" />
      </Field>
      <Field label="入手日期">
        <DateSelect name="acquiredAt" />
      </Field>
      <Field label="备注" className="span-2">
        <input name="note" placeholder="可选" />
      </Field>
      <button className="btn span-3" type="submit">
        记一件
      </button>
    </form>
  )
}

function SkillForm() {
  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    const name = String(fd.get('name') ?? '').trim()
    if (!name) return
    await db.skillAssets.add({
      id: nid(),
      name,
      category: String(fd.get('category') ?? 'tech') as SkillCategory,
      level: String(fd.get('level') ?? 'fluent') as SkillLevel,
      years: Number(fd.get('years') || 0),
      proof: String(fd.get('proof') ?? '').trim(),
      note: String(fd.get('note') ?? '').trim(),
      updatedAt: Date.now(),
    })
    e.currentTarget.reset()
  }

  return (
    <form className="compose cols-3" onSubmit={(e) => void onSubmit(e)}>
      <Field label="技能">
        <input name="name" required placeholder="如：TypeScript / 摄影" />
      </Field>
      <Field label="门类">
        <select name="category" defaultValue="tech">
          {skillCats.map((key) => (
            <option key={key} value={key}>
              {SKILL_LABELS[key]}
            </option>
          ))}
        </select>
      </Field>
      <Field label="程度">
        <select name="level" defaultValue="fluent">
          {skillLevels.map((key) => (
            <option key={key} value={key}>
              {LEVEL_LABELS[key]}
            </option>
          ))}
        </select>
      </Field>
      <Field label="年数">
        <input name="years" type="number" min="0" step="0.5" defaultValue="0" />
      </Field>
      <Field label="凭据" className="span-2">
        <input name="proof" placeholder="证书、作品、可演示的事" />
      </Field>
      <Field label="备注" className="span-3">
        <input name="note" placeholder="可选" />
      </Field>
      <button className="btn span-3" type="submit">
        记一项
      </button>
    </form>
  )
}

function WorkForm() {
  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    const title = String(fd.get('title') ?? '').trim()
    if (!title) return
    await db.workRecords.add({
      id: nid(),
      title,
      kind: String(fd.get('kind') ?? 'job') as WorkKind,
      org: String(fd.get('org') ?? '').trim(),
      role: String(fd.get('role') ?? '').trim(),
      startedAt: String(fd.get('startedAt') ?? ''),
      endedAt: String(fd.get('endedAt') ?? ''),
      summary: String(fd.get('summary') ?? '').trim(),
      updatedAt: Date.now(),
    })
    e.currentTarget.reset()
  }

  return (
    <form className="compose cols-3" onSubmit={(e) => void onSubmit(e)}>
      <Field label="名称">
        <input name="title" required placeholder="公司、项目或客户" />
      </Field>
      <Field label="类型">
        <select name="kind" defaultValue="job">
          {workKinds.map((key) => (
            <option key={key} value={key}>
              {WORK_LABELS[key]}
            </option>
          ))}
        </select>
      </Field>
      <Field label="角色">
        <input name="role" placeholder="如：前端 / 负责人" />
      </Field>
      <Field label="组织">
        <input name="org" placeholder="公司或团队，可选" />
      </Field>
      <Field label="开始">
        <DateSelect name="startedAt" />
      </Field>
      <Field label="结束">
        <DateSelect name="endedAt" />
      </Field>
      <Field label="做了什么" className="span-3">
        <textarea name="summary" placeholder="职责、成果、后来用得上的经验" />
      </Field>
      <button className="btn span-3" type="submit">
        记一条
      </button>
    </form>
  )
}

function MoneyRow({ item }: { item: MoneyAsset }) {
  const [open, setOpen] = useState(false)
  const monthlyOn = (item.monthlyAdd ?? 0) > 0
  const nextDue = monthlyOn ? peekNextMoneyMonthly(item) : ''

  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    const monthlyAdd = Math.max(0, Number(fd.get('monthlyAdd') || 0))
    const monthlyDay = Math.min(28, Math.max(1, Math.round(Number(fd.get('monthlyDay') || 1))))
    const prevAdd = item.monthlyAdd ?? 0
    await db.moneyAssets.update(item.id, {
      name: String(fd.get('name') ?? '').trim() || item.name,
      category: String(fd.get('category') ?? item.category) as MoneyCategory,
      amount: Number(fd.get('amount') || 0),
      note: String(fd.get('note') ?? '').trim(),
      monthlyAdd,
      monthlyDay,
      // Turning on from off: start fresh (don't backfill years)
      lastMonthlyAt: monthlyAdd > 0 && prevAdd <= 0 ? '' : (item.lastMonthlyAt ?? ''),
      updatedAt: Date.now(),
    })
    setOpen(false)
    await syncMoneyMonthly()
  }

  const metaParts = [
    MONEY_LABELS[item.category],
    monthlyOn ? `每月 +${formatMoney(item.monthlyAdd)}` : '',
    monthlyOn && nextDue ? `下次 ${formatShortDate(nextDue)}` : '',
    item.note || '',
  ].filter(Boolean)

  return (
    <li>
      <LedgerHead
        name={item.name}
        meta={metaParts.join(' · ')}
        amount={formatMoney(item.amount)}
        open={open}
        onToggle={() => setOpen((v) => !v)}
        onDelete={() => void db.moneyAssets.delete(item.id)}
      />
      <EditWrap open={open} onSubmit={save}>
        <Field label="名称">
          <input name="name" defaultValue={item.name} />
        </Field>
        <Field label="类别">
          <select name="category" defaultValue={item.category}>
            {moneyCats.map((key) => (
              <option key={key} value={key}>
                {MONEY_LABELS[key]}
              </option>
            ))}
          </select>
        </Field>
        <Field label="金额">
          <input name="amount" type="number" min="0" step="0.01" defaultValue={item.amount} />
        </Field>
        <Field label="每月递增">
          <input
            name="monthlyAdd"
            type="number"
            min="0"
            step="0.01"
            defaultValue={item.monthlyAdd ?? 0}
            placeholder="0 为关闭"
          />
        </Field>
        <Field label="每月几号">
          <input
            name="monthlyDay"
            type="number"
            min="1"
            max="28"
            defaultValue={item.monthlyDay ?? 1}
          />
        </Field>
        <Field label="备注" className="span-1">
          <input name="note" defaultValue={item.note} />
        </Field>
      </EditWrap>
    </li>
  )
}

function DigitalRow({ item }: { item: DigitalAsset }) {
  const [open, setOpen] = useState(false)

  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    await db.digitalAssets.update(item.id, {
      name: String(fd.get('name') ?? '').trim() || item.name,
      category: String(fd.get('category') ?? item.category) as DigitalCategory,
      estimatedValue: Number(fd.get('estimatedValue') || 0),
      account: String(fd.get('account') ?? '').trim(),
      note: String(fd.get('note') ?? '').trim(),
      updatedAt: Date.now(),
    })
    setOpen(false)
  }

  return (
    <li>
      <LedgerHead
        name={item.name}
        meta={`${DIGITAL_LABELS[item.category]}${item.account ? ` · ${item.account}` : ''}${
          item.note ? ` · ${item.note}` : ''
        }`}
        amount={formatMoney(item.estimatedValue)}
        open={open}
        onToggle={() => setOpen((v) => !v)}
        onDelete={() => void db.digitalAssets.delete(item.id)}
      />
      <EditWrap open={open} onSubmit={save}>
        <Field label="名称">
          <input name="name" defaultValue={item.name} />
        </Field>
        <Field label="类别">
          <select name="category" defaultValue={item.category}>
            {digitalCats.map((key) => (
              <option key={key} value={key}>
                {DIGITAL_LABELS[key]}
              </option>
            ))}
          </select>
        </Field>
        <Field label="估值">
          <input
            name="estimatedValue"
            type="number"
            min="0"
            step="0.01"
            defaultValue={item.estimatedValue}
          />
        </Field>
        <Field label="账号或地址">
          <input name="account" defaultValue={item.account} />
        </Field>
        <Field label="备注" className="span-2">
          <input name="note" defaultValue={item.note} />
        </Field>
      </EditWrap>
    </li>
  )
}

function ThingRow({ item }: { item: Possession }) {
  const [open, setOpen] = useState(false)

  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    await db.possessions.update(item.id, {
      name: String(fd.get('name') ?? '').trim() || item.name,
      category: String(fd.get('category') ?? item.category) as PossessionCategory,
      estimatedValue: Number(fd.get('estimatedValue') || 0),
      acquiredAt: String(fd.get('acquiredAt') ?? ''),
      note: String(fd.get('note') ?? '').trim(),
      updatedAt: Date.now(),
    })
    setOpen(false)
  }

  return (
    <li>
      <LedgerHead
        name={item.name}
        meta={`${POSSESSION_LABELS[item.category]}${item.acquiredAt ? ` · ${item.acquiredAt}` : ''}${
          item.note ? ` · ${item.note}` : ''
        }`}
        amount={formatMoney(item.estimatedValue)}
        open={open}
        onToggle={() => setOpen((v) => !v)}
        onDelete={() => void db.possessions.delete(item.id)}
      />
      <EditWrap open={open} onSubmit={save}>
        <Field label="名称">
          <input name="name" defaultValue={item.name} />
        </Field>
        <Field label="类别">
          <select name="category" defaultValue={item.category}>
            {thingCats.map((key) => (
              <option key={key} value={key}>
                {POSSESSION_LABELS[key]}
              </option>
            ))}
          </select>
        </Field>
        <Field label="估值">
          <input
            name="estimatedValue"
            type="number"
            min="0"
            step="0.01"
            defaultValue={item.estimatedValue}
          />
        </Field>
        <Field label="入手日期">
          <DateSelect name="acquiredAt" defaultValue={item.acquiredAt} />
        </Field>
        <Field label="备注" className="span-2">
          <input name="note" defaultValue={item.note} />
        </Field>
      </EditWrap>
    </li>
  )
}

function SkillRow({ item }: { item: SkillAsset }) {
  const [open, setOpen] = useState(false)

  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    await db.skillAssets.update(item.id, {
      name: String(fd.get('name') ?? '').trim() || item.name,
      category: String(fd.get('category') ?? item.category) as SkillCategory,
      level: String(fd.get('level') ?? item.level) as SkillLevel,
      years: Number(fd.get('years') || 0),
      proof: String(fd.get('proof') ?? '').trim(),
      note: String(fd.get('note') ?? '').trim(),
      updatedAt: Date.now(),
    })
    setOpen(false)
  }

  const meta = [
    SKILL_LABELS[item.category],
    LEVEL_LABELS[item.level],
    item.years ? `${item.years} 年` : null,
    item.proof,
    item.note,
  ]
    .filter(Boolean)
    .join(' · ')

  return (
    <li>
      <LedgerHead
        name={item.name}
        meta={meta}
        amount={LEVEL_LABELS[item.level]}
        open={open}
        onToggle={() => setOpen((v) => !v)}
        onDelete={() => void db.skillAssets.delete(item.id)}
      />
      <EditWrap open={open} onSubmit={save}>
        <Field label="技能">
          <input name="name" defaultValue={item.name} />
        </Field>
        <Field label="门类">
          <select name="category" defaultValue={item.category}>
            {skillCats.map((key) => (
              <option key={key} value={key}>
                {SKILL_LABELS[key]}
              </option>
            ))}
          </select>
        </Field>
        <Field label="程度">
          <select name="level" defaultValue={item.level}>
            {skillLevels.map((key) => (
              <option key={key} value={key}>
                {LEVEL_LABELS[key]}
              </option>
            ))}
          </select>
        </Field>
        <Field label="年数">
          <input name="years" type="number" min="0" step="0.5" defaultValue={item.years} />
        </Field>
        <Field label="凭据" className="span-2">
          <input name="proof" defaultValue={item.proof} />
        </Field>
        <Field label="备注" className="span-3">
          <input name="note" defaultValue={item.note} />
        </Field>
      </EditWrap>
    </li>
  )
}

function WorkRow({ item }: { item: WorkRecord }) {
  const [open, setOpen] = useState(false)

  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    await db.workRecords.update(item.id, {
      title: String(fd.get('title') ?? '').trim() || item.title,
      kind: String(fd.get('kind') ?? item.kind) as WorkKind,
      org: String(fd.get('org') ?? '').trim(),
      role: String(fd.get('role') ?? '').trim(),
      startedAt: String(fd.get('startedAt') ?? ''),
      endedAt: String(fd.get('endedAt') ?? ''),
      summary: String(fd.get('summary') ?? '').trim(),
      updatedAt: Date.now(),
    })
    setOpen(false)
  }

  const meta = [WORK_LABELS[item.kind], item.org, item.role, formatPeriod(item.startedAt, item.endedAt)]
    .filter(Boolean)
    .join(' · ')

  return (
    <li>
      <LedgerHead
        name={item.title}
        meta={item.summary ? `${meta} · ${item.summary}` : meta}
        amount={formatPeriod(item.startedAt, item.endedAt) || WORK_LABELS[item.kind]}
        open={open}
        onToggle={() => setOpen((v) => !v)}
        onDelete={() => void db.workRecords.delete(item.id)}
      />
      <EditWrap open={open} onSubmit={save}>
        <Field label="名称">
          <input name="title" defaultValue={item.title} />
        </Field>
        <Field label="类型">
          <select name="kind" defaultValue={item.kind}>
            {workKinds.map((key) => (
              <option key={key} value={key}>
                {WORK_LABELS[key]}
              </option>
            ))}
          </select>
        </Field>
        <Field label="角色">
          <input name="role" defaultValue={item.role} />
        </Field>
        <Field label="组织">
          <input name="org" defaultValue={item.org} />
        </Field>
        <Field label="开始">
          <DateSelect name="startedAt" defaultValue={item.startedAt} />
        </Field>
        <Field label="结束">
          <DateSelect name="endedAt" defaultValue={item.endedAt} />
        </Field>
        <Field label="做了什么" className="span-3">
          <textarea name="summary" defaultValue={item.summary} />
        </Field>
      </EditWrap>
    </li>
  )
}

function LedgerHead({
  name,
  meta,
  amount,
  open,
  onToggle,
  onDelete,
}: {
  name: string
  meta: string
  amount: string
  open: boolean
  onToggle: () => void
  onDelete: () => void
}) {
  return (
    <div className="ledger-row">
      <div>
        <div className="ledger-name">{name}</div>
        <div className="ledger-meta">{meta}</div>
      </div>
      <div className="ledger-amount">{amount}</div>
      <div className="ledger-actions">
        <button type="button" onClick={onToggle}>
          {open ? '收起' : '改'}
        </button>
        <button type="button" onClick={onDelete}>
          除去
        </button>
      </div>
    </div>
  )
}

function EditWrap({
  open,
  onSubmit,
  children,
}: {
  open: boolean
  onSubmit: (e: FormEvent<HTMLFormElement>) => void | Promise<void>
  children: ReactNode
}) {
  return (
    <AnimatePresence>
      {open ? (
        <motion.form
          className="compose cols-3 edit-panel"
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          onSubmit={(e) => void onSubmit(e)}
        >
          {children}
          <button className="btn" type="submit">
            存
          </button>
        </motion.form>
      ) : null}
    </AnimatePresence>
  )
}
