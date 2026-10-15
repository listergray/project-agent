import Dexie, { type Table } from 'dexie'
import { todayKey } from './lib/dates'
import type { LifeSquareId } from './lib/squares'

export type MoneyCategory = 'cash' | 'deposit' | 'investment' | 'receivable' | 'other'

export type PossessionCategory =
  | 'property'
  | 'vehicle'
  | 'electronics'
  | 'collectible'
  | 'household'
  | 'other'

export type DigitalCategory =
  | 'account'
  | 'domain'
  | 'crypto'
  | 'software'
  | 'subscription'
  | 'media'
  | 'other'

export type SkillCategory = 'tech' | 'language' | 'craft' | 'professional' | 'body' | 'other'

export type SkillLevel = 'beginner' | 'fluent' | 'master' | 'teach'

export type WorkKind = 'job' | 'project' | 'freelance' | 'other'

export type GoalHorizon = 'year' | 'decade' | 'life'
export type GoalStatus = 'active' | 'done' | 'paused'
export type Relation = '家人' | '朋友' | '同事' | '师长' | '其他'

export type Settings = {
  id: 'main'
  birthDate: string
  expectedYears: number
  displayName: string
  pathKey: string
  pathTitle: string
  pathLine: string
}

export type MoneyAsset = {
  id: string
  name: string
  category: MoneyCategory
  amount: number
  note: string
  /** 每月自动增加的金额；0 表示关闭 */
  monthlyAdd: number
  /** 每月几号入账（1–28） */
  monthlyDay: number
  /** 上次月增入账日 YYYY-MM-DD；空 = 尚未入过 */
  lastMonthlyAt: string
  updatedAt: number
}

export type Possession = {
  id: string
  name: string
  category: PossessionCategory
  estimatedValue: number
  acquiredAt: string
  note: string
  updatedAt: number
}

export type DigitalAsset = {
  id: string
  name: string
  category: DigitalCategory
  estimatedValue: number
  account: string
  note: string
  updatedAt: number
}

export type SkillAsset = {
  id: string
  name: string
  category: SkillCategory
  level: SkillLevel
  years: number
  proof: string
  note: string
  updatedAt: number
}

export type WorkRecord = {
  id: string
  title: string
  kind: WorkKind
  org: string
  role: string
  startedAt: string
  endedAt: string
  summary: string
  updatedAt: number
}

export type Task = {
  id: string
  title: string
  date: string
  done: boolean
  sourceKind: string
  sourceId: string
  createdAt: number
}

/** 一日二十四时：每小时一格 */
export type DayHour = {
  /** `${date}-${HH}`，如 2026-08-21-09 */
  id: string
  date: string
  /** 0–23 */
  hour: number
  content: string
  updatedAt: number
}

export type Goal = {
  id: string
  title: string
  horizon: GoalHorizon
  status: GoalStatus
  square: LifeSquareId | ''
  note: string
  targetDate: string
  createdAt: number
}

export type HealthLog = {
  id: string
  date: string
  sleepHours: number | null
  weightKg: number | null
  energy: number | null
  exerciseMin: number | null
  note: string
}

export type Person = {
  id: string
  name: string
  relation: Relation
  howWeMet: string
  phone: string
  city: string
  birthday: string
  lastContactAt: string
  impression: string
  createdAt: number
}

export type PersonField = {
  id: string
  personId: string
  label: string
  value: string
}

export type PersonNote = {
  id: string
  personId: string
  content: string
  createdAt: number
}

export type LifeSquare = {
  id: LifeSquareId
  score: number
  note: string
  intention: string
  updatedAt: number
}

export type Home = {
  id: 'main'
  name: string
  address: string
  layoutPreset: string
  planCols: number
  planRows: number
  /** 整套长，厘米；0 表示未记 */
  lengthCm: number
  /** 整套宽，厘米；0 表示未记 */
  widthCm: number
  /** 层高，厘米；0 表示未记 */
  heightCm: number
  /** 平面图「上」相对真北的偏角（度，顺时针）；0 = 图上为北 */
  northOffsetDeg: number
  rentStartedAt: string
  note: string
  /** OpenPlan3D 项目 JSON 字符串；空 = 尚未用专业编辑器 */
  openPlanJson: string
  updatedAt: number
}

export type Room = {
  id: string
  homeId: string
  name: string
  kind: string
  gridX: number
  gridY: number
  gridW: number
  gridH: number
  /** 房间长，厘米；0 表示未记 */
  lengthCm: number
  /** 房间宽，厘米；0 表示未记 */
  widthCm: number
  /** 房间高，厘米；0 表示未记 */
  heightCm: number
  /** 朝向：N/NE/E/SE/S/SW/W/NW 或空 */
  facing: string
  note: string
  sortOrder: number
  updatedAt: number
}

export type RoomItem = {
  id: string
  roomId: string
  parentId: string
  propKey: string
  name: string
  category: string
  /** 长，厘米；0 表示未记 */
  lengthCm: number
  /** 宽，厘米；0 表示未记 */
  widthCm: number
  /** 高，厘米；0 表示未记 */
  heightCm: number
  /** 平面占位：距房间西墙（米）；<0 表示不在平面图上 */
  planXM: number
  /** 平面占位：距房间北墙（米） */
  planYM: number
  /** 平面占位宽（东西，米）；0 表示不画在平面图 */
  planWM: number
  /** 平面占位深（南北，米） */
  planDM: number
  note: string
  updatedAt: number
}

/** 平面组件库条目：可拖到平面上实例化为门窗或物件 */
export type PlanComponentFamily = 'fixture' | 'prop'

export type PlanComponent = {
  id: string
  name: string
  family: PlanComponentFamily
  /** fixture: entrance|door|…；prop: sofa|generic|自定义 key */
  typeKey: string
  /** 门窗沿墙宽 / 物件东西向占位（米） */
  widthM: number
  /** 物件南北向占位（米）；门窗不用 */
  depthM: number
  heightM: number
  sillM: number
  category: string
  /** 平面标记色，如 #38bdf8 */
  color: string
  note: string
  sortOrder: number
  builtin: boolean
  updatedAt: number
}

export type Maintain = {
  id: string
  title: string
  everyDays: number
  lastDoneAt: string
  roomItemId: string
  roomId: string
  note: string
  enabled: boolean
  updatedAt: number
}

/** 房屋构件：门 / 窗等，挂在房间某面墙上 */
export type FixtureKind = 'entrance' | 'door' | 'window' | 'sliding' | 'french'
export type WallSide = 'N' | 'E' | 'S' | 'W'

export type RoomFixture = {
  id: string
  roomId: string
  kind: FixtureKind
  name: string
  /** 所在墙面（上北下南） */
  wall: WallSide
  /** 沿墙起点偏移（米）；N/S 墙从西起，E/W 墙从北起 */
  offsetM: number
  widthM: number
  heightM: number
  /** 距地高度（米）；门一般为 0 */
  sillM: number
  note: string
  updatedAt: number
}

class LedgerDB extends Dexie {
  settings!: Table<Settings, string>
  moneyAssets!: Table<MoneyAsset, string>
  possessions!: Table<Possession, string>
  digitalAssets!: Table<DigitalAsset, string>
  skillAssets!: Table<SkillAsset, string>
  workRecords!: Table<WorkRecord, string>
  tasks!: Table<Task, string>
  goals!: Table<Goal, string>
  healthLogs!: Table<HealthLog, string>
  people!: Table<Person, string>
  personFields!: Table<PersonField, string>
  personNotes!: Table<PersonNote, string>
  lifeSquares!: Table<LifeSquare, LifeSquareId>
  homes!: Table<Home, string>
  rooms!: Table<Room, string>
  roomItems!: Table<RoomItem, string>
  maintains!: Table<Maintain, string>
  roomFixtures!: Table<RoomFixture, string>
  planComponents!: Table<PlanComponent, string>
  dayHours!: Table<DayHour, string>

  constructor() {
    super('wodesuoyou')
    this.version(1).stores({
      settings: 'id',
      moneyAssets: 'id, category, updatedAt',
      possessions: 'id, category, updatedAt',
      tasks: 'id, date, done',
      goals: 'id, status, horizon',
      healthLogs: 'id, date',
      people: 'id, relation, name',
      personFields: 'id, personId',
      personNotes: 'id, personId, createdAt',
    })
    this.version(2)
      .stores({
        settings: 'id',
        moneyAssets: 'id, category, updatedAt',
        possessions: 'id, category, updatedAt',
        digitalAssets: 'id, category, updatedAt',
        skillAssets: 'id, category, updatedAt',
        workRecords: 'id, kind, startedAt',
        tasks: 'id, date, done',
        goals: 'id, status, horizon',
        healthLogs: 'id, date',
        people: 'id, relation, name',
        personFields: 'id, personId',
        personNotes: 'id, personId, createdAt',
      })
      .upgrade(async (tx) => {
        const money = (await tx.table('moneyAssets').toArray()) as Array<{
          id: string
          name: string
          category: string
          amount: number
          note: string
          updatedAt: number
        }>
        const digital = money.filter((row) => row.category === 'digital')
        if (digital.length) {
          await tx.table('digitalAssets').bulkAdd(
            digital.map((row) => ({
              id: row.id,
              name: row.name,
              category: 'crypto' as const,
              estimatedValue: row.amount,
              account: '',
              note: row.note,
              updatedAt: row.updatedAt,
            })),
          )
          await tx.table('moneyAssets').bulkDelete(digital.map((row) => row.id))
        }
      })
    this.version(3).stores({
      settings: 'id',
      moneyAssets: 'id, category, updatedAt',
      possessions: 'id, category, updatedAt',
      digitalAssets: 'id, category, updatedAt',
      skillAssets: 'id, category, updatedAt',
      workRecords: 'id, kind, startedAt',
      tasks: 'id, date, done',
      goals: 'id, status, horizon, square',
      healthLogs: 'id, date',
      people: 'id, relation, name',
      personFields: 'id, personId',
      personNotes: 'id, personId, createdAt',
      lifeSquares: 'id, updatedAt',
    })
    this.version(4).stores({
      settings: 'id',
      moneyAssets: 'id, category, updatedAt',
      possessions: 'id, category, updatedAt',
      digitalAssets: 'id, category, updatedAt',
      skillAssets: 'id, category, updatedAt',
      workRecords: 'id, kind, startedAt',
      tasks: 'id, date, done',
      goals: 'id, status, horizon, square',
      healthLogs: 'id, date',
      people: 'id, relation, name',
      personFields: 'id, personId',
      personNotes: 'id, personId, createdAt',
      lifeSquares: 'id, updatedAt',
      homes: 'id',
      rooms: 'id, homeId, sortOrder',
      roomItems: 'id, roomId, updatedAt',
    })
    this.version(5)
      .stores({
        settings: 'id',
        moneyAssets: 'id, category, updatedAt',
        possessions: 'id, category, updatedAt',
        digitalAssets: 'id, category, updatedAt',
        skillAssets: 'id, category, updatedAt',
        workRecords: 'id, kind, startedAt',
        tasks: 'id, date, done',
        goals: 'id, status, horizon, square',
        healthLogs: 'id, date',
        people: 'id, relation, name',
        personFields: 'id, personId',
        personNotes: 'id, personId, createdAt',
        lifeSquares: 'id, updatedAt',
        homes: 'id',
        rooms: 'id, homeId, sortOrder',
        roomItems: 'id, roomId, parentId, updatedAt',
      })
      .upgrade(async (tx) => {
        const rows = (await tx.table('roomItems').toArray()) as Array<{
          id: string
          roomId: string
          name: string
          category: string
          note: string
          updatedAt: number
          parentId?: string
          propKey?: string
        }>
        for (const row of rows) {
          const name = row.name ?? ''
          let propKey = row.propKey ?? ''
          if (!propKey) {
            if (/沙发|sofa|couch/.test(name)) propKey = 'sofa'
            else if (/电视|tv|显示器|屏幕/.test(name)) propKey = 'tv'
            else if (/冰箱|fridge/.test(name)) propKey = 'fridge'
            else if (/床|bed/.test(name)) propKey = 'bed'
            else if (/书桌|desk|电脑桌/.test(name)) propKey = 'desk'
            else if (/衣柜|wardrobe|衣橱/.test(name)) propKey = 'wardrobe'
            else if (/茶几|餐桌|table|桌子/.test(name)) propKey = 'table'
            else if (/椅|chair/.test(name)) propKey = 'chair'
            else if (/灯|lamp/.test(name)) propKey = 'lamp'
            else if (/架|shelf|书柜/.test(name)) propKey = 'shelf'
            else if (/灶|stove/.test(name)) propKey = 'stove'
            else if (/洗手|sink/.test(name)) propKey = 'sink'
            else if (/马桶|toilet/.test(name)) propKey = 'toilet'
            else if (/淋浴|shower|浴/.test(name)) propKey = 'shower'
            else if (/植物|plant|绿植/.test(name)) propKey = 'plant'
            else propKey = 'generic'
          }
          await tx.table('roomItems').update(row.id, {
            parentId: row.parentId ?? '',
            propKey,
          })
        }
      })
    this.version(6)
      .stores({
        settings: 'id',
        moneyAssets: 'id, category, updatedAt',
        possessions: 'id, category, updatedAt',
        digitalAssets: 'id, category, updatedAt',
        skillAssets: 'id, category, updatedAt',
        workRecords: 'id, kind, startedAt',
        tasks: 'id, date, done, sourceKind, sourceId',
        goals: 'id, status, horizon, square',
        healthLogs: 'id, date',
        people: 'id, relation, name',
        personFields: 'id, personId',
        personNotes: 'id, personId, createdAt',
        lifeSquares: 'id, updatedAt',
        homes: 'id',
        rooms: 'id, homeId, sortOrder',
        roomItems: 'id, roomId, parentId, updatedAt',
      })
      .upgrade(async (tx) => {
        const tasks = (await tx.table('tasks').toArray()) as Array<{
          id: string
          sourceKind?: string
          sourceId?: string
        }>
        for (const row of tasks) {
          await tx.table('tasks').update(row.id, {
            sourceKind: row.sourceKind ?? '',
            sourceId: row.sourceId ?? '',
          })
        }
        const items = (await tx.table('roomItems').toArray()) as Array<{
          id: string
          maintainEveryDays?: number
          maintainLabel?: string
          lastMaintainedAt?: string
        }>
        for (const row of items) {
          await tx.table('roomItems').update(row.id, {
            maintainEveryDays: row.maintainEveryDays ?? 0,
            maintainLabel: row.maintainLabel ?? '',
            lastMaintainedAt: row.lastMaintainedAt ?? '',
          })
        }
      })
    this.version(7)
      .stores({
        settings: 'id',
        moneyAssets: 'id, category, updatedAt',
        possessions: 'id, category, updatedAt',
        digitalAssets: 'id, category, updatedAt',
        skillAssets: 'id, category, updatedAt',
        workRecords: 'id, kind, startedAt',
        tasks: 'id, date, done, sourceKind, sourceId',
        goals: 'id, status, horizon, square',
        healthLogs: 'id, date',
        people: 'id, relation, name',
        personFields: 'id, personId',
        personNotes: 'id, personId, createdAt',
        lifeSquares: 'id, updatedAt',
        homes: 'id',
        rooms: 'id, homeId, sortOrder',
        roomItems: 'id, roomId, parentId, updatedAt',
        maintains: 'id, roomItemId, roomId, enabled, updatedAt',
      })
      .upgrade(async (tx) => {
        const itemToMaintain = new Map<string, string>()
        const items = (await tx.table('roomItems').toArray()) as Array<{
          id: string
          roomId: string
          name: string
          maintainEveryDays?: number
          maintainLabel?: string
          lastMaintainedAt?: string
          updatedAt: number
        }>
        for (const item of items) {
          const everyDays = item.maintainEveryDays ?? 0
          if (everyDays <= 0) continue
          const id = crypto.randomUUID()
          const title =
            (item.maintainLabel ?? '').trim() || `${item.name} · 维护`
          await tx.table('maintains').add({
            id,
            title,
            everyDays,
            lastDoneAt: item.lastMaintainedAt ?? '',
            roomItemId: item.id,
            roomId: item.roomId,
            note: '',
            enabled: true,
            updatedAt: item.updatedAt ?? Date.now(),
          })
          itemToMaintain.set(item.id, id)
          await tx.table('roomItems').update(item.id, {
            maintainEveryDays: 0,
            maintainLabel: '',
            lastMaintainedAt: '',
          })
        }
        const tasks = (await tx.table('tasks').toArray()) as Array<{
          id: string
          sourceKind?: string
          sourceId?: string
        }>
        for (const task of tasks) {
          if (task.sourceKind !== 'room-maintain' || !task.sourceId) continue
          const maintainId = itemToMaintain.get(task.sourceId)
          await tx.table('tasks').update(task.id, {
            sourceKind: maintainId ? 'maintain' : '',
            sourceId: maintainId ?? '',
          })
        }
      })
    this.version(8)
      .stores({
        settings: 'id',
        moneyAssets: 'id, category, updatedAt',
        possessions: 'id, category, updatedAt',
        digitalAssets: 'id, category, updatedAt',
        skillAssets: 'id, category, updatedAt',
        workRecords: 'id, kind, startedAt',
        tasks: 'id, date, done, sourceKind, sourceId',
        goals: 'id, status, horizon, square',
        healthLogs: 'id, date',
        people: 'id, relation, name',
        personFields: 'id, personId',
        personNotes: 'id, personId, createdAt',
        lifeSquares: 'id, updatedAt',
        homes: 'id',
        rooms: 'id, homeId, sortOrder',
        roomItems: 'id, roomId, parentId, updatedAt',
        maintains: 'id, roomItemId, roomId, enabled, updatedAt',
      })
      .upgrade(async (tx) => {
        const home = await tx.table('homes').get('main')
        if (home) {
          await tx.table('homes').update('main', {
            planCols: home.planCols ?? 12,
            planRows: home.planRows ?? 8,
          })
        }
      })
    this.version(9)
      .stores({
        settings: 'id',
        moneyAssets: 'id, category, updatedAt',
        possessions: 'id, category, updatedAt',
        digitalAssets: 'id, category, updatedAt',
        skillAssets: 'id, category, updatedAt',
        workRecords: 'id, kind, startedAt',
        tasks: 'id, date, done, sourceKind, sourceId',
        goals: 'id, status, horizon, square',
        healthLogs: 'id, date',
        people: 'id, relation, name',
        personFields: 'id, personId',
        personNotes: 'id, personId, createdAt',
        lifeSquares: 'id, updatedAt',
        homes: 'id',
        rooms: 'id, homeId, sortOrder',
        roomItems: 'id, roomId, parentId, updatedAt',
        maintains: 'id, roomItemId, roomId, enabled, updatedAt',
      })
      .upgrade(async (tx) => {
        const items = (await tx.table('roomItems').toArray()) as Array<{
          id: string
          lengthCm?: number
          widthCm?: number
          heightCm?: number
        }>
        for (const item of items) {
          await tx.table('roomItems').update(item.id, {
            lengthCm: item.lengthCm ?? 0,
            widthCm: item.widthCm ?? 0,
            heightCm: item.heightCm ?? 0,
          })
        }
      })
    this.version(10)
      .stores({
        settings: 'id',
        moneyAssets: 'id, category, updatedAt',
        possessions: 'id, category, updatedAt',
        digitalAssets: 'id, category, updatedAt',
        skillAssets: 'id, category, updatedAt',
        workRecords: 'id, kind, startedAt',
        tasks: 'id, date, done, sourceKind, sourceId',
        goals: 'id, status, horizon, square',
        healthLogs: 'id, date',
        people: 'id, relation, name',
        personFields: 'id, personId',
        personNotes: 'id, personId, createdAt',
        lifeSquares: 'id, updatedAt',
        homes: 'id',
        rooms: 'id, homeId, sortOrder',
        roomItems: 'id, roomId, parentId, updatedAt',
        maintains: 'id, roomItemId, roomId, enabled, updatedAt',
      })
      .upgrade(async (tx) => {
        const homes = (await tx.table('homes').toArray()) as Array<{
          id: string
          lengthCm?: number
          widthCm?: number
          heightCm?: number
        }>
        for (const home of homes) {
          await tx.table('homes').update(home.id, {
            lengthCm: home.lengthCm ?? 0,
            widthCm: home.widthCm ?? 0,
            heightCm: home.heightCm ?? 0,
          })
        }
        const rooms = (await tx.table('rooms').toArray()) as Array<{
          id: string
          lengthCm?: number
          widthCm?: number
          heightCm?: number
        }>
        for (const room of rooms) {
          await tx.table('rooms').update(room.id, {
            lengthCm: room.lengthCm ?? 0,
            widthCm: room.widthCm ?? 0,
            heightCm: room.heightCm ?? 0,
          })
        }
      })
    this.version(11)
      .stores({
        settings: 'id',
        moneyAssets: 'id, category, updatedAt',
        possessions: 'id, category, updatedAt',
        digitalAssets: 'id, category, updatedAt',
        skillAssets: 'id, category, updatedAt',
        workRecords: 'id, kind, startedAt',
        tasks: 'id, date, done, sourceKind, sourceId',
        goals: 'id, status, horizon, square',
        healthLogs: 'id, date',
        people: 'id, relation, name',
        personFields: 'id, personId',
        personNotes: 'id, personId, createdAt',
        lifeSquares: 'id, updatedAt',
        homes: 'id',
        rooms: 'id, homeId, sortOrder',
        roomItems: 'id, roomId, parentId, updatedAt',
        maintains: 'id, roomItemId, roomId, enabled, updatedAt',
      })
      .upgrade(async (tx) => {
        const CELL = 100
        const homes = (await tx.table('homes').toArray()) as Array<{
          id: string
          planCols?: number
          planRows?: number
          heightCm?: number
        }>
        for (const home of homes) {
          const cols = home.planCols ?? 12
          const rows = home.planRows ?? 8
          await tx.table('homes').update(home.id, {
            lengthCm: cols * CELL,
            widthCm: rows * CELL,
            heightCm: home.heightCm ?? 0,
          })
        }
        const rooms = (await tx.table('rooms').toArray()) as Array<{
          id: string
          gridW?: number
          gridH?: number
          heightCm?: number
        }>
        for (const room of rooms) {
          await tx.table('rooms').update(room.id, {
            lengthCm: (room.gridW ?? 1) * CELL,
            widthCm: (room.gridH ?? 1) * CELL,
            heightCm: room.heightCm ?? 0,
          })
        }
      })
    this.version(12)
      .stores({
        settings: 'id',
        moneyAssets: 'id, category, updatedAt',
        possessions: 'id, category, updatedAt',
        digitalAssets: 'id, category, updatedAt',
        skillAssets: 'id, category, updatedAt',
        workRecords: 'id, kind, startedAt',
        tasks: 'id, date, done, sourceKind, sourceId',
        goals: 'id, status, horizon, square',
        healthLogs: 'id, date',
        people: 'id, relation, name',
        personFields: 'id, personId',
        personNotes: 'id, personId, createdAt',
        lifeSquares: 'id, updatedAt',
        homes: 'id',
        rooms: 'id, homeId, sortOrder',
        roomItems: 'id, roomId, parentId, updatedAt',
        maintains: 'id, roomItemId, roomId, enabled, updatedAt',
      })
      .upgrade(async (tx) => {
        const homes = (await tx.table('homes').toArray()) as Array<{
          id: string
          northOffsetDeg?: number
        }>
        for (const home of homes) {
          await tx.table('homes').update(home.id, {
            northOffsetDeg: home.northOffsetDeg ?? 0,
          })
        }
        const rooms = (await tx.table('rooms').toArray()) as Array<{
          id: string
          facing?: string
        }>
        for (const room of rooms) {
          await tx.table('rooms').update(room.id, {
            facing: room.facing ?? '',
          })
        }
      })
    this.version(13).stores({
      settings: 'id',
      moneyAssets: 'id, category, updatedAt',
      possessions: 'id, category, updatedAt',
      digitalAssets: 'id, category, updatedAt',
      skillAssets: 'id, category, updatedAt',
      workRecords: 'id, kind, startedAt',
      tasks: 'id, date, done, sourceKind, sourceId',
      goals: 'id, status, horizon, square',
      healthLogs: 'id, date',
      people: 'id, relation, name',
      personFields: 'id, personId',
      personNotes: 'id, personId, createdAt',
      lifeSquares: 'id, updatedAt',
      homes: 'id',
      rooms: 'id, homeId, sortOrder',
      roomItems: 'id, roomId, parentId, updatedAt',
      maintains: 'id, roomItemId, roomId, enabled, updatedAt',
      roomFixtures: 'id, roomId, kind, updatedAt',
    })
    this.version(14)
      .stores({
        settings: 'id',
        moneyAssets: 'id, category, updatedAt',
        possessions: 'id, category, updatedAt',
        digitalAssets: 'id, category, updatedAt',
        skillAssets: 'id, category, updatedAt',
        workRecords: 'id, kind, startedAt',
        tasks: 'id, date, done, sourceKind, sourceId',
        goals: 'id, status, horizon, square',
        healthLogs: 'id, date',
        people: 'id, relation, name',
        personFields: 'id, personId',
        personNotes: 'id, personId, createdAt',
        lifeSquares: 'id, updatedAt',
        homes: 'id',
        rooms: 'id, homeId, sortOrder',
        roomItems: 'id, roomId, parentId, updatedAt',
        maintains: 'id, roomItemId, roomId, enabled, updatedAt',
        roomFixtures: 'id, roomId, kind, updatedAt',
        planComponents: 'id, family, sortOrder, updatedAt',
      })
      .upgrade(async (tx) => {
        const items = (await tx.table('roomItems').toArray()) as Array<{
          id: string
          planXM?: number
          planYM?: number
          planWM?: number
          planDM?: number
        }>
        for (const item of items) {
          await tx.table('roomItems').update(item.id, {
            planXM: item.planXM ?? -1,
            planYM: item.planYM ?? 0,
            planWM: item.planWM ?? 0,
            planDM: item.planDM ?? 0,
          })
        }
      })
    this.version(15)
      .stores({
        settings: 'id',
        moneyAssets: 'id, category, updatedAt',
        possessions: 'id, category, updatedAt',
        digitalAssets: 'id, category, updatedAt',
        skillAssets: 'id, category, updatedAt',
        workRecords: 'id, kind, startedAt',
        tasks: 'id, date, done, sourceKind, sourceId',
        goals: 'id, status, horizon, square',
        healthLogs: 'id, date',
        people: 'id, relation, name',
        personFields: 'id, personId',
        personNotes: 'id, personId, createdAt',
        lifeSquares: 'id, updatedAt',
        homes: 'id',
        rooms: 'id, homeId, sortOrder',
        roomItems: 'id, roomId, parentId, updatedAt',
        maintains: 'id, roomItemId, roomId, enabled, updatedAt',
        roomFixtures: 'id, roomId, kind, updatedAt',
        planComponents: 'id, family, sortOrder, updatedAt',
      })
      .upgrade(async (tx) => {
        const homes = (await tx.table('homes').toArray()) as Array<{
          id: string
          openPlanJson?: string
        }>
        for (const home of homes) {
          await tx.table('homes').update(home.id, {
            openPlanJson: home.openPlanJson ?? '',
          })
        }
      })
    this.version(16)
      .stores({
        settings: 'id',
        moneyAssets: 'id, category, updatedAt',
        possessions: 'id, category, updatedAt',
        digitalAssets: 'id, category, updatedAt',
        skillAssets: 'id, category, updatedAt',
        workRecords: 'id, kind, startedAt',
        tasks: 'id, date, done, sourceKind, sourceId',
        goals: 'id, status, horizon, square',
        healthLogs: 'id, date',
        people: 'id, relation, name',
        personFields: 'id, personId',
        personNotes: 'id, personId, createdAt',
        lifeSquares: 'id, updatedAt',
        homes: 'id',
        rooms: 'id, homeId, sortOrder',
        roomItems: 'id, roomId, parentId, updatedAt',
        maintains: 'id, roomItemId, roomId, enabled, updatedAt',
        roomFixtures: 'id, roomId, kind, updatedAt',
        planComponents: 'id, family, sortOrder, updatedAt',
      })
      .upgrade(async (tx) => {
        const rows = (await tx.table('moneyAssets').toArray()) as Array<{
          id: string
          monthlyAdd?: number
          monthlyDay?: number
          lastMonthlyAt?: string
        }>
        for (const row of rows) {
          await tx.table('moneyAssets').update(row.id, {
            monthlyAdd: row.monthlyAdd ?? 0,
            monthlyDay: row.monthlyDay ?? 1,
            lastMonthlyAt: row.lastMonthlyAt ?? '',
          })
        }
      })
    this.version(17).stores({
      settings: 'id',
      moneyAssets: 'id, category, updatedAt',
      possessions: 'id, category, updatedAt',
      digitalAssets: 'id, category, updatedAt',
      skillAssets: 'id, category, updatedAt',
      workRecords: 'id, kind, startedAt',
      tasks: 'id, date, done, sourceKind, sourceId',
      goals: 'id, status, horizon, square',
      healthLogs: 'id, date',
      people: 'id, relation, name',
      personFields: 'id, personId',
      personNotes: 'id, personId, createdAt',
      lifeSquares: 'id, updatedAt',
      homes: 'id',
      rooms: 'id, homeId, sortOrder',
      roomItems: 'id, roomId, parentId, updatedAt',
      maintains: 'id, roomItemId, roomId, enabled, updatedAt',
      roomFixtures: 'id, roomId, kind, updatedAt',
      planComponents: 'id, family, sortOrder, updatedAt',
      dayHours: 'id, date, hour',
    })
  }
}

export const db = new LedgerDB()

export const MONEY_LABELS: Record<MoneyCategory, string> = {
  cash: '现金',
  deposit: '存款',
  investment: '投资',
  receivable: '债权',
  other: '其他',
}

export const POSSESSION_LABELS: Record<PossessionCategory, string> = {
  property: '房产',
  vehicle: '车辆',
  electronics: '数码',
  collectible: '收藏',
  household: '家居衣物',
  other: '其他',
}

export const DIGITAL_LABELS: Record<DigitalCategory, string> = {
  account: '账号',
  domain: '域名',
  crypto: '加密货币',
  software: '软件许可',
  subscription: '订阅',
  media: '内容藏品',
  other: '其他',
}

export const SKILL_LABELS: Record<SkillCategory, string> = {
  tech: '技术',
  language: '语言',
  craft: '手艺',
  professional: '职业',
  body: '体能',
  other: '其他',
}

export const LEVEL_LABELS: Record<SkillLevel, string> = {
  beginner: '入门',
  fluent: '熟练',
  master: '精通',
  teach: '可授',
}

export const WORK_LABELS: Record<WorkKind, string> = {
  job: '任职',
  project: '项目',
  freelance: '独立',
  other: '其他',
}

export const HORIZON_LABELS: Record<GoalHorizon, string> = {
  year: '今年',
  decade: '十年',
  life: '此生',
}

export const RELATIONS: Relation[] = ['家人', '朋友', '同事', '师长', '其他']

export const FIELD_SUGGESTIONS = [
  '忌口',
  '性格',
  '近况',
  '家人',
  '孩子',
  '职业',
  '喜好',
  '忌讳',
  '如何相处',
  '重要日子',
]

export async function ensureSettings() {
  const row = await db.settings.get('main')
  if (!row) {
    await db.settings.add({
      id: 'main',
      birthDate: '',
      expectedYears: 80,
      displayName: '',
      pathKey: '',
      pathTitle: '',
      pathLine: '',
    })
  } else if (row.pathKey == null || row.pathTitle == null || row.pathLine == null) {
    await db.settings.update('main', {
      pathKey: row.pathKey ?? '',
      pathTitle: row.pathTitle ?? '',
      pathLine: row.pathLine ?? '',
    })
  }
  const { ensurePlanCatalog } = await import('./lib/planCatalog')
  await ensurePlanCatalog()
}

export type LedgerDump = {
  exportedAt: string
  settings: Settings[]
  moneyAssets: MoneyAsset[]
  possessions: Possession[]
  digitalAssets: DigitalAsset[]
  skillAssets: SkillAsset[]
  workRecords: WorkRecord[]
  tasks: Task[]
  goals: Goal[]
  healthLogs: HealthLog[]
  people: Person[]
  personFields: PersonField[]
  personNotes: PersonNote[]
  lifeSquares: LifeSquare[]
  homes: Home[]
  rooms: Room[]
  roomItems: RoomItem[]
  maintains: Maintain[]
  roomFixtures: RoomFixture[]
  planComponents: PlanComponent[]
  dayHours: DayHour[]
}

export async function buildLedgerDump(): Promise<LedgerDump> {
  return {
    exportedAt: new Date().toISOString(),
    settings: await db.settings.toArray(),
    moneyAssets: await db.moneyAssets.toArray(),
    possessions: await db.possessions.toArray(),
    digitalAssets: await db.digitalAssets.toArray(),
    skillAssets: await db.skillAssets.toArray(),
    workRecords: await db.workRecords.toArray(),
    tasks: await db.tasks.toArray(),
    goals: await db.goals.toArray(),
    healthLogs: await db.healthLogs.toArray(),
    people: await db.people.toArray(),
    personFields: await db.personFields.toArray(),
    personNotes: await db.personNotes.toArray(),
    lifeSquares: await db.lifeSquares.toArray(),
    homes: await db.homes.toArray(),
    rooms: await db.rooms.toArray(),
    roomItems: await db.roomItems.toArray(),
    maintains: await db.maintains.toArray(),
    roomFixtures: await db.roomFixtures.toArray(),
    planComponents: await db.planComponents.toArray(),
    dayHours: await db.dayHours.toArray(),
  }
}

export async function exportLedger() {
  const payload = await buildLedgerDump()
  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: 'application/json',
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `我的所有-${todayKey()}.json`
  a.click()
  URL.revokeObjectURL(url)
}

export async function importLedger(data: LedgerDump) {
  await db.transaction(
    'rw',
    [
      db.settings,
      db.moneyAssets,
      db.possessions,
      db.digitalAssets,
      db.skillAssets,
      db.workRecords,
      db.tasks,
      db.goals,
      db.healthLogs,
      db.people,
      db.personFields,
      db.personNotes,
      db.lifeSquares,
      db.homes,
      db.rooms,
      db.roomItems,
      db.maintains,
      db.roomFixtures,
      db.planComponents,
      db.dayHours,
    ],
    async () => {
      await db.settings.clear()
      await db.moneyAssets.clear()
      await db.possessions.clear()
      await db.digitalAssets.clear()
      await db.skillAssets.clear()
      await db.workRecords.clear()
      await db.tasks.clear()
      await db.goals.clear()
      await db.healthLogs.clear()
      await db.people.clear()
      await db.personFields.clear()
      await db.personNotes.clear()
      await db.lifeSquares.clear()
      await db.homes.clear()
      await db.rooms.clear()
      await db.roomItems.clear()
      await db.maintains.clear()
      await db.roomFixtures.clear()
      await db.planComponents.clear()
      await db.dayHours.clear()
      const incomingMoney = (data.moneyAssets ?? []) as Array<
        Omit<MoneyAsset, 'category'> & { category: string; amount: number }
      >
      const legacyDigital = incomingMoney.filter((row) => row.category === 'digital')
      const money = incomingMoney
        .filter((row) => row.category !== 'digital')
        .map((row) => ({ ...row, category: row.category as MoneyCategory }))
      const migratedDigital: DigitalAsset[] = legacyDigital.map((row) => ({
        id: row.id,
        name: row.name,
        category: 'crypto',
        estimatedValue: row.amount,
        account: '',
        note: row.note,
        updatedAt: row.updatedAt,
      }))
      if (data.settings?.length)
        await db.settings.bulkAdd(
          data.settings.map((row) => ({
            ...row,
            pathKey: row.pathKey ?? '',
            pathTitle: row.pathTitle ?? '',
            pathLine: row.pathLine ?? '',
          })),
        )
      if (money.length)
        await db.moneyAssets.bulkAdd(
          money.map((row) => ({
            ...row,
            monthlyAdd: row.monthlyAdd ?? 0,
            monthlyDay: row.monthlyDay ?? 1,
            lastMonthlyAt: row.lastMonthlyAt ?? '',
          })),
        )
      if (data.possessions?.length) await db.possessions.bulkAdd(data.possessions)
      const digital = [...(data.digitalAssets ?? []), ...migratedDigital]
      if (digital.length) await db.digitalAssets.bulkAdd(digital)
      if (data.skillAssets?.length) await db.skillAssets.bulkAdd(data.skillAssets)
      if (data.workRecords?.length) await db.workRecords.bulkAdd(data.workRecords)
      if (data.tasks?.length)
        await db.tasks.bulkAdd(
          data.tasks.map((row) => ({
            ...row,
            sourceKind: row.sourceKind ?? '',
            sourceId: row.sourceId ?? '',
          })),
        )
      if (data.goals?.length)
        await db.goals.bulkAdd(
          data.goals.map((row) => ({
            ...row,
            square: row.square ?? '',
          })),
        )
      if (data.healthLogs?.length) await db.healthLogs.bulkAdd(data.healthLogs)
      if (data.people?.length) await db.people.bulkAdd(data.people)
      if (data.personFields?.length) await db.personFields.bulkAdd(data.personFields)
      if (data.personNotes?.length) await db.personNotes.bulkAdd(data.personNotes)
      if (data.lifeSquares?.length) await db.lifeSquares.bulkAdd(data.lifeSquares)
      if (data.homes?.length)
        await db.homes.bulkAdd(
          data.homes.map((row) => ({
            ...row,
            planCols: row.planCols ?? 12,
            planRows: row.planRows ?? 8,
            lengthCm: row.lengthCm ?? 0,
            widthCm: row.widthCm ?? 0,
            heightCm: row.heightCm ?? 0,
            northOffsetDeg: row.northOffsetDeg ?? 0,
            openPlanJson: row.openPlanJson ?? '',
          })),
        )
      if (data.rooms?.length)
        await db.rooms.bulkAdd(
          data.rooms.map((row) => ({
            ...row,
            lengthCm: row.lengthCm ?? 0,
            widthCm: row.widthCm ?? 0,
            heightCm: row.heightCm ?? 0,
            facing: row.facing ?? '',
          })),
        )
      if (data.roomItems?.length)
        await db.roomItems.bulkAdd(
          data.roomItems.map((row) => ({
            id: row.id,
            roomId: row.roomId,
            parentId: row.parentId ?? '',
            propKey: row.propKey ?? '',
            name: row.name,
            category: row.category,
            lengthCm: row.lengthCm ?? 0,
            widthCm: row.widthCm ?? 0,
            heightCm: row.heightCm ?? 0,
            planXM: row.planXM ?? -1,
            planYM: row.planYM ?? 0,
            planWM: row.planWM ?? 0,
            planDM: row.planDM ?? 0,
            note: row.note ?? '',
            updatedAt: row.updatedAt,
          })),
        )
      if (data.maintains?.length)
        await db.maintains.bulkAdd(
          data.maintains.map((row) => ({
            ...row,
            roomItemId: row.roomItemId ?? '',
            roomId: row.roomId ?? '',
            enabled: row.enabled ?? true,
          })),
        )
      if (data.roomFixtures?.length)
        await db.roomFixtures.bulkAdd(
          data.roomFixtures.map((row) => ({
            id: row.id,
            roomId: row.roomId,
            kind: row.kind,
            name: row.name,
            wall: row.wall,
            offsetM: row.offsetM ?? 0,
            widthM: row.widthM ?? 0.9,
            heightM: row.heightM ?? (row.kind === 'window' ? 1.4 : 2.1),
            sillM: row.sillM ?? (row.kind === 'window' ? 0.9 : 0),
            note: row.note ?? '',
            updatedAt: row.updatedAt,
          })),
        )
      if (data.planComponents?.length)
        await db.planComponents.bulkAdd(
          data.planComponents.map((row) => ({
            id: row.id,
            name: row.name,
            family: row.family,
            typeKey: row.typeKey,
            widthM: row.widthM ?? 0.9,
            depthM: row.depthM ?? 0.6,
            heightM: row.heightM ?? 1,
            sillM: row.sillM ?? 0,
            category: row.category ?? '',
            color: row.color ?? '#94a3b8',
            note: row.note ?? '',
            sortOrder: row.sortOrder ?? 0,
            builtin: row.builtin ?? false,
            updatedAt: row.updatedAt,
          })),
        )
      if (data.dayHours?.length)
        await db.dayHours.bulkAdd(
          data.dayHours.map((row) => ({
            id: row.id || `${row.date}-${String(row.hour).padStart(2, '0')}`,
            date: row.date,
            hour: Math.min(23, Math.max(0, Math.round(row.hour))),
            content: row.content ?? '',
            updatedAt: row.updatedAt ?? Date.now(),
          })),
        )
    },
  )
  await ensureSettings()
}

export async function clearLedger() {
  await db.delete()
  await db.open()
  await ensureSettings()
}
