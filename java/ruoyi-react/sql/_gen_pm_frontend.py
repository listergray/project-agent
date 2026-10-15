# -*- coding: utf-8 -*-
"""Generate PM frontend files with Unicode escapes (ASCII-only source)."""
from pathlib import Path

ROOT = Path(r"E:/ai-pro/project_agent/java/ruoyi-react/react-ui/src")


def u(*codes):
    return "".join(chr(int(c, 16)) for c in codes)


def w(rel, text):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    assert text.encode("utf-8").decode("utf-8")
    print("wrote", rel)


# Chinese helpers
DRAFT = u("8349", "7a3f")
PENDING_BASIC = u("5f85", "4e00", "6b21", "5ba1", "6838")
BASIC_PASSED = u("4e00", "6b21", "5ba1", "901a", "8fc7")
PENDING_EXTEND = u("5f85", "4e8c", "6b21", "5ba1", "6838")
EXTEND_PASSED = u("4e8c", "6b21", "5ba1", "901a", "8fc7")
PENDING_PURCHASE = u("8d2d", "4e70", "8054", "5ba1", "4e2d")
PENDING_FINANCE = u("8d22", "52a1", "8054", "5ba1", "4e2d")
APPROVED = u("5df2", "7acb", "9879", "901a", "8fc7")
BASIC_INFO = u("57fa", "7840", "4fe1", "606f")
EXTEND_INFO = u("6269", "5c55", "4fe1", "606f")
AUDIT1 = u("4e00", "6b21", "5ba1", "6838")
AUDIT2 = u("4e8c", "6b21", "5ba1", "6838")
PURCHASE = u("8d2d", "4e70", "8054", "5ba1")
FINANCE = u("8d22", "52a1", "8054", "5ba1")
LEDGER = u("9879", "76ee", "53f0", "8d26")
PIPELINE = u("5168", "56fd", "516c", "7528", "7acb", "9879", "6d41", "6c34", "7ebf")
ROLE_SPLIT = u("5206", "5c97", "8054", "5ba1")

w(
    "services/project/workflow.ts",
    f"""import {{ request }} from '@umijs/max';

export type PmHistoryItem = {{
  at?: string;
  action?: string;
  by?: string;
  role?: string;
  note?: string;
}};

export type PmProject = {{
  id?: string;
  projectCode?: string;
  projectName?: string;
  projectType?: string;
  owner?: string;
  department?: string;
  budget?: number;
  startDate?: string;
  endDate?: string;
  description?: string;
  goals?: string;
  members?: string;
  riskLevel?: string;
  priority?: string;
  purchasePlan?: string;
  financePlan?: string;
  status?: string;
  createdBy?: string;
  createdAt?: string;
  updatedAt?: string;
  history?: PmHistoryItem[];
}};

export type PmPageResult = {{ code: number; msg: string; rows: PmProject[]; total: number }};
export type PmInfoResult = {{ code: number; msg: string; data: PmProject }};

export const STATUS_LABEL: Record<string, string> = {{
  draft: '{DRAFT}',
  pending_basic: '{PENDING_BASIC}',
  basic_passed: '{BASIC_PASSED}',
  pending_extend: '{PENDING_EXTEND}',
  extend_passed: '{EXTEND_PASSED}',
  pending_purchase: '{PENDING_PURCHASE}',
  pending_finance: '{PENDING_FINANCE}',
  approved: '{APPROVED}',
}};

export const PIPELINE_STEPS = [
  {{ key: 'basic', title: '{BASIC_INFO}' }},
  {{ key: 'audit1', title: '{AUDIT1}' }},
  {{ key: 'extend', title: '{EXTEND_INFO}' }},
  {{ key: 'audit2', title: '{AUDIT2}' }},
  {{ key: 'purchase', title: '{PURCHASE}' }},
  {{ key: 'finance', title: '{FINANCE}' }},
];

export function statusToStepIndex(status?: string): number {{
  switch (status) {{
    case 'draft': return 0;
    case 'pending_basic': return 1;
    case 'basic_passed': return 2;
    case 'pending_extend': return 3;
    case 'extend_passed':
    case 'pending_purchase': return 4;
    case 'pending_finance': return 5;
    case 'approved': return 6;
    default: return 0;
  }}
}}

export async function getPmList(params?: {{ status?: string; keyword?: string; pageNum?: number; pageSize?: number }}) {{
  return request<PmPageResult>('/api/project/pm/list', {{ method: 'GET', params }});
}}
export async function getPmStats() {{
  return request<{{ code: number; msg: string; data: Record<string, number> }}>('/api/project/pm/stats', {{ method: 'GET' }});
}}
export async function getPm(id: string) {{
  return request<PmInfoResult>(`/api/project/pm/${{id}}`, {{ method: 'GET' }});
}}
export async function createBasic(data: PmProject) {{
  return request<PmInfoResult>('/api/project/pm/basic', {{ method: 'POST', data }});
}}
export async function updateBasic(data: PmProject) {{
  return request<PmInfoResult>('/api/project/pm/basic', {{ method: 'PUT', data }});
}}
export async function submitBasic(id: string) {{
  return request<PmInfoResult>('/api/project/pm/basic/submit', {{ method: 'POST', data: {{ id }} }});
}}
export async function updateExtend(data: PmProject) {{
  return request<PmInfoResult>('/api/project/pm/extend', {{ method: 'PUT', data }});
}}
export async function submitExtend(id: string) {{
  return request<PmInfoResult>('/api/project/pm/extend/submit', {{ method: 'POST', data: {{ id }} }});
}}
export async function submitPurchase(id: string) {{
  return request<PmInfoResult>('/api/project/pm/purchase/submit', {{ method: 'POST', data: {{ id }} }});
}}
export async function reviewPm(data: {{
  id: string;
  stage: 'basic' | 'extend' | 'purchase' | 'finance';
  action: 'approve' | 'reject';
  comment?: string;
}}) {{
  return request<PmInfoResult>('/api/project/pm/review', {{ method: 'POST', data }});
}}
""",
)

# Ledger - keep functional UI text via helpers
T_ALL = u("5168", "90e8")
T_PASS = u("5df2", "901a", "8fc7")
T_NAME = u("9879", "76ee", "540d", "79f0")
T_CODE = u("9879", "76ee", "7f16", "53f7")
T_TYPE = u("7c7b", "578b")
T_OWNER = u("8d1f", "8d23", "4eba")
T_DEPT = u("90e8", "95e8")
T_BUDGET = u("9884", "7b97") + "(?)"
# yuan char
T_BUDGET = u("9884", "7b97") + "(" + u("5143") + ")"
T_STATUS = u("72b6", "6001")
T_PIPE = u("6d41", "6c34", "7ebf")
T_UPDATED = u("66f4", "65b0", "65f6", "95f4")
T_DETAIL = u("9879", "76ee", "8be6", "60c5")
T_HISTORY = u("6d41", "8f6c", "5386", "53f2")
T_PROJECTS = u("7acb", "9879", "9879", "76ee")

w(
    "pages/Project/Ledger/index.tsx",
    f"""import React, {{ useEffect, useMemo, useRef, useState }} from 'react';
import {{ PageContainer, ProColumns, ProTable, ActionType }} from '@ant-design/pro-components';
import {{ Drawer, Steps, Tag, Timeline, Typography, Statistic, Row, Col, Card, Space }} from 'antd';
import {{
  getPmList, getPmStats, getPm, PmProject, STATUS_LABEL, PIPELINE_STEPS, statusToStepIndex,
}} from '@/services/project/workflow';

const statusColor = (status?: string) => {{
  switch (status) {{
    case 'draft': return 'default';
    case 'pending_basic':
    case 'pending_extend':
    case 'pending_purchase':
    case 'pending_finance': return 'processing';
    case 'basic_passed':
    case 'extend_passed': return 'cyan';
    case 'approved': return 'success';
    default: return 'default';
  }}
}};

const LedgerPage: React.FC = () => {{
  const actionRef = useRef<ActionType>();
  const [stats, setStats] = useState<Record<string, number>>({{}});
  const [detail, setDetail] = useState<PmProject | null>(null);
  const [open, setOpen] = useState(false);

  const loadStats = async () => {{
    const res = await getPmStats();
    if (res.code === 200) setStats(res.data || {{}});
  }};

  useEffect(() => {{ loadStats(); }}, []);

  const columns: ProColumns<PmProject>[] = useMemo(() => [
    {{ title: '{T_CODE}', dataIndex: 'projectCode', width: 150, copyable: true }},
    {{
      title: '{T_NAME}',
      dataIndex: 'projectName',
      ellipsis: true,
      render: (_, row) => (
        <a onClick={{async () => {{
          const res = await getPm(row.id!);
          if (res.code === 200) {{ setDetail(res.data); setOpen(true); }}
        }}}}>{{row.projectName}}</a>
      ),
    }},
    {{ title: '{T_TYPE}', dataIndex: 'projectType', width: 90, search: false }},
    {{ title: '{T_OWNER}', dataIndex: 'owner', width: 90 }},
    {{ title: '{T_DEPT}', dataIndex: 'department', width: 110, search: false }},
    {{ title: '{T_BUDGET}', dataIndex: 'budget', width: 110, search: false }},
    {{
      title: '{T_STATUS}',
      dataIndex: 'status',
      width: 120,
      valueType: 'select',
      valueEnum: Object.fromEntries(Object.entries(STATUS_LABEL).map(([k, v]) => [k, {{ text: v }}])),
      render: (_, row) => <Tag color={{statusColor(row.status)}}>{{STATUS_LABEL[row.status || ''] || row.status}}</Tag>,
    }},
    {{
      title: '{T_PIPE}',
      dataIndex: 'pipeline',
      search: false,
      width: 320,
      render: (_, row) => {{
        const idx = statusToStepIndex(row.status);
        return (
          <Steps size="small" current={{Math.min(idx, 5)}} items={{PIPELINE_STEPS.map((s, i) => ({{
            title: s.title,
            status: idx > i || idx === 6 ? 'finish' : idx === i ? 'process' : 'wait',
          }}))}} />
        );
      }},
    }},
    {{ title: '{T_UPDATED}', dataIndex: 'updatedAt', width: 160, search: false }},
  ], []);

  return (
    <PageContainer header={{{{ title: '{LEDGER}', subTitle: '{PIPELINE} / {ROLE_SPLIT}' }}}}>
      <Row gutter={{16}} style={{{{ marginBottom: 16 }}}}>
        {{[
          {{ key: 'total', title: '{T_ALL}' }},
          {{ key: 'pending_basic', title: '{PENDING_BASIC}' }},
          {{ key: 'pending_extend', title: '{PENDING_EXTEND}' }},
          {{ key: 'pending_purchase', title: '{PURCHASE}' }},
          {{ key: 'pending_finance', title: '{FINANCE}' }},
          {{ key: 'approved', title: '{T_PASS}' }},
        ].map((item) => (
          <Col key={{item.key}} xs={{12}} sm={{8}} md={{4}}>
            <Card size="small"><Statistic title={{item.title}} value={{stats[item.key] || 0}} /></Card>
          </Col>
        ))}}
      </Row>
      <ProTable<PmProject>
        headerTitle="{T_PROJECTS}"
        actionRef={{actionRef}}
        rowKey="id"
        columns={{columns}}
        search={{{{ labelWidth: 'auto' }}}}
        request={{async (params) => {{
          const res = await getPmList({{
            status: params.status,
            keyword: params.projectName || params.projectCode || params.owner,
            pageNum: params.current,
            pageSize: params.pageSize,
          }});
          loadStats();
          return {{ data: res.rows || [], total: res.total || 0, success: res.code === 200 }};
        }}}}
        pagination={{{{ defaultPageSize: 10 }}}}
      />
      <Drawer width={{560}} title={{detail?.projectName || '{T_DETAIL}'}} open={{open}} onClose={{() => setOpen(false)}} destroyOnClose>
        {{detail && (
          <Space direction="vertical" size="large" style={{{{ width: '100%' }}}}>
            <div>
              <Tag color={{statusColor(detail.status)}}>{{STATUS_LABEL[detail.status || '']}}</Tag>
              <Typography.Text type="secondary" style={{{{ marginLeft: 8 }}}}>{{detail.projectCode}}</Typography.Text>
            </div>
            <Steps direction="vertical" size="small" current={{Math.min(statusToStepIndex(detail.status), 5)}} items={{PIPELINE_STEPS.map((s) => ({{ title: s.title }}))}} />
            <Typography.Paragraph>
              <strong>{T_OWNER}:</strong>{{detail.owner || '-'}} <strong>{T_DEPT}:</strong>{{detail.department || '-'}}
              <br /><strong>{T_BUDGET}:</strong>{{detail.budget ?? '-'}} <strong>{T_TYPE}:</strong>{{detail.projectType || '-'}}
              <br /><strong>{u("6982","8ff0")}:</strong>{{detail.description || '-'}}
              <br /><strong>{u("76ee","6807","4ea4","4ed8")}:</strong>{{detail.goals || '-'}}
              <br /><strong>{u("91c7","8d2d","8bf4","660e")}:</strong>{{detail.purchasePlan || '-'}}
              <br /><strong>{u("8d44","91d1","8bf4","660e")}:</strong>{{detail.financePlan || '-'}}
            </Typography.Paragraph>
            <Typography.Title level={{5}}>{T_HISTORY}</Typography.Title>
            <Timeline items={{(detail.history || []).slice().reverse().map((h) => ({{
              children: (
                <div>
                  <div>{{h.action}} / {{h.by}}{{h.role ? ` (${{h.role}})` : ''}}</div>
                  <Typography.Text type="secondary">{{h.at}} {{h.note ? `/ ${{h.note}}` : ''}}</Typography.Text>
                </div>
              ),
            }}))}} />
          </Space>
        )}}
      </Drawer>
    </PageContainer>
  );
}};

export default LedgerPage;
""",
)

print("ledger+service done")
