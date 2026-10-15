import { useLiveQuery } from 'dexie-react-hooks'
import { motion } from 'motion/react'
import { useMemo, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Field, readForm } from '../Field'
import { db, type RoomItem } from '../../db'
import { ITEM_CATEGORIES, formatItemDims, readDimCm, type ItemCategory } from '../../lib/homeLayout'
import { isMaintainDue, linkMaintainFromItem } from '../../lib/maintain'
import {
  deleteRoomItemTree,
  descendantsCount,
  indexItems,
} from '../../lib/itemTree'
import {
  PROP_KEYS,
  PROP_LABELS,
  guessPropKey,
  type PropKey,
} from '../../lib/roomScene'
import { nid, todayKey } from '../../lib/dates'
import { ItemNestTiles } from './ItemNestTiles'
import { PropMark } from './DshMarks'

type Props = {
  roomId: string
  roomKind: string
  items: RoomItem[]
}

export function RoomScene({ roomId, roomKind, items }: Props) {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const maintains = useLiveQuery(() => db.maintains.toArray()) ?? []
  const maintainByItem = useMemo(
    () => new Map(maintains.filter((plan) => plan.roomItemId).map((plan) => [plan.roomItemId, plan])),
    [maintains],
  )
  const index = useMemo(() => indexItems(items), [items])

  const roots = index.childrenOf.get('') ?? []
  const selected = selectedId ? (index.byId.get(selectedId) ?? null) : null
  const parent = selected?.parentId ? index.byId.get(selected.parentId) : null
  const selectedPlan = selected ? maintainByItem.get(selected.id) : null
  const today = todayKey()

  async function addRoot(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    const name = String(fd.get('name') ?? '').trim()
    if (!name) return
    const propKey = String(fd.get('propKey') ?? guessPropKey(name)) as PropKey
    await db.roomItems.add({
      id: nid(),
      roomId,
      parentId: '',
      propKey,
      name,
      category: String(fd.get('category') ?? '家具') as ItemCategory,
      lengthCm: readDimCm(fd.get('lengthCm')),
      widthCm: readDimCm(fd.get('widthCm')),
      heightCm: readDimCm(fd.get('heightCm')),
      planXM: -1,
      planYM: 0,
      planWM: 0,
      planDM: 0,
      note: String(fd.get('note') ?? '').trim(),
      updatedAt: Date.now(),
    })
    e.currentTarget.reset()
  }

  async function saveSelected(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!selected) return
    const fd = readForm(e)
    const name = String(fd.get('name') ?? '').trim()
    await db.roomItems.update(selected.id, {
      name: name || selected.name,
      category: String(fd.get('category') ?? selected.category),
      propKey: String(fd.get('propKey') ?? selected.propKey),
      lengthCm: readDimCm(fd.get('lengthCm')),
      widthCm: readDimCm(fd.get('widthCm')),
      heightCm: readDimCm(fd.get('heightCm')),
      note: String(fd.get('note') ?? '').trim(),
      updatedAt: Date.now(),
    })
  }

  return (
    <div className="studio-wrap dsh-studio" data-kind={roomKind}>
      <div className="dsh-grid item-grid">
        {roots.map((item, i) => {
          const key = (item.propKey || guessPropKey(item.name)) as PropKey
          const active = selectedId === item.id
          const nest = descendantsCount(index, item.id)
          const plan = maintainByItem.get(item.id)
          const maintainDue = plan ? isMaintainDue(plan, today) : false
          const dims = formatItemDims(item)
          return (
            <motion.button
              key={item.id}
              type="button"
              className={[
                'dsh-card',
                'item-card',
                active ? 'on' : '',
                maintainDue ? 'due' : '',
              ]
                .filter(Boolean)
                .join(' ')}
              onClick={() => setSelectedId(active ? null : item.id)}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03, duration: 0.3 }}
            >
              <div className="dsh-card-top">
                <span className="dsh-kicker">{item.category || PROP_LABELS[key]}</span>
                <PropMark kind={key} />
              </div>
              <p className="dsh-meta">
                {nest > 0 ? `内含 ${nest}` : '可继续往下放'}
                {dims ? ` · ${dims}` : ''}
                {maintainDue ? ' · 待维护' : ''}
              </p>
              <h3 className="dsh-card-title">{item.name}</h3>
              <p className="dsh-card-desc">{item.note || PROP_LABELS[key]}</p>
              <span className="dsh-card-link">{active ? '已选中' : '查看 →'}</span>
            </motion.button>
          )
        })}
      </div>

      {roots.length === 0 ? <p className="empty dsh-empty">此间还没有物件。</p> : null}

      {selected ? (
        <div className="dsh-panel">
          <p className="dsh-kicker">{parent ? `在 ${parent.name} 里` : '物件'}</p>
          <h3 className="dsh-panel-title">{selected.name}</h3>
          <form className="compose cols-3" onSubmit={(e) => void saveSelected(e)} key={selected.id}>
            <Field label="名称" className="span-2">
              <input name="name" defaultValue={selected.name} />
            </Field>
            <Field label="图标">
              <select name="propKey" defaultValue={selected.propKey || guessPropKey(selected.name)}>
                {PROP_KEYS.map((key) => (
                  <option key={key} value={key}>
                    {PROP_LABELS[key]}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="类别">
              <select name="category" defaultValue={selected.category}>
                {ITEM_CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="长 cm">
              <input
                name="lengthCm"
                type="number"
                min="0"
                step="0.1"
                inputMode="decimal"
                placeholder="可选"
                defaultValue={selected.lengthCm || ''}
              />
            </Field>
            <Field label="宽 cm">
              <input
                name="widthCm"
                type="number"
                min="0"
                step="0.1"
                inputMode="decimal"
                placeholder="可选"
                defaultValue={selected.widthCm || ''}
              />
            </Field>
            <Field label="高 cm">
              <input
                name="heightCm"
                type="number"
                min="0"
                step="0.1"
                inputMode="decimal"
                placeholder="可选"
                defaultValue={selected.heightCm || ''}
              />
            </Field>
            <Field label="备注" className="span-3">
              <input name="note" defaultValue={selected.note} />
            </Field>
            <button className="btn" type="submit">
              存
            </button>
            <button
              className="btn danger"
              type="button"
              onClick={() => {
                void (async () => {
                  await deleteRoomItemTree(roomId, selected.id)
                  setSelectedId(null)
                })()
              }}
            >
              除去
            </button>
          </form>

          <div className="pixel-maintain-head">
            {selectedPlan ? (
              <p className="section-lead">
                已定期待办：{selectedPlan.title}（每 {selectedPlan.everyDays} 天）
                <Link to="/todos"> 去待办 </Link>
              </p>
            ) : (
              <p className="section-lead">
                定期维护在「待办」章单独管理。
                <button
                  type="button"
                  className="btn inline"
                  onClick={() => {
                    void linkMaintainFromItem({
                      id: selected.id,
                      roomId,
                      name: selected.name,
                      propKey: selected.propKey || guessPropKey(selected.name),
                    })
                  }}
                >
                  加入待办
                </button>
              </p>
            )}
          </div>

          <ItemNestTiles
            key={selected.id}
            roomId={roomId}
            items={items}
            anchorId={selected.id}
            anchorName={selected.name}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
        </div>
      ) : (
        <p className="section-lead">点一张卡片查看；里面还能无限往下放，支持全部平铺。</p>
      )}

      <form className="compose cols-3 pixel-add" onSubmit={(e) => void addRoot(e)}>
        <Field label="添物件" className="span-2">
          <input name="name" required placeholder="如：沙发、电视、冰箱" />
        </Field>
        <Field label="图标">
          <select name="propKey" defaultValue="sofa">
            {PROP_KEYS.map((key) => (
              <option key={key} value={key}>
                {PROP_LABELS[key]}
              </option>
            ))}
          </select>
        </Field>
        <Field label="类别">
          <select name="category" defaultValue="家具">
            {ITEM_CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </Field>
        <Field label="长 cm">
          <input name="lengthCm" type="number" min="0" step="0.1" inputMode="decimal" placeholder="可选" />
        </Field>
        <Field label="宽 cm">
          <input name="widthCm" type="number" min="0" step="0.1" inputMode="decimal" placeholder="可选" />
        </Field>
        <Field label="高 cm">
          <input name="heightCm" type="number" min="0" step="0.1" inputMode="decimal" placeholder="可选" />
        </Field>
        <Field label="备注" className="span-3">
          <input name="note" placeholder="可选" />
        </Field>
        <button className="btn span-3" type="submit">
          摆进房间
        </button>
      </form>
    </div>
  )
}
