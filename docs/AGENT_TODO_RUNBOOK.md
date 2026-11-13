# Agent 待办队列（SuperAgent 轻量版）

灵感来自 DeepSeek **Router / Worker** 原型：本仓库用 **YAML 队列 + 定时 Cursor Agent + Task 子 Agent** 实现，非常驻进程。

## 文件

| 路径 | 作用 |
|------|------|
| [TODO_AGENT_QUEUE.yaml](TODO_AGENT_QUEUE.yaml) | 唯一待办源 |
| [AGENT_TODO_TICK.md](AGENT_TODO_TICK.md) | 每次定时 tick 的完整指令（已入库，供云端 Automation 读取） |
| `.cursor/prompts/agent-todo-tick.md` | 本机会话 tick 用（目录被 gitignore，与上文件保持同步） |
| `.cursor/automations/agent-todo-scan.prompt.md` | 本地 Automation 粘贴草稿（gitignore） |

## 网页维护（推荐）

门户应用空间卡片 **「任务待办」** → `/portal/todo`（需登录）。

- 新建默认为 `pending`（只排队）
- 点 **批准执行** → `approved`，下一次扫描才会跑
- 与 YAML 为**同一文件**；网页保存后 Cursor Automation / 会话 tick 立刻能读到

## 添加待办

也可直接在 `TODO_AGENT_QUEUE.yaml` 的 `items` 下追加：

```yaml
- id: todo-YYYYMMDD-slug
  title: 简短标题
  kind: qa          # qa | docs | douyin | video | deploy | production | data_migrate | general
  assignee_agent: qa-tester   # 见下方子 Agent 表
  status: pending   # pending → approved → in_progress → done | failed | cancelled
  priority: 5       # 越大越先
  created_at: "2026-11-09T12:00:00+08:00"
  payload:
    instruction: 给 Worker 的具体说明
  notes: ""
  result: ""
  updated_at: ""
```

- **pending**：只登记，不执行。
- **approved**：下一次 tick 可认领（`deploy` / `production` / `data_migrate` 必须 approved）。
- 执行前主 Agent 将 `status` 改为 **in_progress**，结束后写 **done** 或 **failed**，并在 `result` 填摘要（≤2000 字），`updated_at` 为 ISO 时间。

## 子 Agent 路由

| assignee_agent | 岗位 | 适用 |
|----------------|------|------|
| `director` | 总监 | 方向、取舍、优先级 |
| `tech-lead` | 总技术工程师 | 架构、技术边界、风险 |
| `project-manager` | 项目经理 | 关键节点、进度、阻塞 |
| `finance` | 财务 | 投入时间、每月费用 |
| `ui-designer` | UI设计师 | 界面、规范、移动端 |
| `qa-tester` | 测试人员 | 用例、冒烟、验收、缺陷 |
| `long-video` | 长视频员工 | 中长视频选题/分镜/animation-pro |
| `explore` | 摸底调研 | 只读搜代码、摸底 |
| `generalPurpose` | 实施助手 | 多步实施、文档、配置 |

派工方式：主 Agent 在本会话用 **Task**，`subagent_type` 与上表一致；`description` 写明队列 `id` 与 `payload`。

## 定时扫描（推荐：Cursor Automation）

1. Cursor → **Automations** → 新建。
2. **Trigger**：Schedule，例如每 **30 分钟**（或 `0 9,14,20 * * *` 每天三次）。
3. **Repository**：`project_agent`，分支当前常用分支。
4. **Instructions**：执行 [AGENT_TODO_TICK.md](AGENT_TODO_TICK.md)（或粘贴 Automation 草稿正文，逻辑须与 tick 一致）。
5. 启用 **Task** 子 Agent（若 UI 可选工具/Agent）。
6. 保存后先 **Run once** 试跑。

云 Automation 无法操作本机 `:12500` Playwright 时，相关事项标 **failed** 并在 `result` 写明「需本机 Agent」。

## 本机会话替代：/loop

在已打开的本仓库 Chat 中：

```text
/loop 30m 执行 agent-todo-tick：读取 docs/TODO_AGENT_QUEUE.yaml，按 docs/AGENT_TODO_TICK.md 处理最多 3 条 approved 待办
```

详见 Cursor skill `loop`（仅本地会话有效）。

## 主 Agent 每 tick 摘要（逻辑）

1. 读取 `docs/TODO_AGENT_QUEUE.yaml`。
2. 筛选 `status: approved`（且 kind 不在 `require_approval_kinds` 时仍为 approved；在名单内也必须已是 approved）。
3. 按 `priority` 降序，最多 `defaults.max_per_tick` 条。
4. 每条：改 `in_progress` → Task 子 Agent → 写回 `done`/`failed` + `result`。
5. 若有实质结论，在 [PROJECT_MAP.md](../PROJECT_MAP.md) **变更记录** 加一行（可选，重大项必加）。

## 安全

- 队列中不写密码、Cookie、API Key。
- `production` / `data_migrate` 类必须在 `notes` 里写回滚方式，且保持 **approved** 人工确认。
