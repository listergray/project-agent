export type LifeSquareId =
  | 'health'
  | 'career'
  | 'wealth'
  | 'family'
  | 'social'
  | 'learning'
  | 'leisure'
  | 'inner'
  | 'purpose'

export type LifeSquareDef = {
  id: LifeSquareId
  name: string
  prompt: string
  href: string
  hrefLabel: string
}

export const LIFE_SQUARES: LifeSquareDef[] = [
  {
    id: 'health',
    name: '健康',
    prompt: '作息、运动、饮食、体检、睡眠、精力',
    href: '/body',
    hrefLabel: '身体',
  },
  {
    id: 'career',
    name: '事业',
    prompt: '职业发展、收入、技能成长、工作成就感',
    href: '/assets/work',
    hrefLabel: '工作',
  },
  {
    id: 'wealth',
    name: '财富',
    prompt: '储蓄、投资、负债、被动收入、财务规划',
    href: '/assets/money',
    hrefLabel: '金钱',
  },
  {
    id: 'family',
    name: '家庭',
    prompt: '父母、伴侣、子女、家庭相处、亲情维护',
    href: '/people',
    hrefLabel: '交际',
  },
  {
    id: 'social',
    name: '社交',
    prompt: '朋友、圈子、人脉、社会连接',
    href: '/people',
    hrefLabel: '交际',
  },
  {
    id: 'learning',
    name: '学习',
    prompt: '知识学习、技能提升、认知迭代',
    href: '/assets/skills',
    hrefLabel: '技能',
  },
  {
    id: 'leisure',
    name: '闲趣',
    prompt: '兴趣、娱乐、旅行、放松、个人热爱',
    href: '/today',
    hrefLabel: '今日',
  },
  {
    id: 'inner',
    name: '心灵',
    prompt: '情绪稳定、内心幸福感、精神追求、价值观',
    href: '/body',
    hrefLabel: '身体',
  },
  {
    id: 'purpose',
    name: '自我实现',
    prompt: '理想、长期目标、价值输出、人生使命',
    href: '/goals',
    hrefLabel: '目标',
  },
]

export const SQUARE_LABELS: Record<LifeSquareId, string> = Object.fromEntries(
  LIFE_SQUARES.map((s) => [s.id, s.name]),
) as Record<LifeSquareId, string>

export const SCORE_HAN = ['未评', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
