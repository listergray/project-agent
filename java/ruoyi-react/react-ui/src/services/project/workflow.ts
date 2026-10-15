import { request } from '@umijs/max';

export type PmHistoryItem = {
  at?: string;
  action?: string;
  by?: string;
  role?: string;
  note?: string;
};

export type PmProject = {
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
};

export type PmPageResult = { code: number; msg: string; rows: PmProject[]; total: number };
export type PmInfoResult = { code: number; msg: string; data: PmProject };

export const STATUS_LABEL: Record<string, string> = {
  draft: '草稿',
  pending_basic: '待一次审核',
  basic_passed: '一次审通过',
  pending_extend: '待二次审核',
  extend_passed: '二次审通过',
  pending_purchase: '购买联审中',
  pending_finance: '财务联审中',
  approved: '已立项通过',
};

export const PIPELINE_STEPS = [
  { key: 'basic', title: '基础信息' },
  { key: 'audit1', title: '一次审核' },
  { key: 'extend', title: '扩展信息' },
  { key: 'audit2', title: '二次审核' },
  { key: 'purchase', title: '购买联审' },
  { key: 'finance', title: '财务联审' },
];

export function statusToStepIndex(status?: string): number {
  switch (status) {
    case 'draft': return 0;
    case 'pending_basic': return 1;
    case 'basic_passed': return 2;
    case 'pending_extend': return 3;
    case 'extend_passed':
    case 'pending_purchase': return 4;
    case 'pending_finance': return 5;
    case 'approved': return 6;
    default: return 0;
  }
}

export async function getPmList(params?: { status?: string; keyword?: string; pageNum?: number; pageSize?: number }) {
  return request<PmPageResult>('/api/project/pm/list', { method: 'GET', params });
}
export async function getPmStats() {
  return request<{ code: number; msg: string; data: Record<string, number> }>('/api/project/pm/stats', { method: 'GET' });
}
export async function getPm(id: string) {
  return request<PmInfoResult>(`/api/project/pm/${id}`, { method: 'GET' });
}
export async function createBasic(data: PmProject) {
  return request<PmInfoResult>('/api/project/pm/basic', { method: 'POST', data });
}
export async function updateBasic(data: PmProject) {
  return request<PmInfoResult>('/api/project/pm/basic', { method: 'PUT', data });
}
export async function submitBasic(id: string) {
  return request<PmInfoResult>('/api/project/pm/basic/submit', { method: 'POST', data: { id } });
}
export async function updateExtend(data: PmProject) {
  return request<PmInfoResult>('/api/project/pm/extend', { method: 'PUT', data });
}
export async function submitExtend(id: string) {
  return request<PmInfoResult>('/api/project/pm/extend/submit', { method: 'POST', data: { id } });
}
export async function submitPurchase(id: string) {
  return request<PmInfoResult>('/api/project/pm/purchase/submit', { method: 'POST', data: { id } });
}
export async function reviewPm(data: {
  id: string;
  stage: 'basic' | 'extend' | 'purchase' | 'finance';
  action: 'approve' | 'reject';
  comment?: string;
}) {
  return request<PmInfoResult>('/api/project/pm/review', { method: 'POST', data });
}
