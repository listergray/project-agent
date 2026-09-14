"""
project-agent 全局配置（集中收口，避免各模块重复读 .env）
设计说明：所有模型/中间件参数统一从 Settings 单例读取，更换模型/环境只改 .env 不动代码
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_repo_root() -> Path:
    """仓库根：含 pyproject.toml + conf/（兼容 python/src 下嵌套深度变化）。"""
    here = Path(__file__).resolve()
    for p in (here, *here.parents):
        if (p / "pyproject.toml").is_file() and (p / "conf").is_dir():
            return p
    return here.parents[4]


ROOT_DIR = _find_repo_root()
CONF_DIR = ROOT_DIR / "conf"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=CONF_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------- 基础 ----------
    port: int = 8080
    log_level: str = "INFO"
    env: str = "dev"

    # ---------- 局域网基础设施（Docker 宿主机）----------
    # 改 IP 只改这一项；Milvus / MinIO / MySQL / Redis 留空时自动继承
    infra_host: str = Field(
        "192.168.1.46",
        description="容器所在局域网宿主机；留空各 *_HOST 时用此值",
    )

    # ---------- LLM ----------
    llm_provider: str = "deepseek"
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_api_key: str = ""
    llm_model: str = "deepseek-chat"
    llm_temperature: float = 0.1
    llm_timeout: int = 60
    # 立项文档图片理解（DeepSeek 主模型无视觉时请另配多模态，如硅基流动 Qwen2-VL）
    llm_vision_model: str = Field(
        "",
        description="多模态模型名；空则尝试 llm_model（多数文本模型会失败）",
    )
    llm_vision_base_url: str = Field(
        "",
        description="多模态 API base_url；空则用 llm_base_url",
    )
    llm_vision_api_key: str = Field(
        "",
        description="多模态 API Key；空则用 llm_api_key",
    )

    # ---------- Embedding / Rerank ----------
    embed_model_name: str = "BAAI/bge-small-zh-v1.5"
    embed_model_cache_dir: Path = ROOT_DIR / "data" / "models"
    rerank_model_name: str = "BAAI/bge-reranker-v2-m3"

    # ---------- Milvus（空 = 用 INFRA_HOST）----------
    milvus_host: str = ""
    milvus_port: int = 19530
    milvus_alias: str = "default"

    # ---------- MinIO（空 endpoint = INFRA_HOST:9000；主演示可不启）----------
    minio_endpoint: str = ""
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket_kb: str = "kb-files"

    # ---------- MySQL（规划/可选；空 host = INFRA_HOST）----------
    mysql_host: str = ""
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = "root123456"
    mysql_db_meta: str = "project_agent_meta"
    mysql_db_dw: str = "project_agent_dw"

    @property
    def mysql_meta_dsn(self) -> str:
        return (
            f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_db_meta}?charset=utf8mb4"
        )

    @property
    def mysql_dw_dsn(self) -> str:
        return (
            f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_db_dw}?charset=utf8mb4"
        )

    # ---------- Redis（规划/可选；空 host = INFRA_HOST）----------
    redis_host: str = ""
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0

    # ---------- Self-RAG ----------
    self_rag_max_retries: int = Field(
        1, description="检索不足时最多改写再检索次数（0=关闭重试）"
    )
    enable_self_rag_route: bool = Field(
        True,
        description="入口 Self-RAG 路由：判断 need_rag；关闭则始终走检索链",
    )

    # ---------- RAG 工程化开关 ----------
    enable_multi_query: bool = Field(True, description="多查询 RAG-Fusion")
    multi_query_count: int = Field(3, description="含原问在内的查询条数（建议 3）")
    enable_faithfulness: bool = Field(True, description="答案忠实度校验")
    enable_graph_hitl: bool = Field(True, description="图级 interrupt HITL")
    checkpoint_db_path: Path = Field(
        default_factory=lambda: ROOT_DIR / "data" / "checkpoints.sqlite",
        description="LangGraph Sqlite Checkpoint 路径",
    )

    # ---------- 会话窗口裁剪 ----------
    chat_max_history_turns: int = Field(12, description="落盘保留的最大对话轮数（user+assistant 各算 1）")
    chat_max_history_messages: int = Field(16, description="注入 Prompt 的最大消息条数")
    chat_max_history_chars: int = Field(6000, description="注入 Prompt 的历史总字符上限")

    # ---------- 项目库业务后端（Nest / 芋道 HTTP）----------
    project_biz_base_url: str = Field(
        "",
        description="业务项目库根地址；空则本地 JSON。可用 http://{INFRA_HOST}:48080",
    )
    project_biz_timeout: int = Field(15, description="调用业务项目库超时秒")

    # ---------- LangSmith ----------
    langsmith_tracing: bool = Field(False, description="是否启用 LangSmith tracing")
    langsmith_api_key: str = ""
    langsmith_project: str = "project-agent"
    langsmith_endpoint: str = "https://api.smith.langchain.com"

    @model_validator(mode="after")
    def _apply_infra_host(self) -> "Settings":
        """未单独配置（空 / localhost）的中间件 host，统一落到 INFRA_HOST。"""
        host = (self.infra_host or "localhost").strip() or "localhost"

        def _host(val: str) -> str:
            v = (val or "").strip()
            if not v or v in ("localhost", "127.0.0.1"):
                return host
            return v

        self.milvus_host = _host(self.milvus_host)
        self.mysql_host = _host(self.mysql_host)
        self.redis_host = _host(self.redis_host)

        ep = (self.minio_endpoint or "").strip()
        if not ep or ep.startswith("localhost:") or ep.startswith("127.0.0.1:"):
            # 保留原端口（若有）
            port = "9000"
            if ":" in ep:
                port = ep.rsplit(":", 1)[-1] or "9000"
            self.minio_endpoint = f"{host}:{port}"
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """单例模式：整个进程只加载一次 .env"""
    return Settings()
