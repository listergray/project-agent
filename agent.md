# Agent 指引 · project-agent

> 给 Cursor / 编码 Agent 的项目速查。详细说明见 `README.md`，精炼大纲见 `PROJECT_OUTLINE.md`。

## 项目是什么

公司预研项目、本地可跑的**双 Agent 演示**（技术演示 + RAG/Agent 落地验证）：

| 演示 | 路径 | 做什么 |
| --- | --- | --- |
| RAG 知识库 | `src/project_agent/rag_kb/` | LangGraph **7 导入 + 7 检索**；3 个 Function Calling 工具 |
| 代码助手 编程提效 | `src/project_agent/copilot/` | LangGraph **5+1** 流水线，产出 Java/单测/接口文档 |

统一 HTTP：`src/project_agent/api/server.py`（FastAPI，默认 `:8080`）。

## 技术约束（改代码时遵守）

- **语言**：Python 3.11–3.12（不要升到 3.13+，FlagEmbedding 兼容性未保证）
- **编排**：LangGraph StateGraph；LLM 走 `langchain-openai`（DeepSeek 等 OpenAI 兼容，Key 在 `conf/.env`）
- **主包**：只改 `src/project_agent/`。
- **配置**：`pydantic-settings` → `src/project_agent/core/config.py`；密钥/连接串只进 `conf/.env`（参考 `conf/.env.example`）
- **Prompt**：放 `prompts/*.txt`，用 `utils/prompt_loader` 加载，勿把长 Prompt 硬编码进节点
- **中间件**：Milvus / MySQL / MinIO / Redis，由 `docker/` Compose 起；本地模型在 `data/models/`

## 目录导航

```
conf/                 .env / .env.example
data/samples/         企业手册 MD（ASSET / HR / FIN）
data/models/          BGE + Reranker 本地权重
docker/               compose + mysql 初始化 + up.ps1
prompts/              与节点对应的 Prompt 模板
output/               代码助手 生成物、rag-ui 展示页
scripts/  tests/      脚本 / pytest 冒烟
src/project_agent/
  core/               config + logger
  clients/            llm / embed / milvus
  utils/              splitter / fuzzy / prompt_loader
  tools/              rag_tools（3 @tool）+ init_infra
  rag_kb/       state + nodes + graphs + cli
  copilot/      state + nodes + graph + cli
  api/server.py       FastAPI 入口
```

## CLI 入口（`pyproject.toml` scripts）

```text
rag-import   → 灌库（samples → Milvus）
rag-chat     → 检索问答（含 --presets）
copilot-run      → 代码助手 流水线
agent-api       → uvicorn :8080
```

开发安装：`pip install -e ".[dev]"`（或在已激活的 `.venv` 里）。

## RAG 知识库 必须对齐的技术要点

**导入 7 节点**：解析 → 读文件 → 清洗 → 语义分块 → LLM 抽 Item → BGE 编码 → Milvus 写入（`kb_item_names` + `kb_chunks`）。

**检索 7 节点**：意图（RETRIEVAL / TOOL_FIRST / MIXED）→ 定位 Item → 向量召回 → 工具模糊召回 → RRF → Rerank → 生成 + 最多 3 轮 Function Calling。

**工具名勿改**（对外契约，改动需同步更新 README/接口文档）：

- `query_resource_by_code`
- `fuzzy_match_resource`
- `export_to_excel`

实现：`src/project_agent/tools/rag_tools.py`；模糊算法在 `utils/fuzzy.py`（Levenshtein + 同义词）。

## 代码助手 流水线

需求拆解 → 代码生成 → 审查重构（5 规则）→ 单测 → 接口文档 → 落盘 `output/copilot_*`。

业务场景：资产盘点导入 + 模糊匹配 + 库存扣减（Java / MyBatis / JUnit5）。

## API 一览

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/v1/health` | 中间件就绪 |
| GET | `/api/v1/prompts` | Prompt 清单 |
| GET | `/api/v1/rag/presets` | 演示预设题 |
| POST | `/api/v1/rag/chat` | 问答 |
| POST | `/api/v1/rag/chat/stream` | SSE |
| POST | `/api/v1/rag/import` | 上传灌库 |
| POST | `/api/v1/copilot/run` | 跑 代码助手 |

展示页：`output/rag-ui/`（常另开 `:8088` 静态服务）。

## Agent 工作约定

1. **先读再改**：改图/节点前看对应 `state.py`、`nodes.py`、`graphs/` 或 `graph/`。
2. **小改动**：只改任务相关文件；不顺手重构、不扩写无关文档。
3. **密钥**：永不提交 `conf/.env`；示例只动 `.env.example`。
4. **测试**：行为变更后跑 `pytest -q`；能本地验证的 CLI/接口尽量验证。
5. **演示一致性**：改检索策略/工具签名前，确认是否破坏 README 演示脚本与文档表述。
6. **Windows**：脚本示例多为 PowerShell；起中间件用 `.\docker\up.ps1`。

## 常用重启

```powershell
$env:TOKENIZERS_PARALLELISM = "false"
.\.venv\Scripts\python.exe -m uvicorn project_agent.api.server:app --host 0.0.0.0 --port 8080
```
