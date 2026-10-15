import { useLiveQuery } from 'dexie-react-hooks'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Chapter } from '../components/Chapter'
import { Field, readForm } from '../components/Field'
import { db, RELATIONS, type Relation } from '../db'
import { daysUntilBirthday, nid, todayKey } from '../lib/dates'

export function People() {
  const navigate = useNavigate()
  const [q, setQ] = useState('')
  const people = useLiveQuery(() => db.people.toArray()) ?? []
  const query = q.trim()
  const rows = people
    .filter((p) => {
      if (!query) return true
      return `${p.name}${p.city}${p.relation}${p.impression}`.includes(query)
    })
    .sort((a, b) => {
      const av = a.lastContactAt || '0000'
      const bv = b.lastContactAt || '0000'
      return av.localeCompare(bv)
    })

  async function addPerson(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    const name = String(fd.get('name') ?? '').trim()
    if (!name) return
    const id = nid()
    await db.people.add({
      id,
      name,
      relation: String(fd.get('relation') ?? '朋友') as Relation,
      howWeMet: '',
      phone: '',
      city: '',
      birthday: '',
      lastContactAt: '',
      impression: '',
      createdAt: Date.now(),
    })
    e.currentTarget.reset()
    navigate(`/people/${id}`)
  }

  return (
    <Chapter index="伍" title="交际" hint="每个人都可以写下补充信息：忌口、近况、家人、该记得的事。">
      <form className="compose cols-2" onSubmit={(e) => void addPerson(e)}>
        <Field label="姓名">
          <input name="name" required placeholder="写下一个人" />
        </Field>
        <Field label="关系">
          <select name="relation" defaultValue="朋友">
            {RELATIONS.map((rel) => (
              <option key={rel} value={rel}>
                {rel}
              </option>
            ))}
          </select>
        </Field>
        <button className="btn span-2" type="submit">
          立档
        </button>
      </form>

      <div className="section">
        <Field label="寻人" className="search">
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="姓名、城市、关系" />
        </Field>
      </div>

      {rows.length === 0 ? (
        <p className="empty">{people.length === 0 ? '还没有写下任何人。' : '没有找到此人。'}</p>
      ) : (
        <ul className="people-list">
          {rows.map((person) => {
            const until = daysUntilBirthday(person.birthday)
            const soon = until != null && until <= 30
            return (
              <li key={person.id}>
                <Link to={`/people/${person.id}`}>
                  <span className="people-name">{person.name}</span>
                  <span className="people-rel">{person.relation}</span>
                  <span className="people-extra">
                    {person.lastContactAt
                      ? `上次联络 ${person.lastContactAt === todayKey() ? '今日' : person.lastContactAt}`
                      : '尚未记下联络'}
                    {soon
                      ? ` · ${until === 0 ? '今日生日' : `${until} 日后生日`}`
                      : ''}
                    {person.city ? ` · ${person.city}` : ''}
                  </span>
                </Link>
              </li>
            )
          })}
        </ul>
      )}
    </Chapter>
  )
}
