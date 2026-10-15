import { buildLedgerDump, importLedger, type LedgerDump } from '../db'

const API = '/api'

let lastPushed = ''
let syncing = false
let loopStarted = false
let timer: number | null = null

function dumpFingerprint(dump: LedgerDump): string {
  const { exportedAt: _ignored, ...rest } = dump
  return JSON.stringify(rest)
}

export type SyncStatus = {
  ok: boolean
  message: string
}

export async function checkRemoteHealth(): Promise<SyncStatus> {
  try {
    const res = await fetch(`${API}/health`, { cache: 'no-store' })
    if (!res.ok) return { ok: false, message: `接口 ${res.status}` }
    const data = (await res.json()) as { ok?: boolean; error?: string }
    if (!data.ok) return { ok: false, message: data.error || 'MySQL 未就绪' }
    return { ok: true, message: '已连上账本库' }
  } catch (err) {
    return { ok: false, message: String((err as Error)?.message || err) }
  }
}

/** Pull MySQL ledger into local Dexie. Returns true if remote had data. */
export async function pullLedgerFromRemote(): Promise<boolean> {
  const res = await fetch(`${API}/ledger`, { cache: 'no-store' })
  if (res.status === 404) return false
  if (!res.ok) throw new Error(`拉取账本失败 ${res.status}`)
  const data = (await res.json()) as { empty?: boolean; ledger?: LedgerDump }
  if (data.empty || !data.ledger) return false
  await importLedger(data.ledger)
  lastPushed = dumpFingerprint(data.ledger)
  return true
}

/** Push current Dexie ledger to MySQL if changed. */
export async function pushLedgerToRemote(force = false): Promise<boolean> {
  if (syncing) return false
  syncing = true
  try {
    const dump = await buildLedgerDump()
    const fp = dumpFingerprint(dump)
    if (!force && fp === lastPushed) return false
    const res = await fetch(`${API}/ledger`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dump),
    })
    if (!res.ok) {
      const text = await res.text()
      throw new Error(`写入账本失败 ${res.status}: ${text}`)
    }
    lastPushed = fp
    return true
  } finally {
    syncing = false
  }
}

/** Start periodic push loop (idempotent). */
export function startRemotePushLoop() {
  if (loopStarted) return
  loopStarted = true
  const tick = () => {
    void pushLedgerToRemote().catch((err) => console.warn('[sync] push', err))
  }
  timer = window.setInterval(tick, 8_000)
  window.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') tick()
  })
  window.addEventListener('beforeunload', () => {
    void pushLedgerToRemote()
  })
}

/**
 * Full boot: health → pull if any → caller runs local ensures → push + loop.
 */
export async function bootRemoteSync(): Promise<SyncStatus> {
  const health = await checkRemoteHealth()
  if (!health.ok) {
    console.warn('[sync]', health.message)
    window.setTimeout(() => {
      void bootRemoteSync().then((s) => {
        if (s.ok) console.info('[sync]', s.message)
      })
    }, 12_000)
    return health
  }

  try {
    await pullLedgerFromRemote()
  } catch (err) {
    const message = String((err as Error)?.message || err)
    console.warn('[sync] pull failed', message)
    return { ok: false, message }
  }

  startRemotePushLoop()
  return { ok: true, message: '账本已与 MySQL 同步' }
}

export function stopRemoteSync() {
  if (timer != null) window.clearInterval(timer)
  timer = null
  loopStarted = false
}
