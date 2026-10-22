from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any, Callable

from playwright.async_api import Page, async_playwright

from app.config import settings
from app.browser_gate import BrowserGate
from app.cover_check import collect_cover_state
from app.publish_confirmation import check_management, find_work, is_publish_request, submission_evidence

logger = logging.getLogger("douyin-auto.publisher")

UPLOAD_URL = "https://creator.douyin.com/creator-micro/content/upload"
HOME_URL = "https://creator.douyin.com/"
MANAGE_URL = "https://creator.douyin.com/creator-micro/content/manage"

ProgressCb = Callable[[str], None]

# One Chromium profile cannot be opened twice; serialize all browser ops.
_browser_gate = BrowserGate()
_login_cache: dict[str, Any] = {"at": 0.0, "result": None}
# Memory TTL for skipping Playwright; disk keeps last known status across restarts.
_LOGIN_CACHE_TTL_SEC = 90.0
_LOGIN_DISK_TTL_SEC = 12 * 3600.0  # 12h — UI/restart soft status


def _profile_dir() -> str:
    return str(Path(settings.browser_profile_dir).resolve())


def _login_status_path() -> Path:
    return Path(settings.data_dir) / "login_status.json"


def _load_login_disk() -> dict[str, Any] | None:
    path = _login_status_path()
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        at = float(data.get("at") or 0)
        result = data.get("result")
        if not isinstance(result, dict):
            return None
        return {"at": at, "result": result}
    except Exception:
        return None


def _save_login_disk(result: dict[str, Any]) -> None:
    path = _login_status_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"at": time.time(), "result": {"ok": bool(result.get("ok")), "message": result.get("message") or ""}}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _login_cache["at"] = payload["at"]
    _login_cache["result"] = dict(payload["result"])


def _remember_login(result: dict[str, Any], *, persist: bool = True) -> dict[str, Any]:
    out = {"ok": bool(result.get("ok")), "message": result.get("message") or ("已登录" if result.get("ok") else "未登录")}
    _login_cache["at"] = time.time()
    _login_cache["result"] = dict(out)
    if persist:
        try:
            _save_login_disk(out)
        except Exception:
            logger.exception("save login_status.json failed")
    return dict(out)


def bootstrap_login_cache() -> dict[str, Any] | None:
    """Load disk login status into memory after process restart."""
    disk = _load_login_disk()
    if not disk:
        return None
    _login_cache["at"] = float(disk.get("at") or 0)
    _login_cache["result"] = disk.get("result")
    return dict(_login_cache["result"] or {})


def browser_busy() -> dict[str, Any]:
    return _browser_gate.status()


def _try_acquire(holder: str, *, wait_sec: float = 0) -> bool:
    return _browser_gate.acquire(holder, wait_sec=wait_sec)


def _release() -> None:
    _browser_gate.release()


async def _wait_for_publish_browser(
    progress: ProgressCb, *, timeout_sec: float | None = None,
) -> bool:
    """Wait without blocking an executor or acquiring the profile after cancellation."""
    timeout = settings.browser_wait_timeout_sec if timeout_sec is None else timeout_sec
    ticket = _browser_gate.enqueue_publish()
    deadline = time.monotonic() + timeout
    last_report = 0.0
    try:
        while True:
            if _browser_gate.acquire_publish(ticket):
                return True
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            if time.monotonic() - last_report >= 5:
                info = browser_busy()
                holder = {"keepalive": "登录保活", "login": "扫码登录", "publish": "上一条发布"}.get(
                    info.get("holder"), "其他浏览器操作"
                )
                progress(f"等待浏览器：{holder}进行中，已排队（共 {info['waitingPublish']} 个任务等待）")
                last_report = time.monotonic()
            await asyncio.sleep(min(0.5, remaining))
    finally:
        _browser_gate.cancel_publish(ticket)


async def open_login_browser(timeout_sec: int = 300) -> dict[str, Any]:
    """Open creator center for QR login; wait for browser lock (status/publish)."""
    # Wait up to 90s if status check / publish is holding the profile.
    if not await asyncio.to_thread(_try_acquire, "login", wait_sec=90.0):
        info = browser_busy()
        return {
            "ok": False,
            "message": f"浏览器忙碌中（{info.get('holder') or 'unknown'}），请稍后再试",
        }
    try:
        settings.ensure_dirs()
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=_profile_dir(),
                headless=False,
                viewport={"width": 1400, "height": 900},
                locale="zh-CN",
                args=["--disable-blink-features=AutomationControlled"],
            )
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto(HOME_URL, wait_until="domcontentloaded", timeout=120_000)
            ok = await _wait_logged_in(page, timeout_sec * 1000)
            await context.close()
            if not ok:
                return _remember_login({"ok": False, "message": "登录失败或超时"}, persist=True)
            return _remember_login({"ok": True, "message": "已登录"}, persist=True)
    except Exception as e:
        logger.exception("open_login_browser failed")
        return {"ok": False, "message": f"登录异常: {e}"}
    finally:
        _release()


def _cached_login(now: float | None = None, *, allow_disk: bool = True) -> dict[str, Any] | None:
    now = time.time() if now is None else now
    cached = _login_cache.get("result")
    at = float(_login_cache.get("at") or 0)
    if cached is not None and now - at < _LOGIN_CACHE_TTL_SEC:
        out = dict(cached)
        out["cached"] = True
        return out
    if not allow_disk:
        return None
    disk = _load_login_disk()
    if not disk:
        return None
    # Restore into memory after restart
    _login_cache["at"] = float(disk.get("at") or 0)
    _login_cache["result"] = disk.get("result")
    age = now - float(disk.get("at") or 0)
    result = disk.get("result") or {}
    if age <= _LOGIN_DISK_TTL_SEC and result.get("ok"):
        out = dict(result)
        out["cached"] = True
        out["fromDisk"] = True
        return out
    if age <= _LOGIN_CACHE_TTL_SEC:
        out = dict(result)
        out["cached"] = True
        out["fromDisk"] = True
        return out
    return None


async def refresh_session() -> dict[str, Any]:
    """Keepalive: headed off-screen visit to refresh Douyin cookies.

    Headless probes do NOT renew session (Douyin ignores/kills them). This opens a
    real Chromium window off-screen, hits home + content manage, then closes.
    """
    # A background probe must not queue ahead of publishing or a QR login.
    if not _try_acquire("keepalive"):
        info = browser_busy()
        return {
            "ok": False,
            "busy": True,
            "message": f"浏览器忙碌（{info.get('holder') or 'busy'}），稍后重试",
        }

    try:
        settings.ensure_dirs()
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=_profile_dir(),
                headless=False,
                viewport={"width": 1280, "height": 800},
                locale="zh-CN",
                args=[
                    "--disable-blink-features=AutomationControlled",
                    # Park window off-screen so keepalive is not disruptive
                    "--window-position=-32000,-32000",
                    "--window-size=1280,800",
                ],
            )
            page = context.pages[0] if context.pages else await context.new_page()
            try:
                try:
                    await page.goto(HOME_URL, wait_until="domcontentloaded", timeout=90_000)
                except Exception as e:
                    logger.warning("keepalive home goto: %s", e)
                await page.wait_for_timeout(2500)

                # Second hit: content manage — stronger session touch
                try:
                    await page.goto(MANAGE_URL, wait_until="domcontentloaded", timeout=90_000)
                    await page.wait_for_timeout(2500)
                except Exception as e:
                    logger.warning("keepalive manage goto: %s", e)

                # Light interaction to look less like a dead probe
                try:
                    await page.mouse.move(200, 200)
                    await page.evaluate("window.scrollTo(0, 300)")
                    await page.wait_for_timeout(800)
                except Exception:
                    pass

                logged_in = await _is_logged_in(page)
                cookies = await page.context.cookies()
                names = {c.get("name") for c in cookies}
                has_sess = bool({"sessionid", "sid_guard", "uid_tt"} & names)

                if logged_in:
                    return _remember_login({"ok": True, "message": "保活成功·已登录"}, persist=True)
                if has_sess:
                    # Cookies present but UI not confirmed — still count as soft success
                    # so we don't wipe a session that renews slowly.
                    out = _remember_login(
                        {"ok": True, "message": "保活完成·cookie仍在"},
                        persist=True,
                    )
                    return out
                return _remember_login(
                    {"ok": False, "message": "保活失败·未登录，请重新扫码"},
                    persist=True,
                )
            finally:
                await context.close()
    except Exception as e:
        logger.exception("refresh_session failed")
        return {"ok": False, "message": f"保活异常: {e}"}
    finally:
        _release()


async def check_login(force: bool = False, soft: bool = False) -> dict[str, Any]:
    """Probe login (UI). Prefer cache; force opens headed off-screen (same as keepalive).

    - soft/default after restart: prefer disk/memory cache so UI won't flash 未登录
    - force=True: real browser probe (not headless — Douyin rejects headless)
    """
    now = time.time()
    if not force:
        hit = _cached_login(now, allow_disk=True)
        if hit is not None:
            if soft or hit.get("ok") or hit.get("fromDisk"):
                return hit
        if soft:
            return {"ok": False, "message": "尚未检测（点刷新状态或扫码登录）", "cached": True}

    # Manual「刷新状态」: reuse refresh_session (headed) instead of headless.
    return await refresh_session()


async def publish_video(
    video_path: str,
    title: str | None = None,
    cover_path: str | None = None,
    cover_path_v: str | None = None,
    cover_path_h: str | None = None,
    description: str | None = None,
    location: str | None = None,
    on_progress: ProgressCb | None = None,
    on_submit: Callable[[], None] | None = None,
) -> dict[str, Any]:
    video = Path(video_path).expanduser().resolve()
    if not video.is_file():
        raise FileNotFoundError(f"文件不存在: {video}")

    title = (title or video.stem).strip()
    desc = (description or "").strip() or None
    cover_v = Path(cover_path_v).resolve() if cover_path_v else None
    cover_h = Path(cover_path_h).resolve() if cover_path_h else None
    cover = Path(cover_path).resolve() if cover_path else None
    if cover_v and not cover_v.is_file():
        cover_v = None
    if cover_h and not cover_h.is_file():
        cover_h = None
    if cover and not cover.is_file():
        cover = None
    if not cover_v and cover:
        cover_v = cover
    if not cover_h and cover:
        cover_h = cover
    location = (location if location is not None else settings.default_location).strip()

    def progress(msg: str) -> None:
        logger.info(msg)
        if on_progress:
            on_progress(msg)

    if not await _wait_for_publish_browser(progress):
        return {
            "ok": False,
            "stage": "browser_wait",
            "retryable": True,
            "message": "等待浏览器超时，尚未上传或发布，请等待当前浏览器操作结束后重试",
        }

    # Always show browser for publish so user can finish captcha / see blockers.
    use_headless = False
    attempted = False

    def submitting() -> None:
        nonlocal attempted
        attempted = True
        if on_submit:
            on_submit()

    try:
        settings.ensure_dirs()
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=_profile_dir(),
                headless=use_headless,
                viewport={"width": 1400, "height": 900},
                locale="zh-CN",
                accept_downloads=True,
                args=["--disable-blink-features=AutomationControlled"],
            )
            page = context.pages[0] if context.pages else await context.new_page()
            try:
                progress("打开上传页...")
                await page.goto(UPLOAD_URL, wait_until="domcontentloaded", timeout=120_000)
                await page.wait_for_timeout(2500)

                if not await _is_logged_in(page):
                    progress("需要登录，请在浏览器中扫码...")
                    if settings.headless:
                        return {
                            "ok": False,
                            "message": "未登录，HEADLESS=true时无法扫码，请先调用 /api/login",
                        }
                    ok = await _wait_logged_in(page, 300_000)
                    if not ok:
                        return {"ok": False, "message": "登录超时"}
                    await page.goto(UPLOAD_URL, wait_until="domcontentloaded", timeout=120_000)
                    await page.wait_for_timeout(2000)

                progress(f"上传: {video.name}")
                await _upload_file(page, video)
                progress("等待进入发布编辑页（不等AI封面）...")
                await _wait_upload_ready(page, progress)
                await _dismiss_guides(page)
                await _save_debug_shot(page, "form_ready")

                progress(f"填写标题/简介(含话题): {title}")
                ok_meta = await _fill_title(page, title, description=desc)
                if not ok_meta.get("title"):
                    progress("标题为空，重试等待表单并再填一次...")
                    await page.wait_for_timeout(2000)
                    if await _form_ready(page):
                        ok_meta = await _fill_title(page, title, description=desc)
                await _dismiss_guides(page)

                ok_cover = True
                cover_check: dict[str, Any] | None = None
                if cover_v or cover_h:
                    progress("分别上传横/竖封面(跳过AI)...")
                    upload_confirmed = await _set_covers(page, cover_v=cover_v, cover_h=cover_h, progress=progress)
                    await _dismiss_guides(page)
                    await _close_cover_modal_if_open(page)
                    cover_check = await _verify_covers(
                        page,
                        expect_v=bool(cover_v),
                        expect_h=bool(cover_h),
                        progress=progress,
                    )
                    cover_check["uploadConfirmed"] = upload_confirmed
                    ok_cover = upload_confirmed and bool(cover_check.get("ok"))
                    if not ok_cover:
                        progress(f"封面质检未通过: {cover_check.get('reason')}")
                    else:
                        progress("封面预览已确认并稳定")

                if location:
                    progress(f"设置定位: {location}")
                    await _set_location(page, location)

                # Gate: never click 发布 until title + cover + topics OK
                missing: list[str] = []
                title_now = await _read_title_text(page)
                if not ok_meta.get("title") or not (title_now or "").strip():
                    missing.append("标题为空")
                if (cover_v or cover_h) and not ok_cover:
                    missing.append(
                        "封面选图或保存未完成" if not (cover_check or {}).get("uploadConfirmed")
                        else "封面预览未确认（详见检测记录）"
                    )
                if not ok_meta.get("topics"):
                    missing.append("话题未写入作品简介")
                if await _cover_modal_open(page):
                    missing.append("封面设置弹窗仍打开")
                if missing:
                    screenshot = await _save_debug_shot(page, "prepublish_blocked")
                    msg = "；".join(missing) + " — 未点击发布，请检查后重试"
                    progress(msg)
                    return {
                        "ok": False,
                        "message": msg,
                        "stage": "prepublish_check",
                        "coverCheck": cover_check,
                        "screenshot": screenshot,
                        "title": title,
                        "video": str(video),
                        "coverV": str(cover_v) if cover_v else None,
                        "coverH": str(cover_h) if cover_h else None,
                        "location": location or None,
                        "url": page.url,
                    }

                progress("处理发布前勾选（AI声明等）...")
                await _prepare_before_publish(page)
                await _dismiss_guides(page)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(800)

                progress("表单已确认，点击发布并等待跳转作品管理...")
                publish_result = await _click_publish_and_confirm(page, progress, expected_title=title, on_submit=submitting)
                if not publish_result.get("ok"):
                    await _save_debug_shot(page, "publish_unconfirmed")
                    return {
                        "ok": False,
                        "unconfirmed": bool(publish_result.get("unconfirmed")),
                        "publishAttempted": attempted,
                        "stage": "publish_confirmation",
                        "message": publish_result.get("message")
                        or "已点发布但未确认成功，请到创作者中心「作品管理」核对",
                        "title": title,
                        "video": str(video),
                        "cover": str(cover_v or cover_h) if (cover_v or cover_h) else None,
                        "coverV": str(cover_v) if cover_v else None,
                        "coverH": str(cover_h) if cover_h else None,
                        "location": location or None,
                        "url": publish_result.get("url"),
                    }

                progress(publish_result.get("message") or "发布成功")
                result = {
                    "ok": True,
                    "message": publish_result.get("message") or "发布成功",
                    "coverCheck": cover_check,
                    "publishEvidence": publish_result.get("evidence"),
                    "title": title,
                    "video": str(video),
                    "cover": str(cover_v or cover_h) if (cover_v or cover_h) else None,
                    "coverV": str(cover_v) if cover_v else None,
                    "coverH": str(cover_h) if cover_h else None,
                    "location": location or None,
                    "url": publish_result.get("url"),
                }
                _remember_login({"ok": True, "message": "已登录"}, persist=True)
                return result
            except Exception as e:
                logger.exception("发布失败")
                return {
                    "ok": False, "unconfirmed": attempted, "publishAttempted": attempted,
                    "message": ("已尝试提交发布，但浏览器中断，结果待核对，请勿重复发布" if attempted else str(e)),
                    "error": str(e),
                }
            finally:
                await _close_publish_context(context)
    finally:
        _release()


async def _close_publish_context(context) -> None:
    """Cleanup must never replace the actual submission result with a close error."""
    try:
        await asyncio.wait_for(context.close(), timeout=10)
    except Exception as e:
        logger.warning("publish browser cleanup: %s", e)


async def verify_published_video(title: str) -> dict[str, Any]:
    """Read management with the existing profile; never upload or press publish."""
    if not _try_acquire("verify"):
        return {"ok": False, "busy": True, "message": "浏览器正在使用，请稍后核对"}
    try:
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=_profile_dir(), headless=False,
                viewport={"width": 1400, "height": 900}, locale="zh-CN",
                args=["--disable-blink-features=AutomationControlled", "--window-position=-32000,-32000"],
            )
            try:
                page = context.pages[0] if context.pages else await context.new_page()
                evidence = await check_management(page, title)
                shot = await _save_debug_shot(page, "management_verification")
                return {"ok": bool(evidence), "evidence": evidence, "screenshot": shot,
                        "message": "已在作品管理核对到该标题" if evidence else "作品管理暂未确认该标题，仍需人工核对"}
            finally:
                await _close_publish_context(context)
    finally:
        _release()


async def _has_login_modal(page: Page) -> bool:
    for sel in ("text=扫码登录", "text=手机号登录", "text=验证码登录"):
        try:
            loc = page.locator(sel).first
            if await loc.count() > 0 and await loc.is_visible():
                return True
        except Exception:
            continue
    return False


async def _is_logged_in(page: Page) -> bool:
    url = page.url or ""
    if "login" in url.lower():
        return False
    if await _has_login_modal(page):
        return False
    cookies = await page.context.cookies()
    names = {c.get("name") for c in cookies}
    if not ({"sessionid", "sid_guard", "uid_tt"} & names):
        return False
    selectors = [
        "text=内容管理",
        "text=作品管理",
        "[class*='avatar']",
        "text=上传视频",
        "text=发布视频",
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if await loc.count() > 0 and await loc.is_visible():
                return True
        except Exception:
            continue
    # cookie present and no login modal counts as logged in
    return True


async def _wait_logged_in(page: Page, timeout_ms: int) -> bool:
    deadline = asyncio.get_event_loop().time() + timeout_ms / 1000
    while asyncio.get_event_loop().time() < deadline:
        if await _is_logged_in(page):
            return True
        await page.wait_for_timeout(1500)
    return False


async def _find_file_input(page: Page):
    """Search main page + iframes (Douyin uploader often lives in x-storage-web)."""
    frames = [page] + list(page.frames)
    # Prefer storage uploader frames
    frames.sort(key=lambda f: (0 if "x-storage" in ((f.url or "") if f != page else page.url) else 1))
    for frame in frames:
        try:
            inputs = frame.locator('input[type="file"]')
            count = await inputs.count()
        except Exception:
            continue
        for i in range(count):
            inp = inputs.nth(i)
            try:
                accept = ((await inp.get_attribute("accept")) or "").lower()
            except Exception:
                accept = ""
            if not accept or "video" in accept or "mp4" in accept or "*/*" in accept or "image" not in accept:
                return inp
    return None


async def _upload_file(page: Page, video: Path) -> None:
    if await _has_login_modal(page):
        raise RuntimeError("未登录创作者中心，请先点「扫码登录」完成登录后再发布")

    deadline = asyncio.get_event_loop().time() + 45
    while asyncio.get_event_loop().time() < deadline:
        if await _has_login_modal(page):
            raise RuntimeError("未登录创作者中心，请先点「扫码登录」完成登录后再发布")
        inp = await _find_file_input(page)
        if inp is not None:
            await inp.set_input_files(str(video))
            return
        for sel in (
            "text=上传视频",
            "text=点击上传",
            "text=选择视频",
            "text=拖拽视频",
            "[class*='upload']",
        ):
            loc = page.locator(sel).first
            try:
                if await loc.count() == 0 or not await loc.is_visible():
                    continue
                async with page.expect_file_chooser(timeout=4000) as fc_info:
                    await loc.click()
                chooser = await fc_info.value
                await chooser.set_files(str(video))
                return
            except Exception:
                continue
        await page.wait_for_timeout(1500)

    raise RuntimeError("未找到上传控件（页面可能未登录或上传区未加载）")


async def _page_still_loading(page: Page) -> bool:
    for sel in (
        "text=加载中，请稍候",
        "text=加载中",
        "text=请稍候",
        "[class*='loading']:visible",
        "[class*='spin']:visible",
    ):
        loc = page.locator(sel).first
        try:
            if await loc.count() > 0 and await loc.is_visible():
                # Ignore tiny spinners in cover AI area if title already present
                txt = ""
                try:
                    txt = (await loc.inner_text()).strip()
                except Exception:
                    txt = ""
                if "加载中" in txt or "请稍候" in txt:
                    return True
        except Exception:
            continue
    return False


async def _title_editor(page: Page):
    """Locate the short-title editor (≤30). Prefer placeholder 填写作品标题."""
    selectors = (
        'div[contenteditable="true"][data-placeholder*="填写作品标题"]',
        'div[contenteditable="true"][data-placeholder*="作品标题"]',
        '[data-placeholder*="填写作品标题"]',
        '[placeholder*="填写作品标题"]',
        'input[placeholder*="作品标题"]',
        'div[contenteditable="true"][data-placeholder*="标题"]',
        'div[contenteditable="true"][data-placeholder*="推荐"]',
    )
    for sel in selectors:
        loc = page.locator(sel)
        try:
            for i in range(await loc.count()):
                ed = loc.nth(i)
                if await ed.is_visible():
                    return ed
        except Exception:
            continue
    return None


async def _form_ready(page: Page) -> bool:
    """True only when edit form widgets are actually interactable (not blank loading)."""
    if await _page_still_loading(page):
        return False
    title_ed = await _title_editor(page)
    if title_ed is None:
        return False
    # Need at least one of cover / description markers
    for sel in (
        "text=设置封面",
        "text=作品描述",
        "text=添加作品简介",
        "text=竖封面",
        "text=横封面",
        "text=上传封面",
        "text=选择封面",
    ):
        loc = page.locator(sel).first
        try:
            if await loc.count() > 0 and await loc.is_visible():
                return True
        except Exception:
            continue
    return False


async def _video_still_uploading(page: Page) -> bool:
    """True while right-rail shows upload progress (上传中 / xx% / MB/s)."""
    for sel in (
        "text=上传中",
        "text=请勿删除",
        "text=请勿删除/移动文件",
    ):
        loc = page.locator(sel).first
        try:
            if await loc.count() > 0 and await loc.is_visible():
                return True
        except Exception:
            continue
    try:
        # e.g. "59%" next to progress while bytes still climbing
        pct = page.locator("text=/\\d{1,3}%/").first
        if await pct.count() > 0 and await pct.is_visible():
            text = (await pct.inner_text()).strip()
            num = "".join(ch for ch in text if ch.isdigit())
            if num and int(num) < 100:
                # Only treat as uploading if speed / size hint also present
                for hint in ("MB/s", "KB/s", "MB/", "KB/"):
                    if await page.locator(f"text={hint}").count() > 0:
                        return True
    except Exception:
        pass
    return False


async def _wait_upload_ready(page: Page, progress: ProgressCb | None = None) -> None:
    """Wait until publish form is ready AND video file upload finished."""
    hard_cap = min(float(settings.upload_timeout_ms) / 1000.0, 300.0)
    end = time.time() + hard_cap
    last_log = 0.0
    while time.time() < end:
        await _dismiss_guides(page)
        if await _page_still_loading(page):
            if progress and time.time() - last_log > 5:
                progress("编辑页加载中，请稍候...")
                last_log = time.time()
            await page.wait_for_timeout(1500)
            continue
        if await _form_ready(page):
            if await _video_still_uploading(page):
                if progress and time.time() - last_log > 5:
                    progress("视频仍在上传中，等传完再设封面...")
                    last_log = time.time()
                await page.wait_for_timeout(1500)
                continue
            # Stabilize: require title editor still present after short wait
            await page.wait_for_timeout(1200)
            if await _form_ready(page) and not await _video_still_uploading(page):
                return
        if progress and time.time() - last_log > 8:
            progress(f"等待编辑页就绪... url={(page.url or '')[-60:]}")
            last_log = time.time()
        await page.wait_for_timeout(1500)

    await _save_debug_shot(page, "wait_form_timeout")
    if progress:
        progress("编辑页等待超时（标题区未就绪），将尝试填表但可能失败")


async def _dismiss_guides(page: Page) -> None:
    """Close Douyin onboarding / preview tips that block clicks."""
    for sel in (
        "button:has-text('我知道了')",
        "text=我知道了",
        "button:has-text('知道了')",
        "text=暂不使用",
        "text=跳过",
    ):
        loc = page.locator(sel).first
        try:
            if await loc.count() == 0 or not await loc.is_visible():
                continue
            await loc.click(timeout=1200)
            await page.wait_for_timeout(250)
        except Exception:
            continue


async def _read_title_text(page: Page) -> str:
    ed = await _title_editor(page)
    if ed is None:
        return ""
    try:
        tag = (await ed.evaluate("e => (e.tagName||'').toLowerCase()")).strip()
        if tag == "input" or tag == "textarea":
            return ((await ed.input_value()) or "").strip()
        return ((await ed.inner_text()) or "").strip()
    except Exception:
        return ""


async def _fill_title(page: Page, title: str, description: str | None = None) -> dict[str, bool]:
    """Fill short title (≤30); put #ai编程 #干货 at the END of 作品简介."""
    from app.scanner import _build_description

    await _dismiss_guides(page)
    full = (title or "").strip()
    short = full[:30]
    desc = (description or "").strip() or _build_description(full)
    tags = settings.publish_hashtag_list or ["#ai编程", "#干货"]
    desc_body = desc
    for t in tags:
        desc_body = desc_body.replace(t, "").strip()
    desc_body = "\n".join(ln for ln in desc_body.splitlines() if ln.strip()).strip() or short

    async def fill_editor(ed, text: str) -> bool:
        try:
            if not await ed.is_visible():
                return False
            await ed.click(timeout=2000)
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Backspace")
            # Prefer fill() for contenteditable/input when supported
            try:
                await ed.fill(text)
            except Exception:
                await page.keyboard.type(text, delay=15)
            await page.wait_for_timeout(300)
            return True
        except Exception:
            return False

    title_filled = False
    title_ed = await _title_editor(page)
    if title_ed is not None:
        title_filled = await fill_editor(title_ed, short)
        # Verify — Douyin sometimes swallows input while still hydrating
        await page.wait_for_timeout(400)
        got = await _read_title_text(page)
        if not got or (short[:8] not in got and got[:8] not in short):
            title_filled = await fill_editor(title_ed, short)
            got = await _read_title_text(page)
        title_filled = bool(got.strip()) and (short[:6] in got or got[:6] in short)
        if not title_filled:
            logger.warning("标题填写后读回为空/不匹配 got=%r want=%r", got, short)

    desc_sels = (
        'div[contenteditable="true"][data-placeholder*="简介"]',
        'div[contenteditable="true"][data-placeholder*="描述"]',
        '[data-placeholder*="添加作品简介"]',
        '[placeholder*="添加作品简介"]',
        '[data-placeholder*="作品描述"]',
        '[placeholder*="作品描述"]',
        'textarea[placeholder*="简介"]',
        'textarea[placeholder*="描述"]',
    )
    desc_filled = False
    desc_ed = None
    for sel in desc_sels:
        loc = page.locator(sel)
        try:
            for i in range(await loc.count()):
                ed = loc.nth(i)
                if await fill_editor(ed, desc_body[:900]):
                    desc_filled = True
                    desc_ed = ed
                    break
        except Exception:
            continue
        if desc_filled:
            break

    if not desc_filled:
        try:
            hint = page.locator("text=添加作品简介").first
            if await hint.count() > 0:
                await hint.click(timeout=2000)
                await page.wait_for_timeout(300)
                await page.keyboard.type(desc_body[:900], delay=15)
                desc_filled = True
        except Exception:
            pass

    # Append topics at the END of 作品简介 (type #tag + pick suggestion / Space)
    topics_ok = await _append_topics_at_end(page, tags, desc_ed=desc_ed)
    if not topics_ok:
        topics_ok = await _add_hashtag_topics(page, tags)

    if not title_filled and not desc_filled:
        await _save_debug_shot(page, "title_fail")
        logger.warning("未能自动填写标题/简介")

    return {"title": title_filled, "desc": desc_filled, "topics": topics_ok}


async def _append_topics_at_end(
    page: Page,
    tags: list[str],
    *,
    desc_ed=None,
) -> bool:
    """Type each #tag at the end of 作品简介 so both appear fully."""
    try:
        if desc_ed is not None:
            await desc_ed.click(timeout=2000)
        else:
            ed = page.locator(
                'div[contenteditable="true"][data-placeholder*="简介"],'
                'div[contenteditable="true"][data-placeholder*="描述"]'
            ).first
            if await ed.count() == 0:
                return False
            await ed.click(timeout=2000)
        # Move to end
        await page.keyboard.press("Control+End")
        await page.wait_for_timeout(200)
        await page.keyboard.type("\n", delay=20)
        for tag in tags:
            plain = tag.lstrip("#")
            if await _page_has_topics(page, [tag]):
                continue
            await page.keyboard.type("#" + plain, delay=40)
            await page.wait_for_timeout(900)
            picked = False
            for sel in (
                f'[class*="suggest"] >> text=#{plain}',
                f'[class*="suggest"] >> text={plain}',
                f'[class*="mention"] >> text=#{plain}',
                f'[class*="topic"] >> text=#{plain}',
                f"li:has-text('#{plain}')",
                f"li:has-text('{plain}')",
            ):
                opt = page.locator(sel).first
                try:
                    if await opt.count() > 0 and await opt.is_visible():
                        await opt.click(timeout=2000)
                        picked = True
                        break
                except Exception:
                    continue
            if not picked:
                await page.keyboard.press("Space")
            await page.wait_for_timeout(400)
        return await _page_has_topics(page, tags)
    except Exception:
        logger.warning("简介末尾写入话题失败", exc_info=True)
        return False


async def _add_hashtag_topics(page: Page, tags: list[str]) -> bool:
    """Click #添加话题 and insert each tag as a proper topic chip."""
    if await _page_has_topics(page, tags):
        return True
    topic_btn = page.locator("text=#添加话题").first
    try:
        if await topic_btn.count() == 0:
            return False
        await topic_btn.scroll_into_view_if_needed()
    except Exception:
        return False

    for tag in tags:
        plain = tag.lstrip("#")
        if await _page_has_topics(page, [tag]):
            continue
        try:
            await topic_btn.click(timeout=2500)
            await page.wait_for_timeout(500)
            await page.keyboard.type(plain, delay=40)
            await page.wait_for_timeout(1000)
            picked = False
            for sel in (
                f'[class*="suggest"] >> text=#{plain}',
                f'[class*="suggest"] >> text={plain}',
                f'[class*="topic"] >> text=#{plain}',
                f'[class*="topic"] >> text={plain}',
                f"li:has-text('#{plain}')",
                f"li:has-text('{plain}')",
            ):
                opt = page.locator(sel).first
                try:
                    if await opt.count() > 0 and await opt.is_visible():
                        await opt.click(timeout=2000)
                        picked = True
                        break
                except Exception:
                    continue
            if not picked:
                await page.keyboard.press("Enter")
            await page.wait_for_timeout(600)
        except Exception:
            logger.warning("添加话题失败: %s", tag)
    return await _page_has_topics(page, tags)


async def _page_has_topics(page: Page, tags: list[str]) -> bool:
    """Prefer 作品简介 editor text; fall back to body."""
    texts: list[str] = []
    for sel in (
        'div[contenteditable="true"][data-placeholder*="简介"]',
        'div[contenteditable="true"][data-placeholder*="描述"]',
        '[data-placeholder*="添加作品简介"]',
        'div[contenteditable="true"]',
    ):
        loc = page.locator(sel)
        try:
            for i in range(min(await loc.count(), 4)):
                t = (await loc.nth(i).inner_text()).strip()
                if t:
                    texts.append(t)
        except Exception:
            continue
    blob = "\n".join(texts)
    if not blob:
        try:
            blob = await page.inner_text("body")
        except Exception:
            return False
    return all(t.lstrip("#") in blob for t in tags)


async def _confirm_cover_after_file(page: Page, progress: ProgressCb | None = None) -> bool:
    """After OS file pick, Douyin shows a crop dialog — must click 完成/保存."""

    def prog(msg: str) -> None:
        if progress:
            progress(msg)

    await page.wait_for_timeout(800)
    deadline = time.time() + 20
    clicked = False
    while time.time() < deadline:
        # Broad: any visible primary confirm in overlay (crop UI may not match modal chrome)
        for sel in (
            "button:has-text('完成')",
            "button:has-text('保存')",
            "button:has-text('确定')",
            "button:has-text('确认')",
            "text=完成",
            "text=保存",
        ):
            btn = page.locator(sel).first
            try:
                if await btn.count() == 0 or not await btn.is_visible():
                    continue
                disabled = await btn.get_attribute("disabled")
                aria = await btn.get_attribute("aria-disabled")
                if disabled is not None or aria in ("true", "True"):
                    continue
                # Avoid main-page 暂存 etc.
                txt = (await btn.inner_text()).strip()
                if txt in ("暂存离开", "发布"):
                    continue
                prog(f"封面裁剪确认: 点击「{txt or sel}」")
                await btn.click(timeout=4000)
                clicked = True
                await page.wait_for_timeout(1200)
                break
            except Exception:
                continue
        if clicked:
            # second confirm if nested
            if await _cover_modal_open(page) or await page.locator("button:has-text('完成')").count() > 0:
                try:
                    again = page.locator("button:has-text('完成'), button:has-text('保存')").first
                    if await again.count() > 0 and await again.is_visible():
                        await again.click(timeout=3000)
                        await page.wait_for_timeout(800)
                except Exception:
                    pass
            return True
        await page.wait_for_timeout(400)
    await _save_debug_shot(page, "cover_crop_no_confirm")
    return False


async def _collect_form_facts(
    page: Page,
    *,
    expect_v: bool,
    expect_h: bool,
    target_title: str = "",
) -> dict[str, Any]:
    title_text = await _read_title_text(page)
    topics = settings.publish_hashtag_list or ["#ai编程", "#干货"]
    topics_ok = await _page_has_topics(page, topics)
    covers = await collect_cover_state(page)
    return {
        "loading": await _page_still_loading(page),
        "cover_modal_open": await _cover_modal_open(page),
        "title_text": title_text[:80],
        "target_title": (target_title or "")[:80],
        "title_ok": bool(title_text.strip()),
        "expect_covers": expect_v or expect_h,
        "cover_v_ok": covers["v"]["ok"] if expect_v else True,
        "cover_h_ok": covers["h"]["ok"] if expect_h else True,
        "cover_previews": covers,
        "missing_cover_tips": covers["missing"],
        "topics_ok": topics_ok,
        "url": (page.url or "")[-120:],
    }


async def _verify_covers(
    page: Page,
    *,
    expect_v: bool,
    expect_h: bool,
    progress: ProgressCb | None = None,
    timeout_ms: int | None = None,
    poll_ms: int = 1000,
) -> dict[str, Any]:
    """Require two stable preview observations; text-only models cannot veto images."""
    timeout = settings.cover_verify_timeout_ms if timeout_ms is None else timeout_ms
    deadline = time.monotonic() + max(0, timeout) / 1000
    attempts: list[dict[str, Any]] = []
    previous = None
    stable = 0
    ok = False
    last_report = 0.0
    while True:
        facts = await _collect_form_facts(page, expect_v=expect_v, expect_h=expect_h)
        ready = (
            not facts["loading"]
            and not facts["cover_modal_open"]
            and facts["cover_v_ok"]
            and facts["cover_h_ok"]
        )
        signature = [
            facts["cover_previews"][kind].get("preview")
            for kind, expected in (("v", expect_v), ("h", expect_h)) if expected
        ]
        stable = stable + 1 if ready and signature == previous else (1 if ready else 0)
        previous = signature if ready else None
        attempts.append({"at": int(time.time() * 1000), "stable": stable, "facts": facts})
        if stable >= 2:
            ok = True
            break
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        if progress and time.monotonic() - last_report >= 5:
            progress(
                f"等待封面预览稳定：竖={'已显示' if facts['cover_v_ok'] else '待确认'} "
                f"横={'已显示' if facts['cover_h_ok'] else '待确认'}"
            )
            last_report = time.monotonic()
        await page.wait_for_timeout(min(max(1, poll_ms), remaining * 1000))

    absent = [name for key, name in (("cover_v_ok", "竖封面"), ("cover_h_ok", "横封面")) if not facts[key]]
    reason = "封面预览已稳定" if ok else "封面预览确认超时：" + (
        "、".join(absent) or ("编辑弹窗未关闭" if facts["cover_modal_open"] else "页面或预览仍在更新")
    )
    diagnostic_path = None
    try:
        out = Path(settings.data_dir) / "debug"
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"cover_check_{time.time_ns()}.json"
        path.write_text(json.dumps({"ok": ok, "reason": reason, "attempts": attempts}, ensure_ascii=False, indent=2), encoding="utf-8")
        diagnostic_path = str(path.resolve())
    except Exception as e:
        logger.warning("save cover diagnostic failed: %s", e)
    logger.info("cover verification ok=%s attempts=%s diagnostic=%s", ok, len(attempts), diagnostic_path)
    return {
        "ok": ok,
        "reason": reason,
        "facts": facts,
        "diagnosticPath": diagnostic_path,
        "attemptCount": len(attempts),
    }


async def _set_covers(
    page: Page,
    *,
    cover_v: Path | None,
    cover_h: Path | None,
    progress: ProgressCb | None = None,
) -> bool:
    """Upload 竖+横 covers; confirm with 保存/完成; retry if 横封面缺失."""
    await _dismiss_guides(page)
    await page.evaluate("window.scrollTo(0, 450)")
    await page.wait_for_timeout(500)

    def prog(msg: str) -> None:
        if progress:
            progress(msg)

    # One editor, two file picks. Do not click「完成」until both files are in.
    steps: list[tuple[str, Path]] = []
    if cover_h:
        steps.append(("横", cover_h))
    if cover_v and (not cover_h or cover_v.resolve() != cover_h.resolve()):
        steps.append(("竖", cover_v))
    elif cover_v and not cover_h:
        steps.append(("竖", cover_v))

    if not steps:
        return True

    if not await _cover_modal_open(page):
        first_kind, _ = steps[0]
        slot = ("横封面4:3", "横封面", "4:3") if first_kind == "横" else ("竖封面3:4", "竖封面", "3:4")
        prog(f"打开封面编辑器，准备分别上传 {'、'.join(k for k, _ in steps)}")
        if not await _open_cover_slot(page, slot, kind=first_kind, progress=progress):
            prog("未打开封面编辑器")
            await _save_debug_shot(page, "cover_no_modal")
            return False

    ok_all = True
    for i, (kind, path) in enumerate(steps):
        prog(f"第{i + 1}张：单独上传{kind}封面 {path.name}")
        if not await _switch_cover_tab(page, kind):
            prog(f"未能切到{kind}封面")
            ok_all = False
            break
        if not await _modal_pick_cover_file(page, path):
            prog(f"{kind}封面：未点到「上传封面」")
            await _save_debug_shot(page, f"cover_nofile_{kind}")
            ok_all = False
            break
        # Image applied when「完成」or the other-ratio button lights up. Do not click 完成 yet.
        if not await _wait_cover_action_ready(page, timeout_ms=40_000):
            prog(f"{kind}封面选图后编辑器无响应")
            await _save_debug_shot(page, f"cover_wait_{kind}")
            ok_all = False
            break
        prog(f"{kind}封面已选入编辑器")

    if not ok_all:
        await _close_cover_modal_if_open(page)
        return False

    prog("横竖都已单独选图，点「完成」")
    if not await _wait_cover_save_enabled(page, timeout_ms=15_000):
        await _save_debug_shot(page, "cover_done_disabled")
        await _close_cover_modal_if_open(page)
        return False
    if not await _click_cover_save_or_done(page):
        await _save_debug_shot(page, "cover_done_click")
        return False
    for _ in range(16):
        if not await _cover_modal_open(page):
            break
        await page.wait_for_timeout(250)
    return True


async def _detect_missing_cover_kinds(page: Page) -> list[str]:
    """Parse 快速检测 tips like 横封面缺失 / 竖封面缺失."""
    missing: list[str] = []
    for kind, needles in (
        ("横", ("横封面缺失", "横封面未设置", "缺少横封面")),
        ("竖", ("竖封面缺失", "竖封面未设置", "缺少竖封面")),
    ):
        for n in needles:
            loc = page.locator(f"text={n}").first
            try:
                if await loc.count() > 0 and await loc.is_visible():
                    missing.append(kind)
                    break
            except Exception:
                continue
    return missing


async def _cover_modal_open(page: Page) -> bool:
    """True only for the cover *editor dialog*, not the form section or video 重新上传.

    Bug history: matching「设置封面」+ side-rail「重新上传」falsely claimed the modal
    was open, so cover upload skipped clicking「选择封面」and later blocked publish.
    """
    # Modal tab titles / preview labels — these do not appear on the main form.
    for sel in (
        "text=设置竖封面",
        "text=设置横封面",
        "text=竖封面预览",
        "text=横封面预览",
    ):
        loc = page.locator(sel)
        try:
            for i in range(await loc.count()):
                if await loc.nth(i).is_visible():
                    return True
        except Exception:
            continue

    # Dialog chrome: 重新上传 + 保存 together (exclude video side-rail 重新上传 alone).
    try:
        dialogs = page.locator(
            "[role='dialog'], [class*='modal'], [class*='Modal'], [class*='dialog']"
        )
        n = await dialogs.count()
        for i in range(min(n, 8)):
            d = dialogs.nth(i)
            if not await d.is_visible():
                continue
            has_reup = await d.locator("text=重新上传").count() > 0
            has_upload = await d.locator("text=上传封面").count() > 0
            has_save = await d.locator("button:has-text('保存'), button:has-text('完成')").count() > 0
            if (has_reup or has_upload) and has_save:
                return True
    except Exception:
        pass
    return False


async def _close_cover_modal_if_open(page: Page) -> None:
    if not await _cover_modal_open(page):
        return
    # Prefer save if image already shown; else cancel
    if await _click_cover_save_or_done(page):
        return
    for sel in (
        "button:has-text('取消')",
        "[aria-label='Close']",
        "[class*='close']",
        "text=取消",
    ):
        btn = page.locator(sel).first
        try:
            if await btn.count() > 0 and await btn.is_visible():
                await btn.click(timeout=2000)
                await page.wait_for_timeout(400)
                if not await _cover_modal_open(page):
                    return
        except Exception:
            continue
    try:
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(400)
    except Exception:
        pass


async def _switch_cover_tab(page: Page, kind: str) -> bool:
    """Switch the open editor to 设置横封面 or 设置竖封面. Does not upload or confirm."""
    title = "设置竖封面" if kind == "竖" else "设置横封面"
    preview = "竖封面预览" if kind == "竖" else "横封面预览"
    loc = page.locator(f"text={title}")
    try:
        n = await loc.count()
    except Exception:
        n = 0
    for i in range(n):
        el = loc.nth(i)
        try:
            if not await el.is_visible():
                continue
            await el.click(timeout=3000)
            await page.wait_for_timeout(500)
            # Confirm the matching preview label is showing
            prev = page.locator(f"text={preview}").first
            if await prev.count() == 0 or await prev.is_visible():
                return True
        except Exception:
            continue
    return n > 0


async def _wait_cover_action_ready(page: Page, timeout_ms: int = 40_000) -> bool:
    """True once 完成 or the other-ratio button is enabled (image accepted, spinner done)."""
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        if await _cover_confirm_button(page) is not None:
            return True
        for label in ("设置竖封面", "设置横封面"):
            btn = page.locator(f"button:has-text('{label}')").first
            try:
                if await btn.count() == 0 or not await btn.is_visible():
                    continue
                if await btn.is_enabled():
                    cls = ((await btn.get_attribute("class")) or "").lower()
                    if "disabled" not in cls:
                        return True
            except Exception:
                continue
        await page.wait_for_timeout(400)
    return False


async def _upload_one_cover_via_modal(
    page: Page,
    *,
    kind: str,
    image: Path,
    progress: ProgressCb | None = None,
) -> bool:
    """kind = 竖|横.

    Douyin editor (截图): tabs 设置横封面/设置竖封面, center may spin while
    frames load, black「上传封面」is the real action,「完成」stays gray until
    a local image is applied. Do not wait on the spinner or click gray 完成.
    """

    def prog(msg: str) -> None:
        if progress:
            progress(msg)

    tab_title = "设置竖封面" if kind == "竖" else "设置横封面"
    slot_texts = (
        ("竖封面3:4", "竖封面", "3:4")
        if kind == "竖"
        else ("横封面4:3", "横封面", "4:3")
    )

    await page.evaluate("window.scrollTo(0, 400)")
    await page.wait_for_timeout(300)
    try:
        sec = page.locator("text=设置封面").first
        if await sec.count() > 0:
            await sec.scroll_into_view_if_needed()
    except Exception:
        pass

    if not await _cover_modal_open(page):
        prog(f"打开{kind}封面编辑器…")
        opened = await _open_cover_slot(page, slot_texts, kind=kind, progress=progress)
        if not opened:
            prog(f"未打开{kind}封面弹窗")
            await _save_debug_shot(page, f"cover_no_modal_{kind}")
            return False

    try:
        tab = page.get_by_text(tab_title, exact=True).first
        if await tab.count() > 0 and await tab.is_visible():
            await tab.click(timeout=3000)
            await page.wait_for_timeout(400)
    except Exception:
        pass

    prog(f"{kind}封面：点「上传封面」选择 {image.name}")
    uploaded = await _modal_pick_cover_file(page, image)
    if not uploaded:
        prog(f"{kind}封面：未能点到「上传封面」")
        await _save_debug_shot(page, f"cover_nofile_{kind}")
        return False

    prog(f"{kind}封面：等「完成」变亮…")
    if not await _wait_cover_save_enabled(page, timeout_ms=40_000):
        prog(f"{kind}封面：「完成」一直是灰色")
        await _save_debug_shot(page, f"cover_wait_{kind}")
        return False
    if not await _click_cover_save_or_done(page):
        prog(f"{kind}封面：点击「完成」失败")
        await _save_debug_shot(page, f"cover_done_click_{kind}")
        return False

    for _ in range(12):
        # After 完成 the editor may close, or stay open for the other ratio.
        if not await _cover_modal_open(page):
            break
        await page.wait_for_timeout(250)
    prog(f"{kind}封面已点完成")
    return True


async def _pick_cover_via_slot_chooser(
    page: Page,
    slot_texts: tuple[str, ...],
    image: Path,
    *,
    kind: str,
    progress: ProgressCb | None = None,
) -> bool:
    """Click「选择封面」inside 横/竖 card and set the local image via file chooser."""

    def prog(msg: str) -> None:
        if progress:
            progress(msg)

    for label in slot_texts:
        loc = page.locator(f"text={label}").first
        try:
            if await loc.count() == 0 or not await loc.is_visible():
                continue
            await loc.scroll_into_view_if_needed()
            await page.wait_for_timeout(200)
            # Prefer a nearby container that also contains 选择封面
            card = loc.locator(
                "xpath=ancestor::*[.//text()[contains(.,'选择封面') or contains(.,'上传封面') or contains(.,'修改封面')]][1]"
            )
            targets = []
            if await card.count() > 0:
                for sub in ("选择封面", "上传封面", "修改封面", "更换封面"):
                    b = card.locator(f"text={sub}").first
                    if await b.count() > 0:
                        targets.append(b)
            # Also try nth「选择封面」by kind (横=left/0, 竖=right/1)
            choose_all = page.locator("text=选择封面")
            n = await choose_all.count()
            if n > 0:
                idx = 0 if kind == "横" else min(1, n - 1)
                targets.append(choose_all.nth(idx))
                if n > 1 and kind == "竖":
                    targets.append(choose_all.nth(n - 1))

            for btn in targets:
                try:
                    if not await btn.is_visible():
                        continue
                    before = await _count_image_inputs(page)
                    try:
                        async with page.expect_file_chooser(timeout=5000) as fc_info:
                            await btn.click(timeout=3000)
                        chooser = await fc_info.value
                        await chooser.set_files(str(image))
                        prog(f"{kind}封面：已通过「选择封面」选文件")
                        await page.wait_for_timeout(2000)
                        return True
                    except Exception:
                        await btn.click(timeout=3000)
                        await page.wait_for_timeout(600)
                        if await _set_image_file_input(page, image, prefer_after=before):
                            prog(f"{kind}封面：已写入隐藏 file input")
                            await page.wait_for_timeout(1500)
                            return True
                except Exception:
                    continue
        except Exception:
            continue
    return False


async def _open_cover_slot(
    page: Page,
    slot_texts: tuple[str, ...],
    *,
    kind: str,
    progress: ProgressCb | None = None,
) -> bool:
    """Click 竖封面3:4 / 横封面4:3 card (label, img, or 选择封面) until modal opens."""

    def prog(msg: str) -> None:
        if progress:
            progress(msg)

    # Click 快速检测 tip to jump into the missing cover editor
    tip = "横封面缺失" if kind == "横" else "竖封面缺失"
    try:
        tip_loc = page.locator(f"text={tip}").first
        if await tip_loc.count() > 0 and await tip_loc.is_visible():
            await tip_loc.click(timeout=2500)
            if await _wait_cover_modal(page, 3500):
                return True
    except Exception:
        pass

    for label in slot_texts:
        loc = page.locator(f"text={label}").first
        try:
            if await loc.count() == 0:
                continue
            await loc.scroll_into_view_if_needed()
            await page.wait_for_timeout(200)

            # 1) click label itself
            await loc.click(timeout=3000)
            if await _wait_cover_modal(page, 2500):
                return True

            # 2) click nearby img / canvas (thumbnail)
            parent = loc.locator("xpath=ancestor::div[position()<=8][1]")
            for img_sel in ("img", "canvas", "[class*='cover']", "[class*='thumb']"):
                try:
                    img = parent.locator(img_sel).first
                    if await img.count() == 0:
                        continue
                    await img.click(timeout=2500)
                    if await _wait_cover_modal(page, 3000):
                        return True
                except Exception:
                    continue

            # 3) click 选择封面 / 上传封面 / 修改封面 inside card
            for sub in ("选择封面", "上传封面", "修改封面", "设置封面", "更换封面"):
                try:
                    b = parent.locator(f"text={sub}").first
                    if await b.count() == 0:
                        continue
                    await b.click(timeout=2500)
                    if await _wait_cover_modal(page, 3000):
                        return True
                except Exception:
                    continue
        except Exception:
            continue

    # Global fallbacks
    for sub in ("选择封面", "上传封面", "设置封面"):
        try:
            btns = page.locator(f"text={sub}")
            n = await btns.count()
            # 竖 usually right; 横 usually left — try index by kind
            order = range(n) if kind == "横" else range(n - 1, -1, -1)
            for i in order:
                b = btns.nth(i)
                if not await b.is_visible():
                    continue
                await b.click(timeout=2500)
                if await _wait_cover_modal(page, 3000):
                    return True
        except Exception:
            continue
    prog(f"{kind}封面：点击入口均未弹出编辑器")
    return False


async def _wait_cover_modal(page: Page, timeout_ms: int = 3000) -> bool:
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        if await _cover_modal_open(page):
            return True
        await page.wait_for_timeout(250)
    return False


async def _direct_cover_file_near_slot(
    page: Page,
    slot_texts: tuple[str, ...],
    image: Path,
) -> bool:
    """When modal won't open: file-chooser on 选择/上传封面 near the slot label."""
    for label in slot_texts:
        loc = page.locator(f"text={label}").first
        try:
            if await loc.count() == 0:
                continue
            parent = loc.locator("xpath=ancestor::div[position()<=10][1]")
            for sub in ("选择封面", "上传封面", "修改封面", "更换封面"):
                btn = parent.locator(f"text={sub}").first
                if await btn.count() == 0:
                    continue
                try:
                    async with page.expect_file_chooser(timeout=4000) as fc_info:
                        await btn.click(timeout=3000)
                    chooser = await fc_info.value
                    await chooser.set_files(str(image))
                    await page.wait_for_timeout(2000)
                    return True
                except Exception:
                    before = await _count_image_inputs(page)
                    try:
                        await btn.click(timeout=2000)
                    except Exception:
                        pass
                    await page.wait_for_timeout(500)
                    if await _set_image_file_input(page, image, prefer_after=before):
                        await page.wait_for_timeout(1500)
                        return True
        except Exception:
            continue
    # Last resort: any image file input
    return await _set_image_file_input(page, image)


async def _confirm_cover_if_possible(page: Page) -> None:
    if await _wait_cover_save_enabled(page, timeout_ms=8_000):
        await _click_cover_save_or_done(page)


async def _modal_pick_cover_file(page: Page, image: Path) -> bool:
    """Inside cover modal: 上传封面 / 重新上传 + file chooser.

    Prefer dialog-scoped locators so we never click the video side-rail「重新上传」.
    """
    roots: list[Any] = []
    try:
        dialogs = page.locator(
            "[role='dialog'], [class*='modal'], [class*='Modal'], [class*='dialog']"
        )
        n = await dialogs.count()
        for i in range(min(n, 6)):
            d = dialogs.nth(i)
            if await d.is_visible():
                roots.append(d)
    except Exception:
        pass
    roots.append(page)

    upload_sels = (
        "button:has-text('上传封面')",
        "text=上传封面",
        "[class*='upload']:has-text('上传封面')",
        "div:has-text('上传封面')",
    )
    # Prefer the black button inside the open editor (not the page behind it).
    candidates = []
    for root in roots:
        for sel in upload_sels:
            loc = root.locator(sel)
            try:
                n = await loc.count()
            except Exception:
                continue
            for i in range(min(n, 6)):
                candidates.append(loc.nth(i))

    for btn in candidates:
        try:
            if not await btn.is_visible():
                continue
            txt = ""
            try:
                txt = (await btn.inner_text()).strip().replace("\n", "")
            except Exception:
                txt = ""
            if "上传封面" not in txt and "重新上传" not in txt:
                continue
            # Skip huge containers that merely contain the label
            box = await btn.bounding_box()
            if box and (box.get("width", 0) > 420 or box.get("height", 0) > 120):
                continue
            before = await _count_image_inputs(page)
            try:
                async with page.expect_file_chooser(timeout=8000) as fc_info:
                    await btn.click(timeout=4000, force=True)
                chooser = await fc_info.value
                await chooser.set_files(str(image))
                await page.wait_for_timeout(1200)
                return True
            except Exception:
                await page.wait_for_timeout(400)
                if await _set_image_file_input(page, image, prefer_after=before):
                    await page.wait_for_timeout(1200)
                    return True
        except Exception:
            continue

    if await _set_image_file_input(page, image):
        await page.wait_for_timeout(1500)
        return True
    return False


async def _cover_confirm_button(page: Page):
    """Modal primary action: 保存 (new UI) or 完成 (old UI)."""
    for sel in (
        "button:has-text('保存')",
        "button:has-text('完成')",
        "button:has-text('确定')",
        "button:has-text('确认')",
    ):
        btn = page.locator(sel).first
        try:
            if await btn.count() == 0 or not await btn.is_visible():
                continue
            # Skip disabled
            disabled = await btn.get_attribute("disabled")
            aria = await btn.get_attribute("aria-disabled")
            cls = ((await btn.get_attribute("class")) or "").lower()
            gray = any(x in cls for x in ("disabled", "disable", "semi-button-disabled"))
            if disabled is not None or aria in ("true", "True") or gray:
                continue
            try:
                if not await btn.is_enabled():
                    continue
            except Exception:
                pass
            return btn
        except Exception:
            continue
    return None


async def _wait_cover_save_enabled(page: Page, timeout_ms: int = 60_000) -> bool:
    """Wait until modal 保存/完成 is visible and enabled."""
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        btn = await _cover_confirm_button(page)
        if btn is not None:
            return True
        await page.wait_for_timeout(500)
    return False


# Back-compat alias
async def _wait_cover_done_enabled(page: Page, timeout_ms: int = 60_000) -> bool:
    return await _wait_cover_save_enabled(page, timeout_ms=timeout_ms)


async def _click_cover_save_or_done(page: Page) -> bool:
    btn = await _cover_confirm_button(page)
    if btn is None:
        # Last try: pink primary in modal
        for sel in ("button:has-text('保存')", "button:has-text('完成')"):
            b = page.locator(sel).first
            try:
                if await b.count() > 0 and await b.is_visible():
                    await b.click(timeout=4000, force=True)
                    await page.wait_for_timeout(1000)
                    return True
            except Exception:
                continue
        return False
    try:
        await btn.click(timeout=5000)
        await page.wait_for_timeout(1200)
        return True
    except Exception:
        try:
            await btn.click(timeout=3000, force=True)
            await page.wait_for_timeout(1200)
            return True
        except Exception:
            return False


async def _count_image_inputs(page: Page) -> int:
    total = 0
    for frame in [page] + list(page.frames):
        try:
            total += await frame.locator('input[type="file"]').count()
        except Exception:
            continue
    return total


async def _set_image_file_input(
    page: Page,
    image: Path,
    *,
    prefer_after: int | None = None,
) -> bool:
    frames = [page] + list(page.frames)
    ranked: list[tuple[int, int, Any]] = []  # score, index, inp
    idx = 0
    for frame in frames:
        try:
            inputs = frame.locator('input[type="file"]')
            count = await inputs.count()
        except Exception:
            continue
        for i in range(count):
            inp = inputs.nth(i)
            try:
                accept = ((await inp.get_attribute("accept")) or "").lower()
            except Exception:
                accept = ""
            if "video" in accept and "image" not in accept and "png" not in accept and "jpg" not in accept:
                idx += 1
                continue
            score = 0
            if "image" in accept or "png" in accept or "jpg" in accept or "jpeg" in accept:
                score = 2
            elif accept == "" or accept == "*/*":
                score = 1
            if prefer_after is not None and idx >= prefer_after:
                score += 3
            ranked.append((score, idx, inp))
            idx += 1
    ranked.sort(key=lambda x: x[0], reverse=True)
    for score, _i, inp in ranked:
        if score <= 0:
            continue
        try:
            await inp.set_input_files(str(image))
            await page.wait_for_timeout(500)
            return True
        except Exception:
            continue
    return False


async def _set_location(page: Page, location: str) -> None:
    """Fill Douyin geo tag — fixed default 北京市朝阳区."""
    if not location:
        return
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(500)
    opened = False
    for sel in (
        'div.semi-select span:has-text("输入地理位置")',
        'span:has-text("输入地理位置")',
        "text=输入地理位置",
        "text=添加位置",
        "text=地理位置",
        "text=添加作品位置",
        'div.semi-select:has-text("位置")',
        '[placeholder*="位置"]',
        '[placeholder*="地理"]',
    ):
        loc = page.locator(sel).first
        try:
            if await loc.count() == 0:
                continue
            if not await loc.is_visible():
                await loc.scroll_into_view_if_needed()
            await loc.click(timeout=5000)
            opened = True
            break
        except Exception:
            continue
    if not opened:
        # Label "位置" then nearby select
        try:
            label = page.locator("text=位置").first
            if await label.count() > 0:
                box = label.locator("xpath=following::*[contains(@class,'semi-select') or self::input][1]")
                if await box.count() > 0:
                    await box.click(timeout=4000)
                    opened = True
        except Exception:
            pass
    if not opened:
        logger.warning("未找到地理位置入口")
        await _save_debug_shot(page, "location_fail")
        return

    await page.wait_for_timeout(800)
    try:
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Backspace")
    except Exception:
        pass
    await page.keyboard.type(location, delay=40)
    await page.wait_for_timeout(1500)

    for opt_sel in (
        'div[role="listbox"] [role="option"]',
        '[class*="option"]',
        f"text={location}",
        "text=朝阳区",
        "text=北京市朝阳区",
    ):
        opt = page.locator(opt_sel).first
        try:
            if await opt.count() > 0 and await opt.is_visible():
                await opt.click(timeout=3000)
                await page.wait_for_timeout(500)
                return
        except Exception:
            continue
    try:
        await page.keyboard.press("ArrowDown")
        await page.keyboard.press("Enter")
    except Exception:
        logger.warning("地理位置选项点击失败: %s", location)


# Only strong success copy; never treat "发布完成/上传成功" alone as published.
_SUCCESS_KW = (
    "发布成功",
    "作品发布成功",
    "投稿成功",
    "视频发布成功",
)
_VERIFY_KW = (
    "验证码",
    "短信验证",
    "扫码验证",
    "安全验证",
    "滑动验证",
    "请完成验证",
    "身份验证",
)
_BLOCKER_KW = (
    "请设置封面",
    "请添加封面",
    "请上传封面",
    "横封面缺失",
    "竖封面缺失",
    "请填写作品标题",
    "请输入标题",
    "标题不能为空",
    "视频还未上传完成",
    "视频上传中",
    "转码中",
    "请完成声明",
    "请勾选",
)


async def _visible_any(page: Page, keywords: tuple[str, ...], *, exact: bool = False) -> str | None:
    for kw in keywords:
        loc = page.get_by_text(kw, exact=exact)
        try:
            for i in range(min(await loc.count(), 10)):
                if await loc.nth(i).is_visible():
                    return kw
        except Exception:
            continue
    return None


async def _save_debug_shot(page: Page, tag: str) -> str | None:
    try:
        out = Path(settings.data_dir) / "debug"
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{tag}_{int(time.time())}.png"
        await page.screenshot(path=str(path), full_page=True)
        return str(path)
    except Exception:
        return None


async def _find_publish_button(page: Page):
    # Prefer exact primary button; avoid sidebar "发布"/定时发布/高清发布.
    try:
        btn = page.get_by_role("button", name="发布", exact=True)
        if await btn.count() > 0:
            for i in range(await btn.count()):
                b = btn.nth(i)
                if await b.is_visible() and await b.is_enabled():
                    return b
    except Exception:
        pass
    for sel in (
        "button:has-text('发布')",
        "[class*='publish'] button",
        "[class*='submit'] button",
    ):
        loc = page.locator(sel)
        try:
            n = await loc.count()
        except Exception:
            continue
        for i in range(n):
            b = loc.nth(i)
            try:
                if not await b.is_visible() or not await b.is_enabled():
                    continue
                text = (await b.inner_text()).strip().replace("\n", "")
                if text != "发布" and not text.endswith("发布"):
                    continue
                if any(x in text for x in ("定时", "高清", "草稿")):
                    continue
                if len(text) <= 6:
                    return b
            except Exception:
                continue
    return None


def _is_editor_url(url: str) -> bool:
    u = url or ""
    return any(x in u for x in ("/content/upload", "/content/post", "/content/publish"))


def _is_manage_url(url: str) -> bool:
    u = url or ""
    return "/content/manage" in u


async def _prepare_before_publish(page: Page) -> None:
    """Tick common Douyin pre-publish checkboxes (AI declaration etc.)."""
    # AI-generated content declaration — often required now.
    for sel in (
        "text=内容由AI生成",
        "text=AI生成",
        "label:has-text('AI')",
        "text=我已阅读并同意",
    ):
        loc = page.locator(sel).first
        try:
            if await loc.count() == 0 or not await loc.is_visible():
                continue
            await loc.click(timeout=2000)
            await page.wait_for_timeout(400)
        except Exception:
            continue

    # Checkboxes near声明
    boxes = page.locator('input[type="checkbox"]')
    try:
        n = await boxes.count()
    except Exception:
        n = 0
    for i in range(min(n, 8)):
        box = boxes.nth(i)
        try:
            if await box.is_checked():
                continue
            # only click if nearby text suggests declaration
            parent_text = ""
            try:
                parent_text = await box.evaluate(
                    "el => (el.closest('label,div,span')||el.parentElement||el).innerText||''"
                )
            except Exception:
                parent_text = ""
            if any(k in parent_text for k in ("AI", "声明", "同意", "原创", "规范")):
                await box.check(force=True, timeout=2000)
                await page.wait_for_timeout(200)
        except Exception:
            continue


async def _click_publish_and_confirm(
    page: Page,
    progress: ProgressCb | None = None,
    wait_sec: float = 90,
    *,
    expected_title: str = "",
    on_submit: Callable[[], None] | None = None,
) -> dict[str, Any]:
    """Submit once, then confirm via response, success notice, or the matching work."""

    def prog(msg: str) -> None:
        if progress:
            progress(msg)

    captured: dict[str, Any] | None = None
    pending: set[asyncio.Task] = set()

    async def read_response(response) -> None:
        nonlocal captured
        try:
            payload = await asyncio.wait_for(response.json(), timeout=3)
            evidence = submission_evidence(payload)
            if evidence is not None and (captured is None or evidence["ok"]):
                captured = evidence
        except Exception:
            pass

    def track_response(response) -> None:
        if is_publish_request(response.url, response.request.method):
            task = asyncio.create_task(read_response(response))
            pending.add(task)
            task.add_done_callback(pending.discard)

    def success(evidence: dict) -> dict[str, Any]:
        return {"ok": True, "message": "发布已提交并确认", "evidence": evidence, "url": page.url}

    def uncertain(message: str) -> dict[str, Any]:
        return {"ok": False, "unconfirmed": True, "message": message + "；请先核对作品管理，勿重复发布", "url": page.url}

    page.on("response", track_response)
    try:
        btn = await _find_publish_button(page)
        if btn is None:
            return {"ok": False, "message": "未找到可点的「发布」按钮", "url": page.url}
        try:
            await btn.scroll_into_view_if_needed(timeout=3000)
        except Exception:
            pass
        if on_submit:
            on_submit()
        try:
            await btn.click(timeout=5000, no_wait_after=True)
        except Exception:
            if captured and captured.get("ok"):
                return success(captured)
            return uncertain("已尝试点击发布，页面响应未确认")

        prog("已点击发布，正在确认结果…")
        deadline = time.monotonic() + max(0, wait_sec)
        last_report = 0.0
        confirmed_dialog = False
        while True:
            if captured:
                if captured.get("ok"):
                    return success(captured)
                return {"ok": False, "message": captured.get("message") or "抖音拒绝发布", "evidence": captured, "url": page.url}
            if page.is_closed():
                return uncertain("提交后浏览器已关闭，结果待核对")
            hit = await _visible_any(page, _SUCCESS_KW, exact=True)
            if hit:
                return success({"source": "success_notice", "notice": hit})
            if _is_manage_url(page.url):
                evidence = await find_work(page, expected_title, timeout_sec=0)
                if evidence:
                    return success(evidence)

            # A successful submit may reset the uploader instead of navigating to
            # management. Read the matching work; an empty form alone is no proof.
            if "/content/upload" in page.url and await _title_editor(page) is None:
                upload = await _visible_any(page, ("上传视频", "点击上传"), exact=True)
                if upload:
                    prog("已回到上传页，正在前往作品管理核对本条视频…")
                    try:
                        evidence = await check_management(page, expected_title)
                    except Exception:
                        evidence = None
                    if captured and captured.get("ok"):
                        return success(captured)
                    if evidence:
                        return success(evidence)
                    return uncertain("提交后已回到上传页，暂未在作品管理确认本条视频")

            # Confirm an explicit secondary dialog once; never press the main
            # publish button again while its outcome is unknown.
            if not confirmed_dialog:
                confirms = page.get_by_role("button", name="确认发布", exact=True)
                for i in range(await confirms.count()):
                    if await confirms.nth(i).is_visible():
                        confirmed_dialog = True
                        await confirms.nth(i).click(timeout=3000, no_wait_after=True)
                        break
            blocker = await _visible_any(page, _BLOCKER_KW)
            if blocker and any(word in blocker for word in ("封面", "标题")):
                return {"ok": False, "message": f"发布受阻：{blocker}（未重复点击）", "url": page.url}
            if await _cover_modal_open(page):
                return {"ok": False, "message": "封面设置弹窗仍打开，未重复点击发布", "url": page.url}
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                await _save_debug_shot(page, "publish_unconfirmed")
                return uncertain("发布确认等待超时，结果待核对")
            if time.monotonic() - last_report >= 5:
                verification = await _visible_any(page, _VERIFY_KW)
                prog(f"{'请在浏览器完成验证；' if verification else ''}正在确认发布结果，剩余约 {int(remaining)} 秒")
                last_report = time.monotonic()
            await page.wait_for_timeout(min(1000, remaining * 1000))
    finally:
        page.remove_listener("response", track_response)
        for task in list(pending):
            task.cancel()
        if pending:
            await asyncio.gather(*list(pending), return_exceptions=True)
