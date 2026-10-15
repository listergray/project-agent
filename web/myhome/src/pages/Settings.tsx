import { useLiveQuery } from 'dexie-react-hooks'
import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Chapter } from '../components/Chapter'
import { DateSelect } from '../components/DateSelect'
import { Field, readForm } from '../components/Field'
import { clearLedger, db, exportLedger, importLedger, type LedgerDump } from '../db'
import {
  checkRemoteHealth,
  pushLedgerToRemote,
  type SyncStatus,
} from '../lib/remoteSync'

export function Settings() {
  const settings = useLiveQuery(() => db.settings.get('main'))
  const fileRef = useRef<HTMLInputElement>(null)
  const [sync, setSync] = useState<SyncStatus | null>(null)
  const [pushing, setPushing] = useState(false)

  useEffect(() => {
    void checkRemoteHealth().then(setSync)
  }, [])

  if (!settings) {
    return (
      <Chapter title="册上" hint="生辰用来计算剩余的日子。账本同步到 MySQL，也可本机备份。">
        <p className="empty">读取中。</p>
      </Chapter>
    )
  }

  const row = settings

  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = readForm(e)
    const expectedYears = Number(fd.get('expectedYears') || 80)
    await db.settings.put({
      id: 'main',
      displayName: String(fd.get('displayName') ?? '').trim(),
      birthDate: String(fd.get('birthDate') ?? ''),
      expectedYears: expectedYears > 0 ? expectedYears : 80,
      pathKey: row.pathKey ?? '',
      pathTitle: row.pathTitle ?? '',
      pathLine: row.pathLine ?? '',
    })
    void pushLedgerToRemote()
  }

  async function onImport(file: File) {
    const text = await file.text()
    const data = JSON.parse(text) as LedgerDump
    await importLedger(data)
    try {
      await pushLedgerToRemote(true)
      window.alert('已读入备份，并写入 MySQL。')
    } catch {
      window.alert('已读入本机；写入 MySQL 失败，请检查服务。')
    }
  }

  async function onClear() {
    if (!window.confirm('此举将抹去本机全部记录。MySQL 中的账本不会自动删除。')) return
    await clearLedger()
  }

  async function onPushNow() {
    setPushing(true)
    try {
      await pushLedgerToRemote(true)
      setSync(await checkRemoteHealth())
      window.alert('已写入 MySQL。')
    } catch (err) {
      window.alert(`写入失败：${String((err as Error)?.message || err)}`)
    } finally {
      setPushing(false)
    }
  }

  return (
    <Chapter title="册上" hint="生辰用来计算剩余的日子。账本同步到 MySQL，也可本机备份。">
      <form
        className="compose cols-2"
        onSubmit={(e) => void save(e)}
        key={`${row.displayName}|${row.birthDate}|${row.expectedYears}`}
      >
        <Field label="如何称呼">
          <input name="displayName" defaultValue={row.displayName} placeholder="可选" />
        </Field>
        <Field label="生辰">
          <DateSelect name="birthDate" defaultValue={row.birthDate} max={new Date().toISOString().slice(0, 10)} />
        </Field>
        <Field label="所记寿数（年）">
          <input
            name="expectedYears"
            type="number"
            min="1"
            max="130"
            defaultValue={row.expectedYears}
          />
        </Field>
        <button className="btn span-2" type="submit">
          写入
        </button>
      </form>

      {row.pathTitle ? (
        <section className="section">
          <h2>当前路线</h2>
          <p className="section-lead">
            {row.pathTitle} · {row.pathLine}
          </p>
        </section>
      ) : null}

      <section className="section">
        <h2>MySQL 持久化</h2>
        <p className="section-lead">
          {sync
            ? sync.ok
              ? sync.message
              : `未连通：${sync.message}`
            : '检测中…'}
          。完整账本（资产、今日、小屋等）定时写入 192.168.1.46。
        </p>
        <div className="compose">
          <button className="btn" type="button" disabled={pushing} onClick={() => void onPushNow()}>
            {pushing ? '写入中…' : '立刻同步到库'}
          </button>
          <button
            className="btn"
            type="button"
            onClick={() => void checkRemoteHealth().then(setSync)}
          >
            再测连通
          </button>
        </div>
      </section>

      <section className="section">
        <h2>备份</h2>
        <p className="section-lead">导出一份 JSON，换电脑时再读入；读入后会尝试写入 MySQL。</p>
        <div className="compose">
          <button className="btn" type="button" onClick={() => void exportLedger()}>
            导出账本
          </button>
          <button className="btn" type="button" onClick={() => fileRef.current?.click()}>
            读入备份
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="application/json"
            hidden
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) void onImport(file)
              e.target.value = ''
            }}
          />
        </div>
      </section>

      <section className="section">
        <h2>抹去</h2>
        <p className="section-lead">只清除这台设备上的 IndexedDB；库中记录需另行处理。</p>
        <button className="btn danger" type="button" onClick={() => void onClear()}>
          清空本机账本
        </button>
      </section>
    </Chapter>
  )
}
