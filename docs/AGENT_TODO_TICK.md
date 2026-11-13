# Agent 待办 tick（主 Agent / Router）

你是一次 **定时扫描** 的主 Agent。严格执行下列步骤，用简体中文写回仓库。

## 1. 读取队列

- 文件：仓库内 `docs/TODO_AGENT_QUEUE.yaml`（与门户「任务待办」同一文件）
- 解析 `defaults.max_per_tick` 与 `defaults.require_approval_kinds`

## 2. 筛选待执行

- `status` 必须为 `approved`
- 按 `priority` 降序排序
- 取前 `max_per_tick` 条（默认 3）

若无条目：回复「本 tick 无 approved 待办」并结束。

## 3. 逐条执行

对每条 `item`：

1. 将 `status` 更新为 `in_progress`，`updated_at` 为当前时间（ISO8601 +08:00），写回 YAML。
2. 调用 **Task** 子 Agent：
   - `subagent_type` = `item.assignee_agent`（仅允许：director、tech-lead、project-manager、finance、ui-designer、qa-tester、long-video、explore、generalPurpose）
   - 任务描述含：`id`、`title`、完整 `payload`，并要求子 Agent 返回可写入 `result` 的摘要
3. 根据子 Agent 结果：
   - 成功 → `status: done`
   - 失败或阻塞 → `status: failed`
   - `result`：摘要 + 证据路径（日志、URL、命令输出）
   - 更新 `updated_at`
4. 写回 `docs/TODO_AGENT_QUEUE.yaml`（保持 UTF-8，勿删其它条目）

## 4. 收尾

- 向用户简短汇报：处理了哪些 `id`、结论如何
- 若涉及外网/架构变更：在 `PROJECT_MAP.md` 变更记录追加一行（事实 + 日期）

## 禁止

- 不要执行 `status: pending` 或 `cancelled` 的项
- 不要未经 approved 执行 `deploy` / `production` / `data_migrate`
- 不要将密钥写入 YAML
