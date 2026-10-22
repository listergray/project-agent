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
    "failStreak": 0,
}
_task: asyncio.Task | None = None


def _state_path() -> Path:
    return Path(settings.data_dir) / "login_keepalive.json"


def next_delay_sec(*, shorter: bool = False) -> float:
    """Base interval with random jitter. shorter=True after soft failures."""
    if shorter:
        delay_min = random.uniform(8, 15)
    else:
        base = max(5, int(settings.keep_alive_interval_min))
        jitter = max(0, int(settings.keep_alive_jitter_min))
        low = max(5, base - jitter)
        high = max(low, base + jitter)
        delay_min = random.uniform(low, high)
    return delay_min * 60.0 + random.uniform(0, 90)


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
        "failStreak": int(_state.get("failStreak") or 0),
    }


def _schedule_next(from_ts: float | None = None, *, shorter: bool = False) -> float:
    now = from_ts if from_ts is not None else time.time()
    delay = next_delay_sec(shorter=shorter)
    _state["lastDelayMin"] = round(delay / 60.0, 2)
    _state["nextAt"] = now + delay
    return delay


async def keepalive_once(force: bool = False) -> dict[str, Any]:
    """Really refresh Douyin cookies via headed off-screen browser visit."""
    from app.publisher import refresh_session

    _state["running"] = True
    try:
        result = await refresh_session()
        now = time.time()
        _state["lastAt"] = now
        msg = result.get("message") or ""
        ok = bool(result.get("ok"))
        busy = bool(result.get("busy"))

        if busy:
            # Do not flip UI; retry soon
            _state["lastMessage"] = msg or "??????????"
            delay = _schedule_next(now, shorter=True)
        elif ok:
            _state["lastOk"] = True
            _state["lastMessage"] = msg or "????"
            _state["failStreak"] = 0
            delay = _schedule_next(now, shorter=False)
        else:
            streak = int(_state.get("failStreak") or 0) + 1
            _state["failStreak"] = streak
            # Need 2 consecutive hard fails before UI shows ???
            # (one flaky probe shouldn't kill a good session display).
            if streak >= 2 or _state.get("lastOk") is not True:
                _state["lastOk"] = False
                _state["lastMessage"] = msg or "?????????"
            else:
                _state["lastMessage"] = f"?????({msg})????????"
            delay = _schedule_next(now, shorter=True)

        save_state()
        logger.info(
            "keepalive ok=%s busy=%s streak=%s msg=%s next=%.1fm",
            _state["lastOk"],
            busy,
            _state.get("failStreak"),
            _state["lastMessage"],
            delay / 60.0,
        )
        return {**status(), **{"probe": result}}
    except Exception as e:
        now = time.time()
        _state["lastAt"] = now
        streak = int(_state.get("failStreak") or 0) + 1
        _state["failStreak"] = streak
        if streak >= 2:
            _state["lastOk"] = False
        _state["lastMessage"] = f"????: {e}"
        delay = _schedule_next(now, shorter=True)
        save_state()
        logger.exception("keepalive failed")
        return status()
    finally:
        _state["running"] = False


async def _loop() -> None:
    await asyncio.sleep(random.uniform(20, 50))
    while True:
        if not settings.keep_alive_enabled:
            await asyncio.sleep(60)
            continue
        try:
            await keepalive_once()
        except Exception:
            logger.exception("keepalive loop error")
            _schedule_next(shorter=True)
            save_state()
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
        "keepalive started interval=%sm jitter=+/-%sm profile=%s mode=headed-offscreen",
        settings.keep_alive_interval_min,
        settings.keep_alive_jitter_min,
        settings.browser_profile_dir,
    )


def stop_background() -> None:
    global _task
    if _task and not _task.done():
        _task.cancel()
    _task = None
