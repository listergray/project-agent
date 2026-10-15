from __future__ import annotations

import asyncio
import logging
import threading
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import db, jobs, keepalive, scanner
from app.config import settings
from app.publisher import bootstrap_login_cache, check_login, open_login_browser, publish_video

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("douyin-auto")

app = FastAPI(title="抖音目录发视频", version="1.0.0")

STATIC_DIR = Path(__file__).resolve().parent.parent / "web"
if STATIC_DIR.is_dir():
    assets = STATIC_DIR / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")


class ScanRequest(BaseModel):
    directory: str | None = None


class SettingsUpdate(BaseModel):
    videoDir: str | None = None
    headless: bool | None = None


class PublishRequest(BaseModel):
    videoPath: str
    title: str | None = None
    coverPath: str | None = None
    location: str | None = None
    directory: str | None = None


@app.get("/")
async def index() -> FileResponse:
    index_html = STATIC_DIR / "index.html"
    if not index_html.is_file():
        raise HTTPException(404, "页面不存在")
    return FileResponse(index_html)


@app.get("/api/health")
async def health() -> dict[str, Any]:
    out: dict[str, Any] = {"ok": True, "port": settings.server_port}
    try:
        out["db"] = db.ping()
    except Exception as e:
        out["db"] = {"ok": False, "error": str(e)}
    return out


@app.get("/api/settings")
async def get_settings() -> dict[str, Any]:
    min_ep = settings.min_ep
    try:
        min_ep = db.get_min_ep()
    except Exception:
        pass
    return {
        "videoDir": settings.video_dir,
        "headless": settings.headless,
        "browserProfileDir": str(Path(settings.browser_profile_dir).resolve()),
        "uploadTimeoutMs": settings.upload_timeout_ms,
        "defaultLocation": settings.default_location,
        "publishHashtags": settings.publish_hashtag_list,
        "allowRepublishEps": sorted(settings.allow_republish_ep_set),
        "llmEnabled": bool(settings.llm_enabled and settings.llm_api_key),
        "llmModel": settings.llm_model,
        "minEp": min_ep,
        "legacyThroughEp": db.LEGACY_THROUGH_EP,
        "mysqlHost": settings.mysql_host,
        "mysqlDb": settings.mysql_db,
        "keepAliveEnabled": settings.keep_alive_enabled,
        "keepAliveIntervalMin": settings.keep_alive_interval_min,
        "keepAliveJitterMin": settings.keep_alive_jitter_min,
        "keepAlive": keepalive.status(),
    }


@app.put("/api/settings")
async def put_settings(body: SettingsUpdate) -> dict[str, Any]:
    if body.videoDir is not None:
        settings.video_dir = body.videoDir.strip()
    if body.headless is not None:
        settings.headless = body.headless
    _persist_env()
    return await get_settings()


@app.post("/api/scan")
async def scan(body: ScanRequest | None = None) -> dict[str, Any]:
    directory = (body.directory if body else None) or settings.video_dir
    if not directory:
        raise HTTPException(400, "请先设置视频目录")
    try:
        min_ep = db.get_min_ep()
    except Exception:
        min_ep = settings.min_ep
    try:
        items = scanner.scan_videos(directory, min_ep=min_ep, exclude_published=True)
    except FileNotFoundError as e:
        raise HTTPException(400, str(e)) from e
    return {
        "directory": str(Path(directory).expanduser().resolve()),
        "minEp": min_ep,
        "total": len(items),
        "list": items,
    }


@app.get("/api/episodes")
async def episodes() -> dict[str, Any]:
    try:
        return {
            "minEp": db.get_min_ep(),
            "legacyThroughEp": db.LEGACY_THROUGH_EP,
            "list": db.list_episodes(),
        }
    except Exception as e:
        raise HTTPException(500, f"数据库不可用: {e}") from e


@app.get("/api/login/status")
async def login_status(force: bool = False, soft: bool = True) -> dict[str, Any]:
    """Default soft=True: use disk/memory cache after restart (no Playwright).

    Use ?force=1 to open browser and re-check for real.
    """
    result = await check_login(force=force, soft=soft and not force)
    result["keepAlive"] = keepalive.status()
    return result


@app.post("/api/login")
async def login() -> dict[str, Any]:
    old = settings.headless
    settings.headless = False
    try:
        result = await open_login_browser(timeout_sec=300)
        if result.get("ok"):
            # Record successful QR login into keepalive state.
            keepalive._state["lastAt"] = __import__("time").time()
            keepalive._state["lastOk"] = True
            keepalive._state["lastMessage"] = result.get("message") or "已登录"
            keepalive._schedule_next(keepalive._state["lastAt"])
            keepalive.save_state()
        return {**result, "keepAlive": keepalive.status()}
    finally:
        settings.headless = old


@app.post("/api/login/keepalive")
async def login_keepalive() -> dict[str, Any]:
    """Manually refresh creator-center session (same as scheduled keepalive)."""
    return await keepalive.keepalive_once(force=True)


@app.get("/api/login/keepalive")
async def login_keepalive_status() -> dict[str, Any]:
    return keepalive.status()


@app.get("/api/jobs")
async def job_list() -> dict[str, Any]:
    return {"list": jobs.list_jobs()}


@app.get("/api/jobs/{job_id}")
async def job_get(job_id: str) -> dict[str, Any]:
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(404, "任务不存在")
    return job


@app.post("/api/publish")
async def publish(body: PublishRequest) -> dict[str, Any]:
    video = Path(body.videoPath).expanduser()
    if not video.is_file():
        raise HTTPException(400, f"文件不存在: {video}")

    meta = scanner.resolve_sidecar(video)
    # Prefer sidecar 标题.txt / 封面上传版_3比4|4比3; body can override coverPath.
    title = (body.title or meta["title"] or video.stem).strip()
    cover_v = meta.get("coverPathV")
    cover_h = meta.get("coverPathH")
    cover = body.coverPath or meta.get("coverPath")
    if body.coverPath and not cover_v and not cover_h:
        cover_v = body.coverPath
    description = meta.get("description") or ""
    location = (body.location if body.location is not None else settings.default_location).strip()
    ep = scanner.ep_number(video.name)
    if ep is None:
        raise HTTPException(400, "文件名需包含 EP.数字（如 EP.32）")
    try:
        min_ep = db.get_min_ep()
        if ep < min_ep:
            raise HTTPException(400, f"EP.{ep} 早于起始集 EP.{min_ep}（≤{db.LEGACY_THROUGH_EP} 已记录为已发布）")
        if ep in db.published_eps():
            raise HTTPException(400, f"EP.{ep} 已在库中标记为已发布")
        if ep in settings.allow_republish_ep_set:
            try:
                db.clear_episode_success(ep)
            except Exception as e:
                logger.warning("clear SUCCESS for republish EP.%s: %s", ep, e)
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("episode db check skipped: %s", e)

    job = jobs.create_job(
        {
            "videoPath": str(video.resolve()),
            "title": title,
            "coverPath": cover,
            "coverPathV": cover_v,
            "coverPathH": cover_h,
            "description": description,
            "location": location,
            "ep": ep,
            "status": "RUNNING",
            "message": "排队中",
        }
    )
    job_id = job["id"]

    try:
        db.upsert_episode(
            ep,
            status="RUNNING",
            video_name=video.name,
            video_path=str(video.resolve()),
            title=title,
            cover_path=cover,
            location=location,
            job_id=job_id,
            message="排队中",
        )
    except Exception as e:
        logger.warning("upsert RUNNING failed: %s", e)

    def runner() -> None:
        def on_progress(msg: str) -> None:
            try:
                jobs.update_job(job_id, message=msg, status="RUNNING")
            except Exception:
                pass

        try:
            result = asyncio.run(
                publish_video(
                    video_path=str(video.resolve()),
                    title=title,
                    cover_path=cover,
                    cover_path_v=cover_v,
                    cover_path_h=cover_h,
                    description=description,
                    location=location,
                    on_progress=on_progress,
                )
            )
            ok = bool(result.get("ok"))
            status = "SUCCESS" if ok else "FAILED"
            message = result.get("message") or ""
            jobs.update_job(job_id, status=status, message=message, result=result)
            try:
                db.upsert_episode(
                    ep,
                    status=status,
                    video_name=video.name,
                    video_path=str(video.resolve()),
                    title=title,
                    cover_path=cover,
                    location=location,
                    job_id=job_id,
                    message=message,
                    mark_published=ok,
                )
            except Exception as e:
                logger.warning("upsert %s failed: %s", status, e)
        except Exception as e:
            logger.exception("publish job failed")
            jobs.update_job(job_id, status="FAILED", message=str(e))
            try:
                db.upsert_episode(
                    ep,
                    status="FAILED",
                    video_name=video.name,
                    video_path=str(video.resolve()),
                    title=title,
                    cover_path=cover,
                    location=location,
                    job_id=job_id,
                    message=str(e),
                )
            except Exception:
                pass

    threading.Thread(target=runner, name=f"douyin-publish-{job_id}", daemon=True).start()
    return {"jobId": job_id, "job": job}


def _persist_env() -> None:
    env_path = Path(".env")
    lines: list[str] = []
    if env_path.is_file():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    kv = {
        "SERVER_PORT": str(settings.server_port),
        "VIDEO_DIR": settings.video_dir,
        "HEADLESS": "true" if settings.headless else "false",
        "BROWSER_PROFILE_DIR": settings.browser_profile_dir,
        "DATA_DIR": settings.data_dir,
        "UPLOAD_TIMEOUT_MS": str(settings.upload_timeout_ms),
        "DEFAULT_LOCATION": settings.default_location,
        "PUBLISH_HASHTAGS": settings.publish_hashtags,
        "ALLOW_REPUBLISH_EPS": settings.allow_republish_eps,
        "MIN_EP": str(settings.min_ep),
        "MYSQL_HOST": settings.mysql_host,
        "MYSQL_PORT": str(settings.mysql_port),
        "MYSQL_USER": settings.mysql_user,
        "MYSQL_DB": settings.mysql_db,
        "KEEP_ALIVE_ENABLED": "true" if settings.keep_alive_enabled else "false",
        "KEEP_ALIVE_INTERVAL_MIN": str(settings.keep_alive_interval_min),
        "KEEP_ALIVE_JITTER_MIN": str(settings.keep_alive_jitter_min),
    }
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        if "=" in line and not line.strip().startswith("#"):
            key = line.split("=", 1)[0].strip()
            if key in kv:
                out.append(f"{key}={kv[key]}")
                seen.add(key)
                continue
        out.append(line)
    for k, v in kv.items():
        if k not in seen:
            out.append(f"{k}={v}")
    env_path.write_text("\n".join(out) + "\n", encoding="utf-8")


@app.on_event("startup")
async def on_startup() -> None:
    settings.ensure_dirs()
    try:
        cached = bootstrap_login_cache()
        if cached:
            logger.info("restored login cache from disk: %s", cached)
    except Exception:
        logger.exception("bootstrap login cache failed")
    try:
        info = db.init_db()
        logger.info("episode db seeded: %s", info)
    except Exception:
        logger.exception("MySQL init failed — publish history will not persist until DB is reachable")
    try:
        keepalive.start_background()
    except Exception:
        logger.exception("keepalive start failed")
    logger.info(
        "douyin-auto ready on :%s video_dir=%s min_ep=%s keepalive=%sm",
        settings.server_port,
        settings.video_dir or "(empty)",
        settings.min_ep,
        settings.keep_alive_interval_min if settings.keep_alive_enabled else 0,
    )


@app.on_event("shutdown")
async def on_shutdown() -> None:
    keepalive.stop_background()
