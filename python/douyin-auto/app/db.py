from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterator

import pymysql
from pymysql.cursors import DictCursor

from app.config import settings

logger = logging.getLogger("douyin-auto.db")

LEGACY_THROUGH_EP = 31
DEFAULT_MIN_EP = 32


@contextmanager
def connect(database: str | None = None) -> Iterator[pymysql.Connection]:
    conn = pymysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=database,
        charset="utf8mb4",
        autocommit=True,
        cursorclass=DictCursor,
        connect_timeout=10,
    )
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> dict[str, Any]:
    """Create database/tables and seed EP<=31 as LEGACY. Idempotent."""
    with connect(None) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{settings.mysql_db}` "
                "DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci"
            )

    with connect(settings.mysql_db) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS dy_meta (
                  meta_key   VARCHAR(64)  NOT NULL,
                  meta_value VARCHAR(512) NOT NULL,
                  updated_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                           ON UPDATE CURRENT_TIMESTAMP,
                  PRIMARY KEY (meta_key)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS dy_episode (
                  ep           INT          NOT NULL,
                  status       VARCHAR(32)  NOT NULL,
                  video_name   VARCHAR(255) NULL,
                  video_path   VARCHAR(1024) NULL,
                  title        VARCHAR(512) NULL,
                  cover_path   VARCHAR(1024) NULL,
                  location     VARCHAR(128) NULL,
                  job_id       VARCHAR(64)  NULL,
                  message      VARCHAR(1024) NULL,
                  published_at DATETIME     NULL,
                  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                             ON UPDATE CURRENT_TIMESTAMP,
                  PRIMARY KEY (ep),
                  KEY idx_dy_episode_status (status)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )

    seeded = seed_legacy_through(LEGACY_THROUGH_EP)
    set_meta("min_ep", str(DEFAULT_MIN_EP))
    set_meta("legacy_through_ep", str(LEGACY_THROUGH_EP))
    set_meta(
        "note",
        f"EP.1-EP.{LEGACY_THROUGH_EP} already published; continue from EP.{DEFAULT_MIN_EP}",
    )
    # keep in-memory settings aligned
    settings.min_ep = DEFAULT_MIN_EP
    logger.info(
        "db ready db=%s host=%s legacy_through=%s min_ep=%s seeded=%s",
        settings.mysql_db,
        settings.mysql_host,
        LEGACY_THROUGH_EP,
        DEFAULT_MIN_EP,
        seeded,
    )
    return {
        "ok": True,
        "database": settings.mysql_db,
        "legacyThroughEp": LEGACY_THROUGH_EP,
        "minEp": DEFAULT_MIN_EP,
        "seeded": seeded,
    }


def seed_legacy_through(through_ep: int) -> int:
    """Mark EP 1..through_ep as LEGACY (already published). Returns inserted count."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    inserted = 0
    with connect(settings.mysql_db) as conn:
        with conn.cursor() as cur:
            for ep in range(1, through_ep + 1):
                cur.execute(
                    """
                    INSERT INTO dy_episode (ep, status, message, published_at)
                    VALUES (%s, 'LEGACY', %s, %s)
                    ON DUPLICATE KEY UPDATE
                      status = IF(status IN ('SUCCESS', 'LEGACY'), status, 'LEGACY'),
                      message = IF(status IN ('SUCCESS', 'LEGACY'), message, VALUES(message)),
                      published_at = IFNULL(published_at, VALUES(published_at))
                    """,
                    (ep, f"??????EP.<={through_ep}?", now),
                )
                if cur.rowcount == 1:
                    inserted += 1
    return inserted


def set_meta(key: str, value: str) -> None:
    with connect(settings.mysql_db) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO dy_meta (meta_key, meta_value) VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE meta_value = VALUES(meta_value)
                """,
                (key, value),
            )


def get_meta(key: str, default: str | None = None) -> str | None:
    with connect(settings.mysql_db) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT meta_value FROM dy_meta WHERE meta_key=%s", (key,))
            row = cur.fetchone()
            return row["meta_value"] if row else default


def get_min_ep() -> int:
    raw = get_meta("min_ep")
    if raw and str(raw).isdigit():
        return int(raw)
    return settings.min_ep


def published_eps() -> set[int]:
    """EPs that should not be offered again (LEGACY or SUCCESS).

    Test-phase EPs in settings.allow_republish_ep_set stay eligible to re-upload.
    """
    with connect(settings.mysql_db) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT ep FROM dy_episode WHERE status IN ('LEGACY', 'SUCCESS')"
            )
            done = {int(r["ep"]) for r in cur.fetchall()}
    return done - settings.allow_republish_ep_set


def clear_episode_success(ep: int, *, message: str = "????????") -> bool:
    """Reset SUCCESS ? PENDING so the episode can be published again."""
    with connect(settings.mysql_db) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE dy_episode
                   SET status = 'PENDING',
                       message = %s,
                       published_at = NULL
                 WHERE ep = %s AND status = 'SUCCESS'
                """,
                (message, ep),
            )
            return cur.rowcount > 0


def list_episodes(limit: int = 200) -> list[dict[str, Any]]:
    with connect(settings.mysql_db) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT ep, status, video_name, video_path, title, cover_path,
                       location, job_id, message, published_at, created_at, updated_at
                FROM dy_episode
                ORDER BY ep DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
    out: list[dict[str, Any]] = []
    for r in rows:
        item = dict(r)
        for k in ("published_at", "created_at", "updated_at"):
            if item.get(k) is not None:
                item[k] = item[k].isoformat(sep=" ", timespec="seconds")
        out.append(item)
    return out


def upsert_episode(
    ep: int,
    *,
    status: str,
    video_name: str | None = None,
    video_path: str | None = None,
    title: str | None = None,
    cover_path: str | None = None,
    location: str | None = None,
    job_id: str | None = None,
    message: str | None = None,
    mark_published: bool = False,
) -> None:
    published_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if mark_published else None
    with connect(settings.mysql_db) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO dy_episode (
                  ep, status, video_name, video_path, title, cover_path,
                  location, job_id, message, published_at
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                  status = VALUES(status),
                  video_name = COALESCE(VALUES(video_name), video_name),
                  video_path = COALESCE(VALUES(video_path), video_path),
                  title = COALESCE(VALUES(title), title),
                  cover_path = COALESCE(VALUES(cover_path), cover_path),
                  location = COALESCE(VALUES(location), location),
                  job_id = COALESCE(VALUES(job_id), job_id),
                  message = COALESCE(VALUES(message), message),
                  published_at = IF(
                    VALUES(status) = 'SUCCESS',
                    COALESCE(VALUES(published_at), published_at, NOW()),
                    published_at
                  )
                """,
                (
                    ep,
                    status,
                    video_name,
                    video_path,
                    title,
                    cover_path,
                    location,
                    job_id,
                    message,
                    published_at,
                ),
            )


def ping() -> dict[str, Any]:
    with connect(settings.mysql_db) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 AS ok")
            cur.fetchone()
            cur.execute("SELECT COUNT(*) AS c FROM dy_episode WHERE status='LEGACY'")
            legacy = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(*) AS c FROM dy_episode WHERE status='SUCCESS'")
            success = cur.fetchone()["c"]
    return {
        "ok": True,
        "host": settings.mysql_host,
        "database": settings.mysql_db,
        "minEp": get_min_ep(),
        "legacyCount": int(legacy),
        "successCount": int(success),
    }
