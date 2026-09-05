"""
project-agent 全局配置（集中收口，避免各模块重复读 .env）
设计说明：所有模型/中间件参数统一从 Settings 单例读取，更换模型/环境只改 .env 不动代码
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]  # repo root
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

    # ---------- LLM ----------
    llm_provider: str = "deepseek"
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_api_key: str = ""
    llm_model: str = "deepseek-chat"
    llm_temperature: float = 0.1
    llm_timeout: int = 60

    # ---------- Embedding / Rerank ----------
    embed_model_name: str = "BAAI/bge-small-zh-v1.5"
    embed_model_cache_dir: Path = ROOT_DIR / "data" / "models"
    rerank_model_name: str = "BAAI/bge-reranker-v2-m3"

    # ---------- Milvus ----------
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_alias: str = "default"

    # ---------- MinIO ----------
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket_kb: str = "kb-files"

    # ---------- MySQL ----------
    mysql_host: str = "localhost"
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

    # ---------- Redis ----------
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """单例模式：整个进程只加载一次 .env"""
    return Settings()  # type: ignore[call-arg]
