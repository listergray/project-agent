# Project Agent 项目大纲

> 公司预研级双 Agent 演示工程：验证 **「Java/芋道 业务微服务 + Python AI 编排」** 混合架构。  
> 架构边界见 `docs/ARCHITECTURE.md`；详细技术栈见 `README.md`。

---

## 1. 项目定位

- **性质**：本地可运行、可浏览器演示（FastAPI AI 入口 + React + 芋道业务模块骨架）
- **切分**：
  - **项目库基础业务**（CRUD / 审批 / MySQL）→ Java（`java/RuoYi/` + `java/project-agent/`）
  - **AI 业务**（RAG / 解析 / 知识库同步 / 代码助手）→ Python（`python/src/project_agent/`）

## 2. 技术栈总览

| 分类 | 组件 |
| --- | --- |
| 业务微服务 | Java 17 · 若依 / 芋道风格模块（`java/`） |
| 编排 | LangGraph（StateGraph） |
| LLM | LangChain / DeepSeek（OpenAI 兼容） |
| 向量 | BGE Embed + Rerank · Milvus |
| 中间件 | MySQL · MinIO · Redis · Docker Compose |
| AI 服务 | FastAPI + SSE · `python-frontend/` React |

## 3. 目录结构大纲

```
project-agent/
├── docs/ARCHITECTURE.md
├── java/                    业务后端（RuoYi / project-agent / 演示 stub）
├── frontend/                业务管理前端（预留；日常用若依 admin）
├── python/                  AI 编排（src / prompts / tests）
├── python-frontend/         AI 门户 React（vue/ 对照）
├── conf/                    .env
└── data/                    本地数据与 checkpoint
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
