import { useLiveQuery } from 'dexie-react-hooks'
import { type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Chapter } from '../components/Chapter'
import { DateSelect } from '../components/DateSelect'
import { Field, readForm } from '../components/Field'
import { db, FIELD_SUGGESTIONS, RELATIONS, type Relation } from '../db'
import { formatLedgerDate, nid, todayKey } from '../lib/dates'

export function PersonDetail() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const people = useLiveQuery(() => db.people.toArray())
  const person = people?.find((row) => row.id === id)
  const fields =
    useLiveQuery(() => (id ? db.personFields.where('personId').equals(id).toArray() : []), [id]) ??
    []
  const notes =
    useLiveQuery(async () => {
      if (!id) return []
      const rows = await db.personNotes.where('personId').equals(id).toArray()
      return rows.sort((a, b) => b.createdAt - a.createdAt)
    }, [id]) ?? []

  if (people === undefined) {
    return (
      <Chapter title="档案" hint="正在翻开。">
        <p className="empty">读取中。</p>
      </Chapter>
    )
  }

  if (!person) {
    return (
      <Chapter title="档案" hint="此人未在册上。">
        <Link className="back" to="/people">
          返回交际
        </Link>
      </Chapter>
    )
  }

  const row = person

  async function saveCore(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    await db.people.update(row.id, {
      name: String(fd.get('name') ?? '').trim() || row.name,
      relation: String(fd.get('relation') ?? row.relation) as Relation,
      howWeMet: String(fd.get('howWeMet') ?? '').trim(),
      phone: String(fd.get('phone') ?? '').trim(),
      city: String(fd.get('city') ?? '').trim(),
      birthday: String(fd.get('birthday') ?? ''),
      lastContactAt: String(fd.get('lastContactAt') ?? ''),
      impression: String(fd.get('impression') ?? '').trim(),
    })
  }

  async function addField(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    const label = String(fd.get('label') ?? '').trim()
    const value = String(fd.get('value') ?? '').trim()
    if (!label || !value) return
    await db.personFields.add({ id: nid(), personId: row.id, label, value })
    e.currentTarget.reset()
  }

  async function addNote(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    const content = String(fd.get('content') ?? '').trim()
    if (!content) return
    await db.personNotes.add({
      id: nid(),
      personId: row.id,
      content,
      createdAt: Date.now(),
    })
    await db.people.update(row.id, { lastContactAt: todayKey() })
    e.currentTarget.reset()
  }

  async function removePerson() {
    if (!window.confirm(`除去「${row.name}」的全部档案？`)) return
    await db.transaction('rw', [db.people, db.personFields, db.personNotes], async () => {
      await db.personFields.where('personId').equals(row.id).delete()
      await db.personNotes.where('personId').equals(row.id).delete()
      await db.people.delete(row.id)
    })
    navigate('/people')
  }

  return (
    <Chapter title={person.name} hint="补充信息可以是忌口、家人、近况，或任何你不想忘掉的事。">
      <Link className="back" to="/people">
        返回交际
      </Link>

      <section className="section">
        <h2>其人</h2>
        <form className="compose cols-2" onSubmit={(e) => void saveCore(e)}>
          <Field label="姓名">
            <input name="name" defaultValue={person.name} />
          </Field>
          <Field label="关系">
            <select name="relation" defaultValue={person.relation}>
              {RELATIONS.map((rel) => (
                <option key={rel} value={rel}>
                  {rel}
                </option>
              ))}
            </select>
          </Field>
          <Field label="电话">
            <input name="phone" defaultValue={person.phone} />
          </Field>
          <Field label="城市">
            <input name="city" defaultValue={person.city} />
          </Field>
          <Field label="生日">
            <DateSelect name="birthday" defaultValue={person.birthday} />
          </Field>
          <Field label="上次联络">
            <DateSelect
              name="lastContactAt"
              defaultValue={person.lastContactAt}
              key={person.lastContactAt || 'none'}
            />
          </Field>
          <Field label="如何相识" className="span-2">
            <textarea name="howWeMet" defaultValue={person.howWeMet} />
          </Field>
          <Field label="印象" className="span-2">
            <textarea name="impression" defaultValue={person.impression} />
          </Field>
          <button className="btn span-2" type="submit">
            存档
          </button>
        </form>
      </section>

      <section className="section">
        <h2>补充</h2>
        <p className="section-lead">给一条信息起个名字，再写下内容。例如「忌口 / 香菜」。</p>
        <form className="compose cols-2" onSubmit={(e) => void addField(e)}>
          <Field label="条目">
            <input name="label" list="field-labels" placeholder="如：忌口" required />
            <datalist id="field-labels">
              {FIELD_SUGGESTIONS.map((item) => (
                <option key={item} value={item} />
              ))}
            </datalist>
          </Field>
          <Field label="内容">
            <input name="value" required placeholder="如：不吃香菜" />
          </Field>
          <button className="btn span-2" type="submit">
            补记
          </button>
        </form>
        {fields.length === 0 ? (
          <p className="empty">还没有补充信息。</p>
        ) : (
          <ul className="ledger">
            {fields.map((field) => (
              <li key={field.id} className="kv">
                <span className="kv-label">{field.label}</span>
                <span>{field.value}</span>
                <div className="ledger-actions">
                  <button type="button" onClick={() => void db.personFields.delete(field.id)}>
                    除去
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="section">
        <h2>往来</h2>
        <p className="section-lead">记下一次见面、一通电话，或一句后来才懂的话。</p>
        <form className="compose" onSubmit={(e) => void addNote(e)}>
          <Field label="一笔往来">
            <textarea name="content" required placeholder="今天聊了什么，下次该问什么" />
          </Field>
          <button className="btn" type="submit">
            记下并记为今日已联络
          </button>
        </form>
        {notes.length === 0 ? (
          <p className="empty">尚无往来记录。</p>
        ) : (
          <ul className="ledger">
            {notes.map((note) => (
              <li key={note.id} style={{ padding: '1rem 0' }}>
                <p className="note-time">{formatLedgerDate(new Date(note.createdAt))}</p>
                <p>{note.content}</p>
                <div className="ledger-actions" style={{ marginTop: '0.5rem' }}>
                  <button type="button" onClick={() => void db.personNotes.delete(note.id)}>
                    除去
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="section">
        <button className="btn danger" type="button" onClick={() => void removePerson()}>
          除去此人
        </button>
      </section>
    </Chapter>
  )
}
