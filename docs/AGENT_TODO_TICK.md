# Agent 待办 tick（主 Agent / Router）

你是一次 **定时扫描** 的主 Agent。严格执行下列步骤，用简体中文汇报。

**数据源：HTTP 接口（与门户 `/portal/todo` 同一后端）**，不要只读 Git 仓库里的 YAML 快照。

## 0. 基址

按顺序选用第一个可达的基址（后面路径以 `/agent/todo` 开头）：

1. `https://geime.fun/gw/ruoyi`
2. `http://127.0.0.1:8088`
3. 若环境变量 / 密钥里有 `AGENT_TODO_BASE`，优先用它（勿打印密钥）

接口 **不鉴权**。写回必须走接口，保证门户立刻看到状态。

## 1. 拉取待执行

```http
GET {BASE}/agent/todo/list?status=approved
```

解析 JSON：`data.defaults.max_per_tick`、`data.items`。

- 只处理 `status === "approved"`
- 按 `priority` 降序
- 取前 `max_per_tick` 条（缺省 3）

若无条目：回复「本 tick 无 approved 待办」并结束。

## 2. 逐条执行

对每条 `item`：

1. 认领：
   ```http
   PUT {BASE}/agent/todo/{id}/status
   Content-Type: application/json
   {"status":"in_progress"}
   ```
2. 调用 **Task** 子 Agent：
   - `subagent_type` = `item.assignee_agent`（仅允许：director、tech-lead、project-manager、finance、ui-designer、qa-tester、long-video、explore、generalPurpose）
   - 描述含：`id`、`title`、完整 `payload`，要求返回可写入 `result` 的摘要（≤2000 字）
3. 写回结果：
   ```http
   PUT {BASE}/agent/todo
   Content-Type: application/json
   {
     "id": "<id>",
     "status": "done|failed",
     "result": "<摘要+证据>"
   }
   ```

## 3. 收尾

- 向用户简短汇报：处理了哪些 `id`、结论如何
- 若涉及外网/架构变更：在 `PROJECT_MAP.md` 变更记录追加一行（事实 + 日期），并尽量提交

## 禁止

- 不要执行 `pending` / `cancelled`
- 不要未经 approved 执行 `deploy` / `production` / `data_migrate`
- 不要将密钥写入 `result` / 仓库
- 本机专属（Playwright、扫码、本机端口）云环境做不到 → `failed`，`result` 写明「需本机 IDE Agent」
