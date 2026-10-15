import cors from 'cors'
import dotenv from 'dotenv'
import express from 'express'
import mysql from 'mysql2/promise'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
dotenv.config({ path: path.join(__dirname, '.env') })

const MYSQL_HOST = process.env.MYSQL_HOST || '127.0.0.1'
const MYSQL_PORT = Number(process.env.MYSQL_PORT || 3306)
const MYSQL_USER = process.env.MYSQL_USER || 'root'
const MYSQL_PASSWORD = process.env.MYSQL_PASSWORD || ''
const MYSQL_DATABASE = process.env.MYSQL_DATABASE || 'wodesuoyou'
const API_PORT = Number(process.env.API_PORT || 18002)

/** @type {import('mysql2/promise').Pool | null} */
let pool = null

async function ensureSchema() {
  const boot = await mysql.createConnection({
    host: MYSQL_HOST,
    port: MYSQL_PORT,
    user: MYSQL_USER,
    password: MYSQL_PASSWORD,
    multipleStatements: true,
  })
  await boot.query(
    `CREATE DATABASE IF NOT EXISTS \`${MYSQL_DATABASE}\` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci`,
  )
  await boot.end()

  pool = mysql.createPool({
    host: MYSQL_HOST,
    port: MYSQL_PORT,
    user: MYSQL_USER,
    password: MYSQL_PASSWORD,
    database: MYSQL_DATABASE,
    waitForConnections: true,
    connectionLimit: 5,
    charset: 'utf8mb4',
  })

  await pool.query(`
    CREATE TABLE IF NOT EXISTS ledger (
      id TINYINT UNSIGNED NOT NULL PRIMARY KEY DEFAULT 1,
      payload JSON NOT NULL,
      updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  `)
}

function getPool() {
  if (!pool) throw new Error('MySQL pool not ready')
  return pool
}

const app = express()
app.use(cors())
app.use(express.json({ limit: '32mb' }))

app.get('/api/health', async (_req, res) => {
  try {
    const [rows] = await getPool().query('SELECT 1 AS ok')
    res.json({ ok: true, mysql: rows[0]?.ok === 1, database: MYSQL_DATABASE })
  } catch (err) {
    res.status(503).json({ ok: false, error: String(err?.message || err) })
  }
})

app.get('/api/ledger', async (_req, res) => {
  try {
    const [rows] = await getPool().query(
      'SELECT payload, updated_at AS updatedAt FROM ledger WHERE id = 1 LIMIT 1',
    )
    if (!rows.length) {
      res.status(404).json({ empty: true })
      return
    }
    const row = rows[0]
    const payload =
      typeof row.payload === 'string' ? JSON.parse(row.payload) : row.payload
    res.json({
      empty: false,
      updatedAt: row.updatedAt,
      ledger: payload,
    })
  } catch (err) {
    res.status(500).json({ error: String(err?.message || err) })
  }
})

app.put('/api/ledger', async (req, res) => {
  try {
    const ledger = req.body
    if (!ledger || typeof ledger !== 'object') {
      res.status(400).json({ error: 'body must be ledger JSON object' })
      return
    }
    if (!ledger.exportedAt) ledger.exportedAt = new Date().toISOString()
    const json = JSON.stringify(ledger)
    await getPool().query(
      `INSERT INTO ledger (id, payload) VALUES (1, CAST(? AS JSON))
       ON DUPLICATE KEY UPDATE payload = CAST(? AS JSON)`,
      [json, json],
    )
    const [rows] = await getPool().query(
      'SELECT updated_at AS updatedAt FROM ledger WHERE id = 1 LIMIT 1',
    )
    res.json({ ok: true, updatedAt: rows[0]?.updatedAt ?? null })
  } catch (err) {
    res.status(500).json({ error: String(err?.message || err) })
  }
})

async function main() {
  console.log(
    `[server] connecting MySQL ${MYSQL_USER}@${MYSQL_HOST}:${MYSQL_PORT}/${MYSQL_DATABASE}`,
  )
  await ensureSchema()
  app.listen(API_PORT, '0.0.0.0', () => {
    console.log(`[server] ledger API http://127.0.0.1:${API_PORT}`)
  })
}

main().catch((err) => {
  console.error('[server] failed to start', err)
  process.exit(1)
})
