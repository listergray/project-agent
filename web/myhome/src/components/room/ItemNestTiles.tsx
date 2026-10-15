import { useMemo, useState, type FormEvent } from 'react'
import { Field, readForm } from '../Field'
import { db, type RoomItem } from '../../db'
import { ITEM_CATEGORIES, formatItemDims, readDimCm, type ItemCategory } from '../../lib/homeLayout'
import {
  flattenSubtree,
  indexItems,
  itemPath,
  type FlatItem,
} from '../../lib/itemTree'
import { guessPropKey, PROP_KEYS, PROP_LABELS, type PropKey } from '../../lib/roomScene'
import { nid } from '../../lib/dates'
import { PropMark } from './DshMarks'

type Props = {
  roomId: string
  items: RoomItem[]
  anchorId: string
  anchorName: string
  selectedId: string | null
  onSelect: (id: string | null) => void
}

export function ItemNestTiles({ roomId, items, anchorId, anchorName, selectedId, onSelect }: Props) {
  const [focusId, setFocusId] = useState(anchorId)
  const [flatAll, setFlatAll] = useState(false)

  const index = useMemo(() => indexItems(items), [items])
  const focus = index.byId.get(focusId) ?? index.byId.get(anchorId)
  const focusName = focus?.name ?? anchorName
  const breadcrumb = useMemo(() => itemPath(index, focusId), [index, focusId])
  const directChildren = index.childrenOf.get(focusId) ?? []
  const flatRows = useMemo(() => flattenSubtree(index, anchorId), [index, anchorId])

  async function addChild(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    const name = String(fd.get('name') ?? '').trim()
    if (!name) return
    const propKey = String(fd.get('propKey') ?? guessPropKey(name)) as PropKey
    await db.roomItems.add({
      id: nid(),
      roomId,
      parentId: focusId,
      propKey,
      name,
      category: String(fd.get('category') ?? '其他') as ItemCategory,
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

  function renderTile(item: RoomItem, meta?: string) {
    const key = (item.propKey || guessPropKey(item.name)) as PropKey
    const childCount = (index.childrenOf.get(item.id) ?? []).length
    const active = selectedId === item.id
    const dims = formatItemDims(item)
    const line = [meta, dims].filter(Boolean).join(' · ')
    return (
      <button
        key={item.id}
        type="button"
        className={active ? 'nest-tile dsh-nest on' : 'nest-tile dsh-nest'}
        onClick={() => onSelect(active ? null : item.id)}
        onDoubleClick={() => {
          setFlatAll(false)
          setFocusId(item.id)
        }}
      >
        <PropMark kind={key} />
        <span className="nest-tile-name">{item.name}</span>
        {line ? <span className="nest-tile-meta">{line}</span> : null}
        {childCount > 0 ? <span className="nest-tile-count">{childCount}</span> : null}
      </button>
    )
  }

  return (
    <div className="nest-pane">
      <div className="nest-toolbar">
        <nav className="nest-crumb" aria-label="嵌套路径">
          {breadcrumb.map((node, i) => (
            <span key={node.id}>
              {i > 0 ? <span className="nest-crumb-sep">›</span> : null}
              <button
                type="button"
                className={node.id === focusId ? 'on' : undefined}
                onClick={() => {
                  setFlatAll(false)
                  setFocusId(node.id)
                }}
              >
                {node.name}
              </button>
            </span>
          ))}
        </nav>
        <div className="nest-actions">
          <button
            type="button"
            className={flatAll ? 'btn inline on' : 'btn inline'}
            onClick={() => setFlatAll((value) => !value)}
          >
            {flatAll ? '按层查看' : '全部平铺'}
          </button>
          {focusId !== anchorId ? (
            <button
              type="button"
              className="btn inline"
              onClick={() => {
                setFlatAll(false)
                setFocusId(anchorId)
              }}
            >
              回到{anchorName}
            </button>
          ) : null}
        </div>
      </div>

      {flatAll ? (
        flatRows.length === 0 ? (
          <p className="empty">下面还没有东西。</p>
        ) : (
          <div className="nest-grid">
            {flatRows.map((row: FlatItem) =>
              renderTile(row.item, row.path.slice(1).join(' › ')),
            )}
          </div>
        )
      ) : directChildren.length === 0 ? (
        <p className="empty">「{focusName}」里还没有东西。任意物件下都能继续放。</p>
      ) : (
        <div className="nest-grid">
          {directChildren.map((child) => renderTile(child))}
        </div>
      )}

      <p className="section-lead nest-hint">双击格子可进入下一层；「全部平铺」展开所有下级。</p>

      <form className="compose cols-3" onSubmit={(e) => void addChild(e)}>
        <Field label={`放进「${focusName}」`} className="span-3">
          <input name="name" required placeholder="如：靠垫、书、盒里的笔" />
        </Field>
        <Field label="图标">
          <select name="propKey" defaultValue="generic">
            {PROP_KEYS.map((key) => (
              <option key={key} value={key}>
                {PROP_LABELS[key]}
              </option>
            ))}
          </select>
        </Field>
        <Field label="类别">
          <select name="category" defaultValue="其他">
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
        <button className="btn span-3" type="submit">
          放一件
        </button>
      </form>
    </div>
  )
}
