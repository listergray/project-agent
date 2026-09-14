/**
 * 零依赖启动入口（npm 不可用时仍可演示项目管理 HTTP API）
 * 完整 Nest 开发：npm i && npm run start:dev
 */
import http from 'http';
import fs from 'fs';
import path from 'path';
import { randomUUID } from 'crypto';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.PORT || 48080);
const DATA_DIR = path.join(__dirname, 'data');
const FILE = path.join(DATA_DIR, 'projects.json');

function nowIso() {
  return new Date().toISOString().replace('T', ' ').slice(0, 19);
}
function ok(data) {
  return JSON.stringify({ code: 0, data, msg: 'success' });
}
function fail(msg, code = 400) {
  return JSON.stringify({ code, data: null, msg });
}
function load() {
  if (!fs.existsSync(FILE)) return [];
  try {
    const raw = JSON.parse(fs.readFileSync(FILE, 'utf8') || '[]');
    return Array.isArray(raw) ? raw : [];
  } catch {
    return [];
  }
}
function save(rows) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
  fs.writeFileSync(FILE, JSON.stringify(rows, null, 2), 'utf8');
}
function toVo(e) {
  return {
    id: e.id,
    status: e.status,
    projectCode: e.projectCode || '',
    projectName: e.projectName || '',
    projectType: e.projectType || '研发',
    owner: e.owner || '',
    department: e.department || '',
    sponsor: e.sponsor || '',
    startDate: e.startDate || '',
    endDate: e.endDate || '',
    budget: Number(e.budget || 0),
    priority: e.priority || 'P1',
    riskLevel: e.riskLevel || '中',
    members: e.members || '',
    description: e.description || '',
    goals: e.goals || '',
    sourceFile: e.sourceFile || '',
    remark: e.remark || '',
    createdBy: e.createdBy || '申请人',
    reviewer: e.reviewer || '',
    reviewComment: e.reviewComment || '',
    ragItemPk: e.ragItemPk || null,
    submittedAt: e.submittedAt || null,
    reviewedAt: e.reviewedAt || null,
    history: Array.isArray(e.history) ? e.history : [],
    createTime: e.createTime,
    updateTime: e.updateTime,
  };
}
function applyBody(e, body) {
  for (const k of [
    'projectCode', 'projectName', 'projectType', 'owner', 'department', 'sponsor',
    'startDate', 'endDate', 'budget', 'priority', 'riskLevel', 'members',
    'description', 'goals', 'sourceFile', 'remark', 'createdBy',
  ]) {
    if (body[k] !== undefined && body[k] !== null) e[k] = body[k];
  }
}
function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', (c) => chunks.push(c));
    req.on('end', () => {
      const raw = Buffer.concat(chunks).toString('utf8');
      if (!raw) return resolve({});
      try {
        resolve(JSON.parse(raw));
      } catch (e) {
        reject(e);
      }
    });
  });
}

const server = http.createServer(async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,PUT,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    return res.end();
  }

  const url = new URL(req.url || '/', `http://127.0.0.1:${PORT}`);
  const p = url.pathname;
  const send = (code, body) => {
    res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(body);
  };

  try {
    if (req.method === 'GET' && p === '/admin-api/project-agent/project/page') {
      let rows = load();
      const status = url.searchParams.get('status');
      if (status) rows = rows.filter((x) => x.status === status);
      const q = (url.searchParams.get('q') || '').trim().toLowerCase();
      if (q) {
        rows = rows.filter((x) => {
          const hay = `${x.projectName || ''} ${x.projectCode || ''} ${x.owner || ''}`.toLowerCase();
          return hay.includes(q);
        });
      }
      const pageNoRaw = url.searchParams.get('pageNo');
      const pageSizeRaw = url.searchParams.get('pageSize');
      let list = rows;
      if (pageNoRaw != null || pageSizeRaw != null) {
        const pageNo = Math.max(1, Number(pageNoRaw || 1) || 1);
        const pageSize = Math.max(1, Number(pageSizeRaw || 500) || 500);
        const start = (pageNo - 1) * pageSize;
        list = rows.slice(start, start + pageSize);
      }
      return send(200, ok({ list: list.map(toVo), total: rows.length }));
    }
    if (req.method === 'GET' && p === '/admin-api/project-agent/project/get') {
      const id = url.searchParams.get('id');
      const e = load().find((x) => x.id === id);
      return send(200, ok(e ? toVo(e) : null));
    }
    if (req.method === 'GET' && p === '/admin-api/project-agent/project/stats') {
      const rows = load();
      const out = { draft: 0, pending: 0, approved: 0, rejected: 0, total: rows.length };
      for (const x of rows) if (x.status in out) out[x.status] += 1;
      return send(200, ok(out));
    }
    if (req.method === 'POST' && p === '/admin-api/project-agent/project/create') {
      const body = await readBody(req);
      const rows = load();
      const e = {
        id: `prj_${randomUUID().replace(/-/g, '').slice(0, 12)}`,
        status: 'draft',
        history: [],
        createTime: nowIso(),
        updateTime: nowIso(),
      };
      applyBody(e, body);
      e.history = [{ at: nowIso(), action: 'created', by: e.createdBy || '申请人', note: '创建立项草稿' }];
      rows.push(e);
      save(rows);
      return send(200, ok(e.id));
    }
    if (req.method === 'PUT' && p === '/admin-api/project-agent/project/update') {
      const body = await readBody(req);
      const rows = load();
      const idx = rows.findIndex((x) => x.id === body.id);
      if (idx < 0) return send(200, fail('项目不存在', 404));
      if (!['draft', 'rejected'].includes(rows[idx].status)) return send(200, fail('仅草稿/驳回可编辑'));
      applyBody(rows[idx], body);
      rows[idx].history = [...(rows[idx].history || []), { at: nowIso(), action: 'updated', by: '申请人', note: '更新草稿' }];
      rows[idx].updateTime = nowIso();
      save(rows);
      return send(200, ok(true));
    }
    if (req.method === 'POST' && p === '/admin-api/project-agent/project/submit') {
      const id = url.searchParams.get('id');
      const rows = load();
      const idx = rows.findIndex((x) => x.id === id);
      if (idx < 0) return send(200, fail('项目不存在', 404));
      rows[idx].status = 'pending';
      rows[idx].submittedAt = nowIso();
      rows[idx].updateTime = nowIso();
      rows[idx].history = [...(rows[idx].history || []), { at: rows[idx].submittedAt, action: 'submitted', by: '申请人', note: '提交审批' }];
      save(rows);
      return send(200, ok(true));
    }
    if (req.method === 'POST' && p === '/admin-api/project-agent/project/review') {
      const body = await readBody(req);
      const rows = load();
      const idx = rows.findIndex((x) => x.id === body.id);
      if (idx < 0) return send(200, fail('项目不存在', 404));
      const action = String(body.action || '').toLowerCase();
      if (!['approve', 'reject'].includes(action)) return send(200, fail('action 须为 approve|reject'));
      rows[idx].status = action === 'approve' ? 'approved' : 'rejected';
      rows[idx].reviewer = body.reviewer || '审批人';
      rows[idx].reviewComment = body.comment || '';
      rows[idx].reviewedAt = nowIso();
      rows[idx].updateTime = nowIso();
      rows[idx].history = [
        ...(rows[idx].history || []),
        { at: rows[idx].reviewedAt, action: action === 'approve' ? 'approved' : 'rejected', by: rows[idx].reviewer, note: rows[idx].reviewComment },
      ];
      save(rows);
      return send(200, ok(true));
    }
    if (req.method === 'PUT' && p === '/admin-api/project-agent/project/rag-item-pk') {
      const id = url.searchParams.get('id');
      const ragItemPk = url.searchParams.get('ragItemPk');
      const rows = load();
      const idx = rows.findIndex((x) => x.id === id);
      if (idx < 0) return send(200, fail('项目不存在', 404));
      rows[idx].ragItemPk = ragItemPk;
      rows[idx].updateTime = nowIso();
      save(rows);
      return send(200, ok(true));
    }
    send(404, fail('not found', 404));
  } catch (e) {
    send(500, fail(String(e && e.message ? e.message : e), 500));
  }
});

fs.mkdirSync(DATA_DIR, { recursive: true });
if (!fs.existsSync(FILE)) save([]);
server.listen(PORT, () => {
  console.log(`[ruoyi-react/server] lite API → http://127.0.0.1:${PORT}`);
});
