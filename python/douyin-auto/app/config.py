from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    server_port: int = 12500
    video_dir: str = ""
    headless: bool = False
    browser_profile_dir: str = "./data/browser-profile"
    data_dir: str = "./data"
    upload_timeout_ms: int = 300_000
    # Douyin publish location (geo tag)
    default_location: str = "北京市朝阳区"
    # Hashtags appended to 作品简介
    publish_hashtags: str = "#ai编程,#干货"
    # Fallback when DB not ready; DB meta.min_ep is source of truth after seed
    min_ep: int = 32
    # Test phase: comma-separated EPs allowed to republish even if SUCCESS (e.g. 32)
    allow_republish_eps: str = "32"

    @property
    def publish_hashtag_list(self) -> list[str]:
        parts = [p.strip() for p in (self.publish_hashtags or "").split(",") if p.strip()]
        return [p if p.startswith("#") else f"#{p}" for p in parts]

    @property
    def allow_republish_ep_set(self) -> set[int]:
        out: set[int] = set()
        for p in (self.allow_republish_eps or "").split(","):
            p = p.strip()
            if p.isdigit():
                out.add(int(p))
        return out

    # MySQL (twlmac) — persists episode publish state
    mysql_host: str = "twlmac"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = "root123456"
    mysql_db: str = "douyin_auto"

    # Login keepalive: periodically open creator center with local profile
    keep_alive_enabled: bool = True
    keep_alive_interval_min: int = 45
    # Random jitter minutes: next delay = interval ± jitter (avoids fixed cadence)
    keep_alive_jitter_min: int = 12

    # DeepSeek / OpenAI-compatible judge (text-only; deepseek-chat 无视觉)
    llm_enabled: bool = True
    llm_base_url: str = "https://api.deepseek.com"
    llm_api_key: str = ""
    llm_model: str = "deepseek-chat"
    llm_timeout: int = 60

    def ensure_dirs(self) -> None:
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        Path(self.browser_profile_dir).mkdir(parents=True, exist_ok=True)
        Path(self.data_dir, "jobs").mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
