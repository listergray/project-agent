# 混合架构：Java 业务微服务 + Python AI 编排

> 目标形态：**项目库等基础业务** 由 Java（推荐 [芋道](https://doc.iocoder.cn/)）承载；**涉及 AI 的能力** 落在本仓 Python（LangGraph / LCEL 节点链 / RAG / HITL）。

## 1. 职责切分

| 域 | 实现 | 内容 |
| --- | --- | --- |
| 项目库 CRUD / 审批 | `java/_nest-biz-stub/`（演示）或 `java/project-agent/` + `java/RuoYi/` | 业务 HITL（状态机） |
| AI 编排 | `python/src/project_agent/rag_kb/` | LangGraph 图 + **节点内 LCEL** |
| Self-RAG 路由 | N1a | 入口判断 `need_rag`，不走则跳过检索直达生成 |
| 多查询 Fusion | N1b + N3 + N5 RRF | 一问多改写并行召回 |
| Self-RAG Grade | N6b | 检索不足改写再检索 |
| 图级 HITL | N6c / N7b + Checkpoint | `interrupt` / `resume` |
| 忠实度 | N7b LCEL | 抗幻觉校验 |
| Checkpoint | SqliteSaver | `data/checkpoints.sqlite` |
| AI 前端 | `python-frontend/` React（默认）；`python-frontend/vue/` 对照 | 对话 HITL 卡片 |
| 业务前端 | `frontend/`（预留）+ 若依 admin | 业务管理 UI |

## 2. 对话链路（业务可感知）

```
改写(N1) → Self-RAG 路由(N1a)：need_rag?
  ├─ false → 工具生成(N7) → 忠实度(N7b)
  └─ true  → 多查询(N1b) → 定位 → 多路召回 → RRF → Rerank
             → Self-RAG Grade(N6b) → (不足且耗尽) HITL interrupt
             → 生成+工具 → 忠实度(LCEL) → (失败) HITL interrupt → SSE
```

立项审批仍走 `/api/v1/projects/*/review`，**不是**图 interrupt。

## 3. 开关（conf/.env）

- `INFRA_HOST`（局域网 Docker 宿主机，默认 `192.168.1.9`；改 IP 只改这一项）
- `ENABLE_SELF_RAG_ROUTE`（入口是否判断 need_rag；关则始终检索）
- `ENABLE_MULTI_QUERY` / `MULTI_QUERY_COUNT`（N3 为批量 Embedding + 线程池并行召回）
- `ENABLE_FAITHFULNESS`
- `ENABLE_GRAPH_HITL`
- `CHECKPOINT_DB_PATH`
- `LANGSMITH_*`（可选链路追踪）
- `PROJECT_BIZ_BASE_URL`（推荐 `http://<INFRA_HOST>:48080` 指向 Nest；空=本地 JSON 回退）
- 现场嫌慢：可用 [`conf/.env.demo`](../conf/.env.demo) 精简 LLM hops

对话 SSE：节点 `status` + N7 **真 token 流**（LangGraph custom stream）+ 诊断 `meta`。

### 基础设施叙事（面试对齐）

| 组件 | 状态 |
| --- | --- |
| Milvus | **主路径依赖**（健康检查 readiness 以此为准） |
| 会话记忆 | 本地 JSON 窗口裁剪，非 Redis |
| 工具查库 | Mock / 可换真实 MySQL |
| MySQL / Redis / MinIO | **规划或可选**，配置项预留，勿写成已上线生产依赖 |

## 4. 前端

- **AI 门户（默认）**：`python-frontend/` React
- 开发：`cd python-frontend && npm run dev` → http://localhost:5173/
- 生产静态：`python-frontend/dist`（FastAPI 优先挂载）
- `python-frontend/vue/` 仅作 Vue 预研对照
- **业务前端**：`frontend/` 预留；日常可用 `java/RuoYi` 自带 admin
