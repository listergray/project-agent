# -*- coding: utf-8 -*-
"""Rewrite douyin-auto sources with proper UTF-8 Chinese (ASCII-safe generator)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
u = lambda *cs: "".join(chr(c) for c in cs)

# Common phrases
DOUYIN = u(0x6296, 0x97F3)
DIR_UPLOAD = u(0x76EE, 0x5F55) + u(0x53D1) + u(0x89C6, 0x9891)
COVER = u(0x5C01, 0x9762)
COVER_UP_34 = COVER + u(0x4E0A, 0x4F20, 0x7248) + "_3" + u(0x6BD4) + "4.png"
COVER_UP_43 = COVER + u(0x4E0A, 0x4F20, 0x7248) + "_4" + u(0x6BD4) + "3.png"
NOT_FOUND_DIR = u(0x76EE, 0x5F55, 0x4E0D, 0x5B58, 0x5728)
NOT_FOUND_FILE = u(0x6587, 0x4EF6, 0x4E0D, 0x5B58, 0x5728)
NOT_FOUND_PAGE = u(0x9875, 0x9762, 0x4E0D, 0x5B58, 0x5728)
NOT_FOUND_JOB = u(0x4EFB, 0x52A1, 0x4E0D, 0x5B58, 0x5728)
PLEASE_SET_DIR = u(0x8BF7, 0x5148, 0x8BBE, 0x7F6E, 0x89C6, 0x9891, 0x76EE, 0x5F55)
QUEUED = u(0x6392, 0x961F, 0x4E2D)
PENDING = u(0x5F85, 0x5904, 0x7406)
OPENING_UPLOAD = u(0x6253, 0x5F00, 0x4E0A, 0x4F20, 0x9875) + "..."
NEED_LOGIN = u(0x9700, 0x8981, 0x767B, 0x5F55) + u(0xFF0C) + u(0x8BF7, 0x5728, 0x6D4F, 0x89C8, 0x5668, 0x4E2D, 0x626B, 0x7801) + "..."
LOGIN_TIMEOUT = u(0x767B, 0x5F55, 0x8D85, 0x65F6)
UPLOADING = u(0x4E0A, 0x4F20, 0x4E2D)
WAIT_PROCESS = u(0x7B49, 0x5F85, 0x5904, 0x7406) + "..."
FILL_TITLE = u(0x586B, 0x5199, 0x6807, 0x9898)
SET_COVER = u(0x8BBE, 0x7F6E, 0x5C01, 0x9762)
CLICK_PUBLISH = u(0x70B9, 0x51FB, 0x53D1, 0x5E03) + "..."
PUBLISH_OK = u(0x5DF2, 0x63D0, 0x4EA4, 0x53D1, 0x5E03)
PUBLISH_BTN_FAIL = (
    u(0x672A, 0x627E, 0x5230, 0x53EF, 0x70B9, 0x53D1, 0x5E03, 0x6309, 0x94AE)
    + u(0xFF0C)
    + u(0x8BF7, 0x624B, 0x52A8, 0x68C0, 0x67E5, 0x9875, 0x9762)
)
LOGIN_OK = u(0x5DF2, 0x767B, 0x5F55)
LOGIN_NO = u(0x672A, 0x767B, 0x5F55)
LOGIN_FAIL = u(0x767B, 0x5F55, 0x5931, 0x8D25, 0x6216, 0x8D85, 0x65F6)
HEADLESS_NEED_LOGIN = (
    u(0x672A, 0x767B, 0x5F55)
    + u(0xFF0C)
    + "HEADLESS=true"
    + u(0x65F6, 0x65E0, 0x6CD5, 0x626B, 0x7801)
    + u(0xFF0C)
    + u(0x8BF7, 0x5148, 0x8C03, 0x7528)
    + " /api/login"
)
NO_FILE_INPUT = u(0x672A, 0x627E, 0x5230, 0x4E0A, 0x4F20, 0x63A7, 0x4EF6)
UPLOAD_TIMEOUT = u(0x4E0A, 0x4F20, 0x6216, 0x5904, 0x7406, 0x8D85, 0x65F6)
TITLE_WARN = u(0x672A, 0x80FD, 0x81EA, 0x52A8, 0x586B, 0x5199, 0x6807, 0x9898)
COVER_WARN = u(0x672A, 0x627E, 0x5230, 0x5C01, 0x9762, 0x5165, 0x53E3)
COVER_SET_WARN = u(0x672A, 0x80FD, 0x8BBE, 0x7F6E, 0x5C01, 0x9762)
PUBLISH_FAIL = u(0x53D1, 0x5E03, 0x5931, 0x8D25)
TEXT_PUBLISH = u(0x53D1, 0x5E03)
TEXT_UPLOAD = u(0x4E0A, 0x4F20)
TEXT_HOME = u(0x9996, 0x9875)
TEXT_CONTENT = u(0x5185, 0x5BB9, 0x7BA1, 0x7406)
TEXT_WORKS = u(0x4F5C, 0x54C1, 0x7BA1, 0x7406)
TEXT_SELECT = u(0x9009, 0x62E9, 0x89C6, 0x9891)
TEXT_DRAG = u(0x62D6, 0x62FD, 0x89C6, 0x9891)
TEXT_CLICK_UPLOAD = u(0x70B9, 0x51FB, 0x4E0A, 0x4F20)
TEXT_DESC = u(0x4F5C, 0x54C1, 0x63CF, 0x8FF0)
TEXT_TITLE_PH = u(0x6DFB, 0x52A0, 0x4F5C, 0x54C1, 0x6807, 0x9898)
TEXT_COVER_SEL = u(0x9009, 0x62E9, 0x5C01, 0x9762)
TEXT_COVER_SET = u(0x8BBE, 0x7F6E, 0x5C01, 0x9762)
TEXT_COVER_EDIT = u(0x7F16, 0x8F91, 0x5C01, 0x9762)
TEXT_COVER_CUSTOM = u(0x81EA, 0x5B9A, 0x4E49, 0x5C01, 0x9762)
TEXT_OK = u(0x786E, 0x5B9A)
TEXT_DONE = u(0x5B8C, 0x6210)
TEXT_CONFIRM = u(0x786E, 0x8BA4)
TEXT_CONFIRM_PUB = u(0x786E, 0x8BA4, 0x53D1, 0x5E03)
TEXT_TIMED = u(0x5B9A, 0x65F6, 0x53D1, 0x5E03)


def write(rel: str, content: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    print("wrote", path)


def rewrite_scanner() -> None:
    write(
        "app/scanner.py",
        f'''from __future__ import annotations

from pathlib import Path
from typing import Any


VIDEO_EXTS = {{".mp4", ".mov", ".webm", ".mkv"}}
COVER_CANDIDATES = (
    "{COVER}.png",
    "{COVER}.jpg",
    "{COVER}.jpeg",
    "{COVER_UP_34}",
    "{COVER_UP_43}",
    "cover.png",
    "cover.jpg",
)


def scan_videos(directory: str) -> list[dict[str, Any]]:
    root = Path(directory).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"{NOT_FOUND_DIR}: {{root}}")

    items: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in VIDEO_EXTS:
            continue
        if path.name.startswith("."):
            continue
        cover = _find_cover(path)
        srt = path.with_suffix(".srt")
        items.append(
            {{
                "name": path.name,
                "path": str(path),
                "size": path.stat().st_size,
                "mtime": int(path.stat().st_mtime * 1000),
                "title": path.stem,
                "coverPath": str(cover) if cover else None,
                "srtPath": str(srt) if srt.is_file() else None,
                "relativeDir": str(path.parent.relative_to(root)),
            }}
        )
    return items


def _find_cover(video: Path) -> Path | None:
    parent = video.parent
    for name in COVER_CANDIDATES:
        p = parent / name
        if p.is_file():
            return p
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        p = video.with_suffix(ext)
        if p.is_file():
            return p
    return None
''',
    )


def rewrite_jobs() -> None:
    write(
        "app/jobs.py",
        f'''from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from app.config import settings


_lock = threading.Lock()


def _job_path(job_id: str) -> Path:
    return Path(settings.data_dir) / "jobs" / f"{{job_id}}.json"


def create_job(payload: dict[str, Any]) -> dict[str, Any]:
    job_id = uuid.uuid4().hex[:12]
    now = int(time.time() * 1000)
    job = {{
        "id": job_id,
        "status": "PENDING",
        "createdAt": now,
        "updatedAt": now,
        "message": "{PENDING}",
        **payload,
    }}
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
''',
    )


def rewrite_publisher() -> None:
    write(
        "app/publisher.py",
        f'''from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Callable

from playwright.async_api import Page, async_playwright

from app.config import settings

logger = logging.getLogger("douyin-auto.publisher")

UPLOAD_URL = "https://creator.douyin.com/creator-micro/content/upload"
HOME_URL = "https://creator.douyin.com/"

ProgressCb = Callable[[str], None]


async def open_login_browser(timeout_sec: int = 300) -> dict[str, Any]:
    """Open creator center for QR login; persist Chromium profile."""
    settings.ensure_dirs()
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(Path(settings.browser_profile_dir).resolve()),
            headless=False,
            viewport={{"width": 1400, "height": 900}},
            locale="zh-CN",
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto(HOME_URL, wait_until="domcontentloaded", timeout=120_000)
        ok = await _wait_logged_in(page, timeout_sec * 1000)
        await context.close()
        if not ok:
            return {{"ok": False, "message": "{LOGIN_FAIL}"}}
        return {{"ok": True, "message": "{LOGIN_OK}"}}


async def check_login() -> dict[str, Any]:
    settings.ensure_dirs()
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(Path(settings.browser_profile_dir).resolve()),
            headless=settings.headless,
            viewport={{"width": 1400, "height": 900}},
            locale="zh-CN",
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else await context.new_page()
        try:
            await page.goto(HOME_URL, wait_until="domcontentloaded", timeout=90_000)
            await page.wait_for_timeout(2000)
            logged_in = await _is_logged_in(page)
            return {{"ok": logged_in, "message": "{LOGIN_OK}" if logged_in else "{LOGIN_NO}"}}
        finally:
            await context.close()


async def publish_video(
    video_path: str,
    title: str | None = None,
    cover_path: str | None = None,
    on_progress: ProgressCb | None = None,
) -> dict[str, Any]:
    video = Path(video_path).expanduser().resolve()
    if not video.is_file():
        raise FileNotFoundError(f"{NOT_FOUND_FILE}: {{video}}")

    title = (title or video.stem).strip()
    cover = Path(cover_path).resolve() if cover_path else None
    if cover and not cover.is_file():
        cover = None

    def progress(msg: str) -> None:
        logger.info(msg)
        if on_progress:
            on_progress(msg)

    settings.ensure_dirs()
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(Path(settings.browser_profile_dir).resolve()),
            headless=settings.headless,
            viewport={{"width": 1400, "height": 900}},
            locale="zh-CN",
            accept_downloads=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else await context.new_page()
        try:
            progress("{OPENING_UPLOAD}")
            await page.goto(UPLOAD_URL, wait_until="domcontentloaded", timeout=120_000)
            await page.wait_for_timeout(2500)

            if not await _is_logged_in(page):
                progress("{NEED_LOGIN}")
                if settings.headless:
                    await context.close()
                    return {{
                        "ok": False,
                        "message": "{HEADLESS_NEED_LOGIN}",
                    }}
                ok = await _wait_logged_in(page, 300_000)
                if not ok:
                    return {{"ok": False, "message": "{LOGIN_TIMEOUT}"}}
                await page.goto(UPLOAD_URL, wait_until="domcontentloaded", timeout=120_000)
                await page.wait_for_timeout(2000)

            progress(f"{TEXT_UPLOAD}: {{video.name}}")
            await _upload_file(page, video)
            progress("{WAIT_PROCESS}")
            await _wait_upload_ready(page)

            progress(f"{FILL_TITLE}: {{title}}")
            await _fill_title(page, title)

            if cover:
                progress(f"{SET_COVER}: {{cover.name}}")
                await _set_cover(page, cover)

            progress("{CLICK_PUBLISH}")
            published = await _click_publish(page)
            if not published:
                return {{
                    "ok": False,
                    "message": "{PUBLISH_BTN_FAIL}",
                }}

            progress("{PUBLISH_OK}")
            await page.wait_for_timeout(3000)
            return {{
                "ok": True,
                "message": "{PUBLISH_OK}",
                "title": title,
                "video": str(video),
                "cover": str(cover) if cover else None,
            }}
        except Exception as e:
            logger.exception("{PUBLISH_FAIL}")
            return {{"ok": False, "message": str(e)}}
        finally:
            await context.close()


async def _is_logged_in(page: Page) -> bool:
    url = page.url or ""
    if "login" in url.lower():
        return False
    selectors = [
        "text={TEXT_PUBLISH}",
        "text={TEXT_CONTENT}",
        "text={TEXT_WORKS}",
        "[class*='avatar']",
        "text={TEXT_HOME}",
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if await loc.count() > 0 and await loc.is_visible():
                return True
        except Exception:
            continue
    cookies = await page.context.cookies()
    names = {{c.get("name") for c in cookies}}
    if {{"sessionid", "sid_guard", "uid_tt"}} & names:
        return True
    return False


async def _wait_logged_in(page: Page, timeout_ms: int) -> bool:
    deadline = asyncio.get_event_loop().time() + timeout_ms / 1000
    while asyncio.get_event_loop().time() < deadline:
        if await _is_logged_in(page):
            return True
        await page.wait_for_timeout(1500)
    return False


async def _upload_file(page: Page, video: Path) -> None:
    inputs = page.locator('input[type="file"]')
    count = await inputs.count()
    if count > 0:
        for i in range(count):
            inp = inputs.nth(i)
            accept = (await inp.get_attribute("accept")) or ""
            if not accept or "video" in accept or "mp4" in accept or "*/*" in accept:
                await inp.set_input_files(str(video))
                return
        await inputs.first.set_input_files(str(video))
        return

    for sel in ("text={TEXT_SELECT}", "text={TEXT_DRAG}", "text={TEXT_CLICK_UPLOAD}", "[class*='upload']"):
        loc = page.locator(sel).first
        if await loc.count() == 0:
            continue
        try:
            async with page.expect_file_chooser(timeout=5000) as fc_info:
                await loc.click()
            chooser = await fc_info.value
            await chooser.set_files(str(video))
            return
        except Exception:
            continue
    raise RuntimeError("{NO_FILE_INPUT}")


async def _wait_upload_ready(page: Page) -> None:
    timeout = settings.upload_timeout_ms
    selectors = [
        'div[contenteditable="true"]',
        "textarea",
        "text={TEXT_DESC}",
        "text={TEXT_PUBLISH}",
        "text={TEXT_COVER_SET}",
    ]
    end = asyncio.get_event_loop().time() + timeout / 1000
    while asyncio.get_event_loop().time() < end:
        for sel in selectors:
            loc = page.locator(sel).first
            try:
                if await loc.count() > 0 and await loc.is_visible():
                    uploading = page.locator("text={UPLOADING}")
                    if await uploading.count() > 0 and await uploading.first.is_visible():
                        break
                    return
            except Exception:
                continue
        await page.wait_for_timeout(1500)
    raise TimeoutError("{UPLOAD_TIMEOUT}")


async def _fill_title(page: Page, title: str) -> None:
    editors = page.locator('div[contenteditable="true"]')
    if await editors.count() > 0:
        ed = editors.first
        await ed.click()
        await page.keyboard.press("Control+A")
        await page.keyboard.type(title[:1000], delay=20)
        return
    areas = page.locator("textarea")
    if await areas.count() > 0:
        await areas.first.fill(title[:1000])
        return
    for sel in ("text={TEXT_TITLE_PH}", "text={TEXT_DESC}", "placeholder={TEXT_TITLE_PH}"):
        loc = page.locator(sel).first
        if await loc.count() == 0:
            continue
        try:
            await loc.click()
            await page.keyboard.type(title[:1000], delay=20)
            return
        except Exception:
            continue
    logger.warning("{TITLE_WARN}")


async def _set_cover(page: Page, cover: Path) -> None:
    for sel in ("text={TEXT_COVER_SEL}", "text={TEXT_COVER_SET}", "text={TEXT_COVER_EDIT}", "text={TEXT_COVER_CUSTOM}"):
        loc = page.locator(sel).first
        if await loc.count() == 0:
            continue
        try:
            await loc.click()
            await page.wait_for_timeout(1000)
            break
        except Exception:
            continue
    else:
        logger.warning("{COVER_WARN}")
        return

    inputs = page.locator('input[type="file"]')
    count = await inputs.count()
    for i in range(count):
        inp = inputs.nth(i)
        accept = (await inp.get_attribute("accept")) or ""
        if "image" in accept or "png" in accept or "jpg" in accept or accept == "":
            try:
                await inp.set_input_files(str(cover))
                await page.wait_for_timeout(1500)
                for ok_sel in ("text={TEXT_OK}", "text={TEXT_DONE}", "text={TEXT_CONFIRM}"):
                    btn = page.locator(ok_sel).first
                    if await btn.count() > 0 and await btn.is_visible():
                        await btn.click()
                        break
                return
            except Exception:
                continue
    logger.warning("{COVER_SET_WARN}")


async def _click_publish(page: Page) -> bool:
    for sel in ("button:has-text('{TEXT_PUBLISH}')", "text={TEXT_PUBLISH}", "[class*='publish']"):
        loc = page.locator(sel).first
        if await loc.count() == 0:
            continue
        try:
            if not await loc.is_visible():
                continue
            text = (await loc.inner_text()).strip()
            if "{TEXT_TIMED}" in text:
                continue
            await loc.click()
            await page.wait_for_timeout(2000)
            for confirm in ("button:has-text('{TEXT_CONFIRM_PUB}')", "text={TEXT_CONFIRM_PUB}", "text={TEXT_CONFIRM}"):
                c = page.locator(confirm).first
                if await c.count() > 0 and await c.is_visible():
                    await c.click()
                    await page.wait_for_timeout(1500)
            return True
        except Exception:
            continue
    return False
''',
    )


def rewrite_main() -> None:
    write(
        "app/main.py",
        f'''from __future__ import annotations

import asyncio
import logging
import threading
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import jobs, scanner
from app.config import settings
from app.publisher import check_login, open_login_browser, publish_video

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("douyin-auto")

app = FastAPI(title="{DOUYIN}{DIR_UPLOAD}", version="1.0.0")

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
    directory: str | None = None


@app.get("/")
async def index() -> FileResponse:
    index_html = STATIC_DIR / "index.html"
    if not index_html.is_file():
        raise HTTPException(404, "{NOT_FOUND_PAGE}")
    return FileResponse(index_html)


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {{"ok": True, "port": settings.server_port}}


@app.get("/api/settings")
async def get_settings() -> dict[str, Any]:
    return {{
        "videoDir": settings.video_dir,
        "headless": settings.headless,
        "browserProfileDir": str(Path(settings.browser_profile_dir).resolve()),
        "uploadTimeoutMs": settings.upload_timeout_ms,
    }}


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
        raise HTTPException(400, "{PLEASE_SET_DIR}")
    try:
        items = scanner.scan_videos(directory)
    except FileNotFoundError as e:
        raise HTTPException(400, str(e)) from e
    return {{"directory": str(Path(directory).expanduser().resolve()), "total": len(items), "list": items}}


@app.get("/api/login/status")
async def login_status() -> dict[str, Any]:
    return await check_login()


@app.post("/api/login")
async def login() -> dict[str, Any]:
    old = settings.headless
    settings.headless = False
    try:
        return await open_login_browser(timeout_sec=300)
    finally:
        settings.headless = old


@app.get("/api/jobs")
async def job_list() -> dict[str, Any]:
    return {{"list": jobs.list_jobs()}}


@app.get("/api/jobs/{{job_id}}")
async def job_get(job_id: str) -> dict[str, Any]:
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(404, "{NOT_FOUND_JOB}")
    return job


@app.post("/api/publish")
async def publish(body: PublishRequest) -> dict[str, Any]:
    video = Path(body.videoPath).expanduser()
    if not video.is_file():
        raise HTTPException(400, f"{NOT_FOUND_FILE}: {{video}}")

    title = body.title or video.stem
    cover = body.coverPath
    if not cover:
        try:
            found = scanner.scan_videos(str(video.parent))
            for it in found:
                if Path(it["path"]).resolve() == video.resolve():
                    cover = it.get("coverPath")
                    break
        except Exception:
            cover = None

    job = jobs.create_job(
        {{
            "videoPath": str(video.resolve()),
            "title": title,
            "coverPath": cover,
            "status": "RUNNING",
            "message": "{QUEUED}",
        }}
    )
    job_id = job["id"]

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
                    on_progress=on_progress,
                )
            )
            jobs.update_job(
                job_id,
                status="SUCCESS" if result.get("ok") else "FAILED",
                message=result.get("message") or "",
                result=result,
            )
        except Exception as e:
            logger.exception("publish job failed")
            jobs.update_job(job_id, status="FAILED", message=str(e))

    threading.Thread(target=runner, name=f"douyin-publish-{{job_id}}", daemon=True).start()
    return {{"jobId": job_id, "job": job}}


def _persist_env() -> None:
    env_path = Path(".env")
    lines: list[str] = []
    if env_path.is_file():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    kv = {{
        "SERVER_PORT": str(settings.server_port),
        "VIDEO_DIR": settings.video_dir,
        "HEADLESS": "true" if settings.headless else "false",
        "BROWSER_PROFILE_DIR": settings.browser_profile_dir,
        "DATA_DIR": settings.data_dir,
        "UPLOAD_TIMEOUT_MS": str(settings.upload_timeout_ms),
    }}
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        if "=" in line and not line.strip().startswith("#"):
            key = line.split("=", 1)[0].strip()
            if key in kv:
                out.append(f"{{key}}={{kv[key]}}")
                seen.add(key)
                continue
        out.append(line)
    for k, v in kv.items():
        if k not in seen:
            out.append(f"{{k}}={{v}}")
    env_path.write_text("\\n".join(out) + "\\n", encoding="utf-8")


@app.on_event("startup")
async def on_startup() -> None:
    settings.ensure_dirs()
    logger.info("douyin-auto ready on :%s video_dir=%s", settings.server_port, settings.video_dir or "(empty)")
''',
    )


def rewrite_env_example() -> None:
    write(
        ".env.example",
        f"""# {DOUYIN}{DIR_UPLOAD}
SERVER_PORT=12500

# {u(0x89C6, 0x9891)}{u(0x76EE, 0x5F55)} {u(0xFF08)}{u(0x7EDD, 0x5BF9, 0x8DEF, 0x5F84)}{u(0xFF09)}
VIDEO_DIR=

# Playwright headless: false = show browser for QR login
HEADLESS=false

# Chromium persistent profile (login state)
BROWSER_PROFILE_DIR=./data/browser-profile

# Job / runtime data
DATA_DIR=./data

# Upload wait timeout (ms)
UPLOAD_TIMEOUT_MS=300000
""",
    )


def rewrite_readme() -> None:
    ep29_mp4 = u(0x6280, 0x672F, 0x6808) + "EP.29" + u(0x6559, 0x7A0B) + ".mp4"
    write(
        "README.md",
        f"""# {DOUYIN}{DIR_UPLOAD} (Playwright)

{u(0x65B9, 0x6848)} B: {u(0x72EC, 0x7ACB)} FastAPI {u(0x540E, 0x53F0)} + Playwright {u(0x81EA, 0x52A8)} {u(0x4E0A, 0x4F20)} {u(0x521B, 0x4F5C, 0x8005, 0x4E2D, 0x5FC3)}.

> {u(0x975E, 0x5B98, 0x65B9)} OpenAPI, {u(0x4F9D, 0x8D56)} {u(0x9875, 0x9762)} DOM, {u(0x4E0A, 0x7EBF)} UI {u(0x53D8, 0x66F4)} {u(0x65F6)} {u(0x53EF, 0x80FD)} {u(0x9700, 0x8C03)} selector.
> {u(0x767B, 0x5F55)} {u(0x6001)} {u(0x4FDD, 0x5B58)} {u(0x5728)} `data/browser-profile`, {u(0x52FF)} {u(0x63D0, 0x4EA4)} {u(0x5230)} git.

## {u(0x542F, 0x52A8)}

```powershell
cd E:\\ai-pro\\project_agent\\python\\douyin-auto
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
playwright install chromium
copy .env.example .env
# edit .env VIDEO_DIR=.../video_html
python run.py
```

{u(0x540E, 0x53F0)}: http://127.0.0.1:12500

## {u(0x4F7F, 0x7528)}

1. {u(0x586B)} {u(0x89C6, 0x9891)}{u(0x76EE, 0x5F55)} ({u(0x4F8B)} `.../EP29_wechat_voice/video_html`) -> **{u(0x4FDD, 0x5B58, 0x5E76, 0x626B, 0x63CF)}**
2. **{u(0x626B, 0x7801, 0x767B, 0x5F55)}** -> Chromium {u(0x5F39, 0x7A97)} {u(0x767B)} {u(0x521B, 0x4F5C, 0x8005, 0x4E2D, 0x5FC3)}
3. {u(0x627E)} `{ep29_mp4}` - **{u(0x53D1, 0x5E03, 0x5230)}{DOUYIN}**
4. {u(0x540C, 0x76EE, 0x5F55)} {COVER}.png / {COVER_UP_34} {u(0x4F1A)} {u(0x81EA, 0x52A8)} {u(0x9009)} {u(0x4E3A)} {u(0x5C01, 0x9762)}

## {u(0x6CE8, 0x610F)}

- {u(0x9996, 0x6B21)} {u(0x4FDD, 0x6301)} `HEADLESS=false`
- {u(0x53D1, 0x5E03)} {u(0x524D)} {u(0x8BF7)} {u(0x786E, 0x8BA4)} {u(0x6807, 0x9898)}/{u(0x5C01, 0x9762)}/{u(0x5408, 0x89C4)}
- {u(0x4EC5)} {u(0x7528)} {u(0x4E8E)} {u(0x81EA, 0x5DF1)} {u(0x8D26, 0x53F7)} {u(0x5185, 0x5BB9)}
""",
    )


def fix_gen_web_scaninfo() -> None:
    path = ROOT / "scripts" / "gen_web.py"
    text = path.read_text(encoding="utf-8")
    old = "$('scanInfo').textContent = data.directory + "
    # rewrite any broken separator to pipe
    import re

    text2 = re.sub(
        r"\$\('scanInfo'\)\.textContent = data\.directory \+ .*? \+ data\.total;",
        "$('scanInfo').textContent = data.directory + ' | ' + data.total;",
        text,
    )
    path.write_text(text2, encoding="utf-8")
    print("fixed gen_web scanInfo")


def main() -> None:
    rewrite_scanner()
    rewrite_jobs()
    rewrite_publisher()
    rewrite_main()
    rewrite_env_example()
    rewrite_readme()
    fix_gen_web_scaninfo()
    # regenerate html
    import runpy

    runpy.run_path(str(ROOT / "scripts" / "gen_web.py"), run_name="__main__")
    html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
    assert DOUYIN in html, "html missing douyin title"
    print("all ok")


if __name__ == "__main__":
    main()
