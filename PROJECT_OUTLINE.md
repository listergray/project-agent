# Project Agent 项目大纲

> 公司预研级双 Agent 演示工程：验证 **「Java/芋道 业务微服务 + Python AI 编排」** 混合架构。  
> 架构边界见 `docs/ARCHITECTURE.md`；详细技术栈见 `README.md`。

---

## 1. 项目定位

- **性质**：本地可运行、可浏览器演示（FastAPI AI 入口 + React + 芋道业务模块骨架）
- **切分**：
  - **项目库基础业务**（CRUD / 审批 / MySQL）→ Java，推荐芋道单体（`java-biz/`）
  - **AI 业务**（RAG / 解析 / 知识库同步 / 代码助手）→ 本仓 Python（`src/project_agent/`）

## 2. 技术栈总览

| 分类 | 组件 |
| --- | --- |
| 业务微服务 | Java 17 · 芋道 · MyBatis-Plus · MySQL（`java-biz/`） |
| 编排 | LangGraph（StateGraph） |
| LLM | LangChain / DeepSeek（OpenAI 兼容） |
| 向量 | BGE Embed + Rerank · Milvus |
| 中间件 | MySQL · MinIO · Redis · Docker Compose |
| AI 服务 | FastAPI + SSE · React 前端 |

## 3. 目录结构大纲

```
project-agent/
├── docs/ARCHITECTURE.md     混合架构说明
├── java-biz/                芋道风格项目库模块 + OpenAPI + SQL
├── conf/                    .env（含 PROJECT_BIZ_BASE_URL）
├── frontend/                React SPA
└── src/project_agent/       Python AI
    ├── projects/            JSON 或转发 Java；parse / rag_sync 为 AI
    ├── rag_kb/              RAG + Self-RAG
    ├── copilot/             代码助手
    └── api/server.py        AI HTTP 入口
```

## 4. 两个智能体 大纲

### RAG 知识库
- 导入 7 节点 · 检索含 Self-RAG · Function Calling 工具

### 代码助手
- 5+1 节点流水线 → 可拷入 Spring Boot / 芋道工程的 Java 脚手架

## 5. 项目库对接

| 模式 | 条件 | 行为 |
| --- | --- | --- |
| 演示 | `PROJECT_BIZ_BASE_URL` 为空 | Python 本地 `data/projects.json` |
| 正式 | 配置芋道地址 | CRUD/审批转发 Java；解析与 RAG 同步仍在 Python |

## 6. 快速启动

```powershell
pip install -e ".[dev]"
.\docker\up.ps1
rag-import
agent-api
# 前端：cd frontend && npm run dev
# 芋道就绪后：conf/.env 设置 PROJECT_BIZ_BASE_URL=http://127.0.0.1:48080
```
