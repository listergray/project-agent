"""
LangSmith 链路追踪初始化

【技能点 · LLM 工程化】
  ✅ 通过环境变量启用 LangSmith（LANGCHAIN_TRACING_V2 等）
  ✅ 无 Key 时静默关闭，不影响本地开发
"""
from __future__ import annotations

import os

from loguru import logger

_configured = False


def configure_langsmith() -> bool:
    """根据 Settings 配置 LangSmith；返回是否已启用 tracing。"""
    global _configured
    from project_agent.core import get_settings

    settings = get_settings()
    enabled = bool(getattr(settings, "langsmith_tracing", False))
    api_key = (getattr(settings, "langsmith_api_key", None) or "").strip()
    project = (getattr(settings, "langsmith_project", None) or "project-agent").strip()
    endpoint = (getattr(settings, "langsmith_endpoint", None) or "https://api.smith.langchain.com").strip()

    if not enabled or not api_key:
        # 显式关掉，避免环境残留误开
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")
        if not _configured:
            logger.info("[LangSmith] 未启用（LANGSMITH_TRACING=false 或未配置 API Key）")
            _configured = True
        return False

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = api_key
    os.environ["LANGCHAIN_PROJECT"] = project
    os.environ["LANGCHAIN_ENDPOINT"] = endpoint
    # 兼容新变量名
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = api_key
    os.environ["LANGSMITH_PROJECT"] = project

    if not _configured:
        logger.info(f"[LangSmith] 已启用 tracing · project={project}")
        _configured = True
    return True
