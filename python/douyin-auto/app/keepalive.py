from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from pathlib import Path
from typing import Any

from app.config import settings

logger = logging.getLogger("douyin-auto.keepalive")

_state: dict[str, Any] = {
    "enabled": True,
    "lastAt": 0.0,
    "lastOk": None,
    "lastMessage": "",
    "nextAt": 0.0,
    "lastDelayMin": None,
    "running": False,
}
_task: asyncio.Task | None = None


def _state_path() -> Path:
    return Path(settings.data_dir) / "login_keepalive.json"


def next_delay_sec() -> float:
    """Base interval with random jitter to avoid fixed detection cadence."""
    base = max(5, int(settings.keep_alive_interval_min))
    jitter = max(0, int(settings.keep_alive_jitter_min))
    # Clamp so delay never goes below 5 minutes.
    low = max(5, base - jitter)
    high = max(low, base + jitter)
    delay_min = random.uniform(low, high)
    # Extra seconds noise (0-90s)
    delay_sec = delay_min * 60.0 + random.uniform(0, 90)
    return delay_sec


def load_state() -> dict[str, Any]:
    path = _state_path()
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            _state.update({k: data.get(k, _state.get(k)) for k in _state})
        except Exception:
            pass
    _state["enabled"] = bool(settings.keep_alive_enabled)
    return status()


def save_state() -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_state, ensure_ascii=False, indent=2), encoding="utf-8")


def status() -> dict[str, Any]:
    interval = max(5, int(settings.keep_alive_interval_min))
    jitter = max(0, int(settings.keep_alive_jitter_min))
    last_at = float(_state.get("lastAt") or 0)
    return {
        "enabled": bool(settings.keep_alive_enabled and _state.get("enabled", True)),
        "intervalMin": interval,
        "jitterMin": jitter,
        "lastDelayMin": _state.get("lastDelayMin"),
        "running": bool(_state.get("running")),
        "lastOk": _state.get("lastOk"),
        "lastMessage": _state.get("lastMessage") or "",
        "lastAt": int(last_at * 1000) if last_at else None,
        "nextAt": int(float(_state.get("nextAt") or 0) * 1000) or None,
    }


def _schedule_next(from_ts: float | None = None) -> float:
    now = from_ts if from_ts is not None else time.time()
    delay = next_delay_sec()
    _state["lastDelayMin"] = round(delay / 60.0, 2)
    _state["nextAt"] = now + delay
    return delay


async def keepalive_once(force: bool = False) -> dict[str, Any]:
    """Visit creator center with persistent profile to refresh cookies."""
    from app.publisher import check_login

    _state["running"] = True
    try:
        result = await check_login(force=True, soft=False)
        now = time.time()
        _state["lastAt"] = now
        # Ignore transient "busy/skip" as logged-out
        msg = result.get("message") or ""
        transient = bool(result.get("cached")) and ("??" in msg or "????" in msg)
        if transient and _state.get("lastOk") is True:
            _state["lastMessage"] = msg
        else:
            _state["lastOk"] = bool(result.get("ok"))
            _state["lastMessage"] = msg
        delay = _schedule_next(now)
        save_state()
        logger.info(
            "keepalive ok=%s msg=%s next_delay=%.1fm (base=%sm jitter=+/-%sm)",
            _state["lastOk"],
            _state["lastMessage"],
            delay / 60.0,
            settings.keep_alive_interval_min,
            settings.keep_alive_jitter_min,
        )
        return {**status(), **{"probe": result}}
    except Exception as e:
        now = time.time()
        _state["lastAt"] = now
        _state["lastOk"] = False
        _state["lastMessage"] = f"??: {e}"
        # Failure: shorter retry with jitter 8-15 min
        delay = random.uniform(8, 15) * 60 + random.uniform(0, 60)
        _state["lastDelayMin"] = round(delay / 60.0, 2)
        _state["nextAt"] = now + delay
        save_state()
        logger.exception("keepalive failed")
        return status()
    finally:
        _state["running"] = False


async def _loop() -> None:
    # First run after randomized short delay (15-45s) so startup isn't patterned.
    await asyncio.sleep(random.uniform(15, 45))
    while True:
        if not settings.keep_alive_enabled:
            await asyncio.sleep(60)
            continue
        try:
            await keepalive_once()
        except Exception:
            logger.exception("keepalive loop error")
            _schedule_next()
            save_state()
        # Sleep until scheduled nextAt (already jittered inside keepalive_once).
        now = time.time()
        wait = max(30.0, float(_state.get("nextAt") or now) - now)
        await asyncio.sleep(wait)


def start_background() -> None:
    global _task
    load_state()
    if not settings.keep_alive_enabled:
        logger.info("keepalive disabled")
        return
    if _task and not _task.done():
        return
    _task = asyncio.create_task(_loop(), name="douyin-keepalive")
    logger.info(
        "keepalive started interval=%sm jitter=+/-%sm profile=%s",
        settings.keep_alive_interval_min,
        settings.keep_alive_jitter_min,
        settings.browser_profile_dir,
    )


def stop_background() -> None:
    global _task
    if _task and not _task.done():
        _task.cancel()
    _task = None
