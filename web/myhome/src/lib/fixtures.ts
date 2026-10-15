import { db, type FixtureKind, type RoomFixture, type WallSide } from '../db'
import { nid } from './dates'
import { cmToMeters } from './homeLayout'

export const FIXTURE_KINDS: FixtureKind[] = ['entrance', 'door', 'window', 'sliding', 'french']

export const FIXTURE_LABELS: Record<FixtureKind, string> = {
  entrance: '入户门',
  door: '房门',
  window: '窗',
  sliding: '推拉门',
  french: '落地窗',
}

export const WALL_SIDES: WallSide[] = ['N', 'E', 'S', 'W']

export const WALL_LABELS: Record<WallSide, string> = {
  N: '北墙',
  E: '东墙',
  S: '南墙',
  W: '西墙',
}

export function defaultFixtureSize(kind: FixtureKind): {
  widthM: number
  heightM: number
  sillM: number
} {
  if (kind === 'window') return { widthM: 1.5, heightM: 1.4, sillM: 0.9 }
  if (kind === 'french') return { widthM: 1.8, heightM: 2.2, sillM: 0 }
  if (kind === 'sliding') return { widthM: 1.6, heightM: 2.1, sillM: 0 }
  if (kind === 'entrance') return { widthM: 1.0, heightM: 2.1, sillM: 0 }
  return { widthM: 0.9, heightM: 2.1, sillM: 0 }
}

export function wallLengthM(
  room: { lengthCm?: number; widthCm?: number; gridW: number; gridH: number },
  wall: WallSide,
): number {
  const L = cmToMeters(room.lengthCm ?? 0) || room.gridW
  const W = cmToMeters(room.widthCm ?? 0) || room.gridH
  return wall === 'N' || wall === 'S' ? L : W
}

export async function addFixture(
  roomId: string,
  partial?: Partial<Pick<RoomFixture, 'kind' | 'name' | 'wall'>>,
) {
  const kind = partial?.kind ?? 'window'
  const size = defaultFixtureSize(kind)
  const id = nid()
  await db.roomFixtures.add({
    id,
    roomId,
    kind,
    name: partial?.name?.trim() || FIXTURE_LABELS[kind],
    wall: partial?.wall ?? 'S',
    offsetM: 0.5,
    ...size,
    note: '',
    updatedAt: Date.now(),
  })
  return id
}

export async function deleteFixture(id: string) {
  await db.roomFixtures.delete(id)
}

/** 平面图上构件在房间矩形上的线段位置（百分比）
 * roomLengthM / roomDepthM：房间东西长、南北深（米）
 */
export function fixturePlanStyle(
  fixture: RoomFixture,
  roomLengthM: number,
  roomDepthM: number,
): { left: string; top: string; width: string; height: string } {
  const wallLen = fixture.wall === 'N' || fixture.wall === 'S' ? roomLengthM : roomDepthM
  const safeLen = Math.max(0.01, wallLen)
  const start = Math.max(0, Math.min(safeLen, fixture.offsetM)) / safeLen
  const span = Math.max(0.04, Math.min(1 - start, fixture.widthM / safeLen))
  const thick = '12%'

  if (fixture.wall === 'N') {
    return { left: `${start * 100}%`, top: '0', width: `${span * 100}%`, height: thick }
  }
  if (fixture.wall === 'S') {
    return { left: `${start * 100}%`, top: `${100 - 12}%`, width: `${span * 100}%`, height: thick }
  }
  if (fixture.wall === 'W') {
    return { left: '0', top: `${start * 100}%`, width: thick, height: `${span * 100}%` }
  }
  return { left: `${100 - 12}%`, top: `${start * 100}%`, width: thick, height: `${span * 100}%` }
}
