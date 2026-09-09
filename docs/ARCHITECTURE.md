# 混合架构：Java 业务微服务 + Python AI 编排

> 目标形态：**项目库等基础业务** 由 Java（推荐 [芋道](https://doc.iocoder.cn/)）承载；**涉及 AI 的能力** 落在本仓 Python（LangGraph / LCEL 节点链 / RAG / HITL）。

## 1. 职责切分

| 域 | 实现 | 内容 |
| --- | --- | --- |
| 项目库 CRUD / 审批 | `java-biz/` + Python 可转发 | 业务 HITL（状态机） |
| AI 编排 | `src/project_agent/rag_kb/` | LangGraph 图 + **节点内 LCEL** |
| 多查询 Fusion | N1b + N3 + N5 RRF | 一问多改写并行召回 |
| Self-RAG | N6b | 检索不足改写再检索 |
| 图级 HITL | N6c / N7b + Checkpoint | `interrupt` / `resume` |
| 忠实度 | N7b LCEL | 抗幻觉校验 |
| Checkpoint | SqliteSaver | `data/checkpoints.sqlite` |
| 前端 | `frontend-vue/` | Vue 3 + 对话 HITL 卡片 |

## 2. 对话链路（业务可感知）

```
改写(N1) → 多查询(N1b/LCEL) → 定位 → 多路召回 → RRF → Rerank
 → Self-RAG → (不足且耗尽) HITL interrupt
 → 生成+工具 → 忠实度(LCEL) → (失败) HITL interrupt → SSE
```

立项审批仍走 `/api/v1/projects/*/review`，**不是**图 interrupt。

## 3. 开关（conf/.env）

- `ENABLE_MULTI_QUERY` / `MULTI_QUERY_COUNT`
- `ENABLE_FAITHFULNESS`
- `ENABLE_GRAPH_HITL`
- `CHECKPOINT_DB_PATH`
- `LANGSMITH_*`（可选链路追踪）
- `PROJECT_BIZ_BASE_URL`（空=本地 JSON）

## 4. 前端

- **主门户（默认）**：`frontend/` React（视觉与交互以此为准）
- 开发：`cd frontend && npm run dev` → http://localhost:5173/
- 生产静态：`frontend/dist`（FastAPI 优先挂载）
- `frontend-vue/` 仅作 Vue 预研对照，不作为默认入口
