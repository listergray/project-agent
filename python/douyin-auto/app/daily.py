"""Publish the next unpublished episode once per day at 19:00 local time."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable

from app.config import settings

logger = logging.getLogger("douyin-auto.daily")

_enqueue: Callable[[dict[str, Any]], dict[str, Any]] | None = None
_task: asyncio.Task | None = None


def set_enqueue(fn: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
    global _enqueue
    _enqueue = fn


def _seconds_until_next() -> float:
    now = datetime.now()
    target = now.replace(
        hour=int(settings.daily_publish_hour),
        minute=int(settings.daily_publish_minute),
        second=0,
        microsecond=0,
    )
    if target <= now:
        target += timedelta(days=1)
    return max(5.0, (target - now).total_seconds())


def next_at_iso() -> str:
    now = datetime.now()
    target = now.replace(
        hour=int(settings.daily_publish_hour),
        minute=int(settings.daily_publish_minute),
        second=0,
        microsecond=0,
    )
    if target <= now:
        target += timedelta(days=1)
    return target.strftime("%Y-%m-%d %H:%M")


def status() -> dict[str, Any]:
    return {
        "enabled": bool(settings.daily_publish_enabled),
        "hour": int(settings.daily_publish_hour),
        "minute": int(settings.daily_publish_minute),
        "nextAt": next_at_iso() if settings.daily_publish_enabled else None,
    }


def run_once(*, force: bool = False) -> dict[str, Any]:
    """Publish the lowest unpublished EP. Same calendar day runs only once unless force."""
    from app import db, jobs, scanner

    today = datetime.now().strftime("%Y-%m-%d")
    if not force:
        try:
            if db.get_meta("daily_publish_date") == today:
                return {"ok": True, "skipped": True, "message": f"{today} already published today"}
        except Exception:
            logger.exception("read daily_publish_date failed")

    running = [j for j in jobs.list_jobs(limit=20) if j.get("status") == "RUNNING"]
    if running:
        return {"ok": False, "skipped": True, "message": "a publish job is already running"}

    directory = (settings.video_dir or "").strip()
    if not directory:
        return {"ok": False, "message": "video dir is empty"}

    items = scanner.scan_videos(directory, exclude_published=True)
    if not items:
        return {"ok": True, "skipped": True, "message": "no pending video"}
    item = min(items, key=lambda x: int(x.get("ep") or 10**9))
    if _enqueue is None:
        return {"ok": False, "message": "publish entry not ready"}

    try:
        if not force and not db.claim_daily_publish(today):
            return {"ok": True, "skipped": True, "message": f"{today} already published today"}
        if force:
            db.set_meta("daily_publish_date", today)
        db.set_meta("daily_publish_ep", str(item.get("ep") or ""))
    except Exception:
        logger.exception("save daily_publish_date failed")

    queued = _enqueue(item)
    logger.info("daily publish queued ep=%s path=%s", item.get("ep"), item.get("path"))
    return {
        "ok": True,
        "skipped": False,
        "message": f"queued EP.{item.get('ep')}",
        "ep": item.get("ep"),
        "title": item.get("title"),
        "videoPath": item.get("path"),
        "job": queued,
    }


async def _loop() -> None:
    while True:
        wait = _seconds_until_next()
        logger.info("daily publish next in %.0fs (%s)", wait, next_at_iso())
        await asyncio.sleep(wait)
        if not settings.daily_publish_enabled:
            await asyncio.sleep(60)
            continue
        try:
            result = await asyncio.to_thread(run_once, force=False)
            logger.info("daily publish result: %s", result.get("message"))
        except Exception:
            logger.exception("daily publish failed")
        # Avoid tight loop if the clock is still on the trigger second.
        await asyncio.sleep(90)


def start_background() -> None:
    global _task
    if not settings.daily_publish_enabled:
        logger.info("daily publish disabled")
        return
    if _task and not _task.done():
        return
    _task = asyncio.create_task(_loop(), name="douyin-daily-publish")
    logger.info(
        "daily publish started at %02d:%02d",
        settings.daily_publish_hour,
        settings.daily_publish_minute,
    )


def stop_background() -> None:
    global _task
    if _task and not _task.done():
        _task.cancel()
    _task = None
