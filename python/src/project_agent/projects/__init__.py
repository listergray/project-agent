"""
项目管理：立项录入 / 文件解析 / 审批 / 同步知识库

【架构边界 · Java 业务 + Python AI】
  ✅ 基础 CRUD/审批：默认本地 JSON；配 PROJECT_BIZ_BASE_URL 后走 Java（java/project-agent/ 或演示 stub）
  ✅ AI：文档 LLM 解析（parse.py）、审批通过后 rag_sync → Milvus —— 始终在 Python
  ✅ HITL：草稿 → 提交 → 待审 → 通过/驳回（业务人工确认）
  详见 docs/ARCHITECTURE.md

模块：
  models.py       字段与状态机
  store.py        本地 JSON + get_store() 路由
  java_client.py  芋道 HTTP 适配
  parse.py        文件解析填表（LLM+规则）【AI】
  rag_sync.py     已通过项目 → Markdown → run_import【AI】
"""
from .models import ProjectCreate, ProjectRecord, ProjectStatus
from .parse import parse_project_from_text
from .rag_sync import sync_approved_project, try_sync_approved_project
from .store import ProjectStore, get_store, get_local_store, reset_store_cache

__all__ = [
    "ProjectCreate",
    "ProjectRecord",
    "ProjectStatus",
    "ProjectStore",
    "get_store",
    "get_local_store",
    "reset_store_cache",
    "parse_project_from_text",
    "sync_approved_project",
    "try_sync_approved_project",
]
