"""
project-agent 根包 —— 生产级双 Agent 预研（Python AI 编排服务）

【核心代码地图】
  api/server.py          HTTP 入口（FastAPI）：RAG / 代码助手 / 立项审批 / SSE
  rag_kb/                Agent① 企业知识库 RAG：State + 7+7 LangGraph 节点
  copilot/               Agent② AI 编程提效：5+1 LangGraph 流水线（生成 Java 样板）
  clients/               工程化封装：LLM(OpenAI 兼容) / Embedding+Rerank / Milvus
  tools/rag_tools.py     Function Calling 工具（编码精确查 / 模糊匹配 / 导出 / 立项查询）
  projects/              立项录入审批（业务 HITL）+ 通过后同步知识库
  utils/                 Prompt 加载、语义分块、编辑距离模糊
  prompts/               Prompt 工程模板（与代码解耦，可独立调优）

【技能点落地情况见各子包模块头注释；总览】
  ✅ LangGraph State/Node/Edge/条件分支 · Prompt · 基础 RAG+查询改写+RRF 融合
  ✅ Function Calling 思考-行动循环 · Milvus+Embedding+余弦+IVF+元数据过滤
  ✅ LLM 兼容封装 · 重试/超时 · DeepSeek 等 OpenAI 兼容模型
  ✅ Self-RAG（N1a 路由 need_rag · N6b Grade）· 多查询 Fusion（N1b）· 忠实度（N7b）· 图级 HITL + Sqlite Checkpoint
  ✅ 会话窗口裁剪 · LangSmith · 节点内 LCEL · React 门户（frontend/；Vue 对照在 frontend-vue）
  ✅ 混合架构：项目库基础业务 → Java/芋道（java-biz/）；AI 编排 → 本仓 Python（见 docs/ARCHITECTURE.md）
  ⚠️ LCEL 管道未替代整图编排（图仍为 LangGraph）；Chroma 未作为主库
  📘 Java 微服务 + Python AI：业务 CRUD 在芋道；RAG/解析/代码助手编排在 Python
"""
from .rag_kb import run_import, run_search, import_sample_dir, cli_import, cli_chat  # noqa: F401
from .copilot import run_copilot, cli_run  # noqa: F401

__version__ = "1.0.0"
__all__ = [
    "__version__",
    "run_import",
    "run_search",
    "import_sample_dir",
    "cli_import",
    "cli_chat",
    "run_copilot",
    "cli_run",
]


def get_app():
    """延迟加载 FastAPI app，避免 import project_agent 时拉起整个 API 栈。"""
    from .api.server import app

    return app
