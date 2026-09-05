"""project-agent 根包。对外暴露两个 Agent 的门面函数（便于 import）。"""
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
