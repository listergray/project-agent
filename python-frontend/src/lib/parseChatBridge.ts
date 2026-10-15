export type ParseGapItem = {
  key: string
  label: string
  required: boolean
  kind: 'text' | 'textarea' | 'number' | 'select'
  options?: { label: string; value: string }[]
  placeholder?: string
  value?: string
}

export const PARSE_GAP_FIELD_META: ParseGapItem[] = [
  { key: 'project_code', label: '项目编号', required: false, kind: 'text', placeholder: 'PRJ-2026-001' },
  { key: 'project_name', label: '项目名称', required: true, kind: 'text' },
  {
    key: 'project_type',
    label: '项目类型',
    required: false,
    kind: 'select',
    options: [
      { label: '研发', value: 'rd' },
      { label: '产品', value: 'product' },
      { label: '运维', value: 'ops' },
      { label: '其他', value: 'other' },
    ],
  },
  {
    key: 'priority',
    label: '优先级',
    required: false,
    kind: 'select',
    options: [
      { label: 'P0', value: 'P0' },
      { label: 'P1', value: 'P1' },
      { label: 'P2', value: 'P2' },
      { label: 'P3', value: 'P3' },
    ],
  },
  { key: 'budget', label: '预算（元）', required: false, kind: 'number' },
  { key: 'owner_name', label: '负责人', required: false, kind: 'text' },
  { key: 'department', label: '所属部门', required: false, kind: 'text' },
  { key: 'start_date', label: '计划开始', required: false, kind: 'text', placeholder: 'YYYY-MM-DD' },
  { key: 'end_date', label: '计划结束', required: false, kind: 'text', placeholder: 'YYYY-MM-DD' },
  { key: 'description', label: '项目描述', required: false, kind: 'textarea' },
  { key: 'objectives', label: '项目目标', required: false, kind: 'textarea' },
  { key: 'scope', label: '项目范围', required: false, kind: 'textarea' },
]

function isFieldEmpty(fields: Record<string, unknown>, key: string): boolean {
  const v = fields[key]
  if (v === undefined || v === null) return true
  if (typeof v === 'string') return !v.trim()
  if (typeof v === 'number') return Number.isNaN(v)
  return false
}

/** Collect empty form fields for chat gap-fill UI. */
export function collectParseGaps(fields: object): ParseGapItem[] {
  const rec = fields as Record<string, unknown>
  return PARSE_GAP_FIELD_META.filter((m) => isFieldEmpty(rec, m.key))
}

/** Build assistant summary markdown after document parse. */
export function buildParseSummary(opts: {
  filename: string
  method?: string
  confidence?: number
  fields: object
  gaps: ParseGapItem[]
}): string {
  const conf = Math.round((opts.confidence || 0) * 100)
  const nl = String.fromCharCode(10)
  const rec = opts.fields as Record<string, unknown>
  const filled = PARSE_GAP_FIELD_META.filter((m) => !isFieldEmpty(rec, m.key))
    .map((m) => {
      const raw = rec[m.key]
      const show = typeof raw === 'number' ? String(raw) : String(raw).slice(0, 40)
      return '- ' + m.label + '：' + show
    })
    .join(nl)

  const missing = opts.gaps.length
    ? opts.gaps.map((g) => '- ' + g.label + (g.required ? '（必填）' : '')).join(nl)
    : '- （关键字段已齐，可直接核对表单后提交）'

  const head =
    '已根据文档「' +
    opts.filename +
    '」完成解析回填（方式 ' +
    (opts.method || '—') +
    '，置信度 ' +
    conf +
    '%）。'
  const filledBlock = filled || '- （较少字段，请人工核对）'
  const tail = opts.gaps.length
    ? '请在下方补全待填项，确认后会写回左侧立项表单。'
    : '表单关键字段已基本齐全，请在左侧再人工确认后提交。'
  return [head, '', '### 已识别', filledBlock, '', '### 待补全', missing, '', tail].join(nl)
}
