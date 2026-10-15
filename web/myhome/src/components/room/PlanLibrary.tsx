import { useLiveQuery } from 'dexie-react-hooks'
import { useState, type DragEvent, type FormEvent } from 'react'
import { Field, readForm } from '../Field'
import {
  db,
  type PlanComponent,
  type PlanComponentFamily,
} from '../../db'
import {
  addPlanComponent,
  deletePlanComponent,
  familyLabel,
  PLAN_COMPONENT_MIME,
  typeKeyOptions,
} from '../../lib/planCatalog'

export function PlanLibrary() {
  const components =
    useLiveQuery(async () => {
      const rows = await db.planComponents.toArray()
      return rows.sort((a, b) => a.sortOrder - b.sortOrder || a.name.localeCompare(b.name, 'zh'))
    }) ?? []

  const [family, setFamily] = useState<PlanComponentFamily>('prop')
  const [editId, setEditId] = useState<string | null>(null)
  const editing = editId ? components.find((c) => c.id === editId) : null

  function onDragStart(event: DragEvent, item: PlanComponent) {
    event.dataTransfer.setData(PLAN_COMPONENT_MIME, item.id)
    event.dataTransfer.setData('text/plain', item.id)
    event.dataTransfer.effectAllowed = 'copy'
  }

  async function createCustom(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    const name = String(fd.get('name') ?? '').trim()
    if (!name) return
    const fam = String(fd.get('family') ?? family) as PlanComponentFamily
    await addPlanComponent({
      name,
      family: fam,
      typeKey: String(fd.get('typeKey') ?? '').trim() || (fam === 'fixture' ? 'window' : 'generic'),
      widthM: Number(fd.get('widthM')) || undefined,
      depthM: Number(fd.get('depthM')) || undefined,
      heightM: Number(fd.get('heightM')) || undefined,
      sillM: Number(fd.get('sillM')) || 0,
      category: String(fd.get('category') ?? '').trim(),
      color: String(fd.get('color') ?? '').trim(),
    })
    e.currentTarget.reset()
    setFamily(fam)
  }

  async function saveEdit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!editing) return
    const fd = readForm(e)
    await db.planComponents.update(editing.id, {
      name: String(fd.get('name') ?? '').trim() || editing.name,
      typeKey: String(fd.get('typeKey') ?? '').trim() || editing.typeKey,
      widthM: Number(fd.get('widthM')) || editing.widthM,
      depthM: Number(fd.get('depthM')) || editing.depthM,
      heightM: Number(fd.get('heightM')) || editing.heightM,
      sillM: Number(fd.get('sillM')) || 0,
      category: String(fd.get('category') ?? '').trim() || editing.category,
      color: String(fd.get('color') ?? '').trim() || editing.color,
      note: String(fd.get('note') ?? '').trim(),
      updatedAt: Date.now(),
    })
    setEditId(null)
  }

  async function remove(id: string, name: string) {
    if (!window.confirm(`从组件库除去「${name}」？已摆到平面上的实例不会删除。`)) return
    await deletePlanComponent(id)
    if (editId === id) setEditId(null)
  }

  const typeOpts = typeKeyOptions(editing?.family ?? family)

  return (
    <aside className="plan-library">
      <div className="plan-library-head">
        <h3>组件库</h3>
        <p className="section-lead">拖到房间上；可自定义窗户、书包等。</p>
      </div>

      <ul className="plan-library-list">
        {components.map((item) => (
          <li key={item.id}>
            <button
              type="button"
              className="plan-library-chip"
              draggable
              onDragStart={(e) => onDragStart(e, item)}
              onClick={() => setEditId(item.id === editId ? null : item.id)}
              title="拖到平面 · 点击编辑"
            >
              <span className="plan-library-swatch" style={{ background: item.color }} />
              <span className="plan-library-name">{item.name}</span>
              <span className="plan-library-meta">{familyLabel(item.family)}</span>
            </button>
          </li>
        ))}
      </ul>

      {editing ? (
        <form className="plan-library-form" onSubmit={(e) => void saveEdit(e)} key={editing.id}>
          <p className="dsh-kicker">改组件</p>
          <Field label="名称">
            <input name="name" defaultValue={editing.name} required />
          </Field>
          <Field label="类型键">
            <select name="typeKey" defaultValue={editing.typeKey}>
              {typeOpts.map((opt) => (
                <option key={opt.id} value={opt.id}>
                  {opt.label}
                </option>
              ))}
              {!typeOpts.some((o) => o.id === editing.typeKey) ? (
                <option value={editing.typeKey}>{editing.typeKey}</option>
              ) : null}
            </select>
          </Field>
          <Field label="宽 m">
            <input name="widthM" type="number" min="0.05" step="0.01" defaultValue={editing.widthM} />
          </Field>
          {editing.family === 'prop' ? (
            <Field label="深 m">
              <input name="depthM" type="number" min="0.05" step="0.01" defaultValue={editing.depthM} />
            </Field>
          ) : (
            <Field label="窗台高 m">
              <input name="sillM" type="number" min="0" step="0.01" defaultValue={editing.sillM} />
            </Field>
          )}
          <Field label="高 m">
            <input name="heightM" type="number" min="0" step="0.01" defaultValue={editing.heightM} />
          </Field>
          <Field label="分类">
            <input name="category" defaultValue={editing.category} />
          </Field>
          <Field label="标记色">
            <input name="color" type="color" defaultValue={editing.color || '#94a3b8'} />
          </Field>
          <Field label="备忘" className="span-2">
            <input name="note" defaultValue={editing.note} />
          </Field>
          <button className="btn" type="submit">
            存
          </button>
          <button className="btn danger" type="button" onClick={() => void remove(editing.id, editing.name)}>
            除去
          </button>
          <button className="btn" type="button" onClick={() => setEditId(null)}>
            收起
          </button>
        </form>
      ) : (
        <form className="plan-library-form" onSubmit={(e) => void createCustom(e)}>
          <p className="dsh-kicker">自定义</p>
          <Field label="名称">
            <input name="name" placeholder="如：窗户、书包" required />
          </Field>
          <Field label="族">
            <select
              name="family"
              value={family}
              onChange={(e) => setFamily(e.target.value as PlanComponentFamily)}
            >
              <option value="prop">物件</option>
              <option value="fixture">构件（门窗）</option>
            </select>
          </Field>
          <Field label="类型">
            <select key={family} name="typeKey" defaultValue={family === 'fixture' ? 'window' : 'generic'}>
              {typeKeyOptions(family).map((opt) => (
                <option key={opt.id} value={opt.id}>
                  {opt.label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="宽 m">
            <input name="widthM" type="number" min="0.05" step="0.01" placeholder="默认" />
          </Field>
          {family === 'prop' ? (
            <Field label="深 m">
              <input name="depthM" type="number" min="0.05" step="0.01" placeholder="默认" />
            </Field>
          ) : (
            <Field label="窗台高 m">
              <input name="sillM" type="number" min="0" step="0.01" defaultValue={0.9} />
            </Field>
          )}
          <Field label="高 m">
            <input name="heightM" type="number" min="0" step="0.01" placeholder="默认" />
          </Field>
          <Field label="分类">
            <input name="category" placeholder="家具 / 随身…" />
          </Field>
          <Field label="标记色">
            <input name="color" type="color" defaultValue="#94a3b8" />
          </Field>
          <button className="btn" type="submit">
            记入库
          </button>
        </form>
      )}
    </aside>
  )
}
