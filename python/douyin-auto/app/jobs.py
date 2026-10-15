from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from app.config import settings


_lock = threading.Lock()


def _job_path(job_id: str) -> Path:
    return Path(settings.data_dir) / "jobs" / f"{job_id}.json"


def create_job(payload: dict[str, Any]) -> dict[str, Any]:
    job_id = uuid.uuid4().hex[:12]
    now = int(time.time() * 1000)
    job = {
        "id": job_id,
        "status": "PENDING",
        "createdAt": now,
        "updatedAt": now,
        "message": "待处理",
        **payload,
    }
    _write(job)
    return job


def update_job(job_id: str, **fields: Any) -> dict[str, Any]:
    with _lock:
        job = get_job(job_id)
        if not job:
            raise KeyError(job_id)
        job.update(fields)
        job["updatedAt"] = int(time.time() * 1000)
        _write(job)
        return job


def get_job(job_id: str) -> dict[str, Any] | None:
    path = _job_path(job_id)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_jobs(limit: int = 50) -> list[dict[str, Any]]:
    root = Path(settings.data_dir) / "jobs"
    files = sorted(root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    out: list[dict[str, Any]] = []
    for f in files[:limit]:
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            continue
    return out


def _write(job: dict[str, Any]) -> None:
    path = _job_path(job["id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
