export const ASSET_KINDS = [
  {
    id: 'money',
    name: '金钱',
    hint: '现金、存款、投资与债权。',
  },
  {
    id: 'digital',
    name: '数字',
    hint: '账号、域名、加密货币、软件许可、订阅与数字藏品。',
  },
  {
    id: 'things',
    name: '实物',
    hint: '房子、车子、收藏与用着的东西。',
  },
  {
    id: 'skills',
    name: '技能',
    hint: '技术、语言、手艺、职业能力。记下程度与凭据。',
  },
  {
    id: 'work',
    name: '工作',
    hint: '任职、项目与独立工作。一条记录写清时段、角色和做了什么。',
  },
] as const

export type AssetKindId = (typeof ASSET_KINDS)[number]['id']

export function isAssetKind(value: string | undefined): value is AssetKindId {
  return ASSET_KINDS.some((item) => item.id === value)
}
