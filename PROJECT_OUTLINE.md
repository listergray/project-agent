# Project Agent 项目大纲

> 公司预研级双 Agent 演示 工程：把「企业资源知识库 RAG+Agent」与「AI 编程提效 代码助手」
> 两个场景落地成可运行代码，用于技术演示与「Java 业务微服务 + Python AI 编排」混合架构验证。
> 详细文档见 `README.md`，本文件为精炼大纲。

---

## 1. 项目定位

- **性质**：本地可运行、可浏览器演示的 Agent 工程（FastAPI 后端 + 静态展示页）
- **目标**：① 一键跑通验证技术可行性 ② 沉淀 RAG/Agent/混合架构落地经验
- **定位**：公司预研项目「项目进度管理智能 Agent 平台（Java 微服务 + Python AI 编排）」的原型验证

## 2. 技术栈总览

| 分类 | 组件 |
| --- | --- |
| 编排 | LangGraph（StateGraph + Checkpoint） |
| LLM 链 | LangChain / langchain-openai |
| 大模型 | DeepSeek-chat（OpenAI 兼容，`conf/.env` 注入 Key） |
| Embedding | BAAI/bge-small-zh-v1.5（本地目录加载） |
| Rerank | BAAI/bge-reranker-v2-m3（本地目录加载） |
| 向量库 | Milvus（kb_item_names + kb_chunks 双层索引） |
| 关系库 | MySQL 8（元数据库 + 业务 Mock 数据） |
| 对象存储 | MinIO（PDF/MD 入库） |
| 缓存/锁 | Redis 7 |
| 工具 | 3 个 LangChain Function Calling 工具 |
| 算法 | 纯 Python Levenshtein DP + 同义词加权 |
| 服务 | FastAPI + SSE 流式 |
| 部署 | Docker Compose 单文件（4 容器健康级联） |

## 3. 目录结构大纲

```
project-agent/
├── conf/                 .env 配置（LLM / 模型 / 中间件连接）
├── data/
│   ├── samples/          3 份企业手册 MD（ASSET / HR / FIN）
│   └── models/           BGE + Reranker 本地权重目录
├── docker/               docker-compose.yml + mysql 初始化 SQL + up.ps1
├── prompts/             10 个 Prompt 模板 txt（与节点一一对应）
├── output/               rag-ui（美观展示页）/ copilot_xxx（生成代码）
├── scripts/  tests/      评测脚本 / 5 条冒烟单测
└── src/project_agent/
    ├── core/             config（pydantic-settings）+ logger（loguru + TraceID）
    ├── clients/          llm_client / embed_client / milvus_client
    ├── utils/            text_splitter / fuzzy / prompt_loader
    ├── tools/            rag_tools（3 个 @tool）+ init_infra
    ├── rag_kb/     state + nodes(7+7) + graphs(2) + cli
    ├── copilot/    state + nodes(5) + graph + cli
    └── api/server.py     FastAPI 统一入口
```

## 4. 两个智能体 大纲

### RAG 知识库 RAG + Agent
- **导入流水线（7 节点）**：解析 → 读文件 → 清洗 → 语义分块 → LLM 抽 Item → BGE 编码 → Milvus 写入
- **检索流水线（7 节点）**：意图识别(RETRIEVAL/TOOL_FIRST/MIXED) → 定位 Item → 向量召回 → 工具模糊召回 → RRF 融合 → Rerank 精排 → 生成回答 + 工具
- **3 个 Function Calling 工具**：`query_resource_by_code`（精确查库）/ `fuzzy_match_resource`（模糊匹配）/ `export_to_excel`（批量导出）

### 代码助手 AI 编程提效
- **流水线（5+1 节点）**：需求拆解 → 代码生成 → 审查重构(5 规则) → 单测生成 → 接口文档 → 落盘
- **产出**：10+ 个 Java/XML/DTO 文件 + 14 条 JUnit5 测试 + Mermaid 接口文档（STAR 案例：2 周工期压到 8 天）

## 5. API 服务大纲（FastAPI :8080）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/health` | 健康（Milvus/MySQL/Redis 就绪态） |
| GET | `/api/v1/prompts` | Prompt 模板清单 |
| GET | `/api/v1/rag/presets` | 预设演示问题 |
| POST | `/api/v1/rag/chat` | 问答（answer + sources + tool_calls + intent） |
| POST | `/api/v1/rag/chat/stream` | SSE 流式问答 |
| POST | `/api/v1/rag/import` | 上传文档灌库 |
| POST | `/api/v1/copilot/run` | 跑 代码助手 生成代码 |

> 展示页（`:8088` 静态服务，`output/rag-ui/index.html`）直连上面 RAG 知识库 接口。

## 6. 基础设施（Docker 4 容器）

Milvus（向量库） · MySQL 8（元/业务库） · MinIO（对象存储） · Redis 7（缓存/锁）

## 7. 快速启动（大纲版）

```powershell
python -m venv .venv && .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"                 # 装依赖
.\docker\up.ps1                         # 起 4 容器
rag-import                            # 灌库（306 chunks）
rag-chat --presets                    # 跑 5 个预设问题看工具调用
copilot-run                               # 生成 Java 代码
agent-api                               # 启 HTTP 服务（:8080）
```

## 8. 当前状态（2026-09-04）

- LLM 已接 **DeepSeek-chat**（Key 在 `conf/.env`），真实模型回答已验证
- 本地模型（BGE / Reranker）已落盘 `data/models/`，启动不再联网
- 8080（API）+ 8088（展示页）运行中，前端修复了 IPv6 / 健康徽章 / 超时三处
- 重启命令：`TOKENIZERS_PARALLELISM=false .venv/Scripts/python.exe -m uvicorn project_agent.api.server:app --host 0.0.0.0 --port 8080`
