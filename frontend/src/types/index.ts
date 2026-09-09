export type ProjectStatus = 'draft' | 'pending' | 'approved' | 'rejected'

export interface ProjectFields {
  project_code: string
  project_name: string
  project_type: string
  owner: string
  department: string
  sponsor: string
  start_date: string
  end_date: string
  budget: number
  priority: string
  risk_level: string
  members: string
  description: string
  goals: string
  source_file: string
  remark: string
}

export interface ProjectHistory {
  at: string
  action: string
  by: string
  note?: string
}

export interface ProjectRecord extends ProjectFields {
  id: string
  status: ProjectStatus
  created_at: string
  updated_at: string
  submitted_at?: string | null
  reviewed_at?: string | null
  reviewer: string
  review_comment: string
  created_by: string
  parse_confidence?: number | null
  rag_item_pk?: string | null
  rag_synced?: boolean
  rag_error?: string
  history: ProjectHistory[]
}

export interface ProjectStats {
  total: number
  draft: number
  pending: number
  approved: number
  rejected: number
}

export interface HealthResp {
  liveness: boolean
  readiness: boolean
  milvus?: {
    kb_chunks?: number
    kb_item_names?: number
    error?: string
  }
  trace_id?: string
}

export interface ChatResp {
  session_id: string
  answer: string
  sources: string[]
  tool_calls: Array<Record<string, unknown>>
  intent: string
  elapsed_ms: number
  need_rag?: boolean | null
  self_rag_route_reason?: string | null
  self_rag_retries?: number
  self_rag_grade?: Record<string, unknown> | null
  multi_queries?: string[]
  retrieval_paths?: Record<string, unknown> | null
  faithfulness_score?: number | null
  faithfulness?: Record<string, unknown> | null
  interrupted?: boolean
  interrupt_payload?: Record<string, unknown> | null
  need_human_review?: boolean
}

export interface CopilotResp {
  output_dir: string
  steps_done: string[]
  files: Array<{ path: string; size_bytes: number }>
  total_cost_ms: number
  errors: string[]
}

export const emptyProjectFields = (): ProjectFields => ({
  project_code: '',
  project_name: '',
  project_type: '研发',
  owner: '',
  department: '',
  sponsor: '',
  start_date: '',
  end_date: '',
  budget: 0,
  priority: 'P1',
  risk_level: '中',
  members: '',
  description: '',
  goals: '',
  source_file: '',
  remark: '',
})
