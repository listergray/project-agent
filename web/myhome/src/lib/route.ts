import type { Goal, LifeSquare } from '../db'
import { db } from '../db'
import type { LifeSquareId } from './squares'

export const ROUTE_A = {
  key: 'ai-job',
  title: '全力求职',
  line: '优先拿下 AI 相关工作。入职之后，再备考北航软工非全。',
  why: [
    '立刻积累工业界 AI 实战履历。真实项目比自学 Demo 重一个量级。',
    '先有收入，经济独立，不必承担备考失败的空窗。',
    '在职仍可读非全日制。求职与读研不必二选一。',
  ],
}

export const ROUTE_A_GOALS: Array<
  Omit<Goal, 'createdAt'> & { createdAt?: number }
> = [
  {
    id: 'route-a-job',
    title: '拿下 AI 相关工作',
    horizon: 'year',
    status: 'active',
    square: 'career',
    note: '全力求职。工业界履历优先于自学 Demo。',
    targetDate: '',
  },
  {
    id: 'route-a-record',
    title: '用真实 AI 项目填履历',
    horizon: 'year',
    status: 'active',
    square: 'career',
    note: '入职后做的事，才是简历的主页。',
    targetDate: '',
  },
  {
    id: 'route-a-stand',
    title: '经济独立',
    horizon: 'year',
    status: 'active',
    square: 'wealth',
    note: '先有收入，再谈其余。',
    targetDate: '',
  },
  {
    id: 'route-a-beihang',
    title: '在职备考北航软工非全',
    horizon: 'decade',
    status: 'active',
    square: 'learning',
    note: '入职之后继续。求职与读研并行，不必二选一。',
    targetDate: '',
  },
]

export const ROUTE_A_SQUARES: Array<
  Pick<LifeSquare, 'id' | 'intention'> & { note: string }
> = [
  {
    id: 'career' as LifeSquareId,
    intention: '拿下 AI 相关工作，用工业界项目写履历。',
    note: '全力求职，不走备考空窗。',
  },
  {
    id: 'wealth' as LifeSquareId,
    intention: '先有工资，经济独立。',
    note: '收入先于备考的机会成本。',
  },
  {
    id: 'learning' as LifeSquareId,
    intention: '入职后备考北航软工非全。',
    note: '非全日制，与工作并行。',
  },
  {
    id: 'purpose' as LifeSquareId,
    intention: '工业界立足，再读非全，两条路合成一条。',
    note: '不必在求职与读研之间二选一。',
  },
]

export async function adoptRouteA() {
  const now = Date.now()
  await db.settings.update('main', {
    pathKey: ROUTE_A.key,
    pathTitle: ROUTE_A.title,
    pathLine: ROUTE_A.line,
  })

  for (const [i, goal] of ROUTE_A_GOALS.entries()) {
    const existing = await db.goals.get(goal.id)
    if (existing) {
      await db.goals.update(goal.id, {
        title: goal.title,
        horizon: goal.horizon,
        square: goal.square,
        note: goal.note,
      })
    } else {
      await db.goals.add({ ...goal, createdAt: now + i, status: 'active' })
    }
  }

  for (const cell of ROUTE_A_SQUARES) {
    const existing = await db.lifeSquares.get(cell.id)
    await db.lifeSquares.put({
      id: cell.id,
      score: existing?.score ?? 0,
      note: existing?.note || cell.note,
      intention: cell.intention,
      updatedAt: now,
    })
  }
}
