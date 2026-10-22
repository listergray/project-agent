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
    # Keep user publishing queued while another operation holds the profile.
    browser_wait_timeout_sec: int = 900
    cover_verify_timeout_ms: int = 60_000
    # Douyin publish location (geo tag)
    default_location: str = "北京市朝阳区"
    # Hashtags appended to 作品简介
    publish_hashtags: str = "#ai编程,#干货"
    # Fallback when DB not ready; DB meta.min_ep is source of truth after seed
    min_ep: int = 36
    # Comma-separated EPs allowed to republish even if SUCCESS. Empty = none.
    allow_republish_eps: str = ""
    # Daily auto-publish of the next unpublished episode (local time)
    daily_publish_enabled: bool = True
    daily_publish_hour: int = 19
    daily_publish_minute: int = 0

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

    # Login keepalive: headed off-screen visit (headless does NOT renew Douyin cookies)
    keep_alive_enabled: bool = True
    # Douyin sessions drop if idle too long; 20±6min is safer than 45
    keep_alive_interval_min: int = 20
    keep_alive_jitter_min: int = 6

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
