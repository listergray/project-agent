from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Callable

from playwright.async_api import Page, async_playwright

from app.config import settings

logger = logging.getLogger("douyin-auto.publisher")

UPLOAD_URL = "https://creator.douyin.com/creator-micro/content/upload"
HOME_URL = "https://creator.douyin.com/"

ProgressCb = Callable[[str], None]

# One Chromium profile cannot be opened twice; serialize all browser ops.
_browser_lock = threading.Lock()
_lock_holder = ""
_lock_meta = threading.Lock()
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
    with _lock_meta:
        holder = _lock_holder
    return {"busy": bool(holder), "holder": holder or None}


def _try_acquire(holder: str, *, wait_sec: float = 0) -> bool:
    global _lock_holder
    if wait_sec <= 0:
        ok = _browser_lock.acquire(blocking=False)
    else:
        ok = _browser_lock.acquire(blocking=True, timeout=wait_sec)
    if ok:
        with _lock_meta:
            _lock_holder = holder
    return ok


def _release() -> None:
    global _lock_holder
    with _lock_meta:
        _lock_holder = ""
    try:
        _browser_lock.release()
    except RuntimeError:
        pass


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


async def check_login(force: bool = False, soft: bool = False) -> dict[str, Any]:
    """Probe login.

    - soft/default after restart: prefer disk/memory cache so UI won't flash 未登录
    - force=True: always open Playwright and update disk
    """
    now = time.time()
    if not force:
        hit = _cached_login(now, allow_disk=True)
        if hit is not None:
            # soft: never launch browser; hard refresh still uses short memory TTL above
            if soft or hit.get("ok") or hit.get("fromDisk"):
                return hit
        if soft:
            # No usable cache — report unknown without wiping disk
            return {"ok": False, "message": "尚未检测（点刷新状态或扫码登录）", "cached": True}

    # Never block long for status; login/publish have priority.
    if not await asyncio.to_thread(_try_acquire, "status", wait_sec=0):
        hit = _cached_login(now, allow_disk=True)
        if hit is not None:
            hit["cached"] = True
            return hit
        info = browser_busy()
        return {
            "ok": False,
            "message": f"检测跳过（忙碌: {info.get('holder') or 'busy'}）",
            "cached": True,
        }

    try:
        settings.ensure_dirs()
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=_profile_dir(),
                headless=True,
                viewport={"width": 1400, "height": 900},
                locale="zh-CN",
                args=["--disable-blink-features=AutomationControlled"],
            )
            page = context.pages[0] if context.pages else await context.new_page()
            try:
                await page.goto(HOME_URL, wait_until="domcontentloaded", timeout=60_000)
                await page.wait_for_timeout(1500)
                logged_in = await _is_logged_in(page)
                return _remember_login(
                    {"ok": logged_in, "message": "已登录" if logged_in else "未登录"},
                    persist=True,
                )
            finally:
                await context.close()
    except Exception as e:
        logger.exception("check_login failed")
        # Do not overwrite a recent successful disk cache on transient probe errors.
        hit = _cached_login(now, allow_disk=True)
        if hit and hit.get("ok"):
            hit["cached"] = True
            hit["message"] = f"{hit.get('message')}（本次检测失败已忽略）"
            return hit
        return {"ok": False, "message": f"检测失败: {e}"}
    finally:
        _release()


async def publish_video(
    video_path: str,
    title: str | None = None,
    cover_path: str | None = None,
    cover_path_v: str | None = None,
    cover_path_h: str | None = None,
    description: str | None = None,
    location: str | None = None,
    on_progress: ProgressCb | None = None,
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

    if not await asyncio.to_thread(_try_acquire, "publish", wait_sec=5.0):
        info = browser_busy()
        return {
            "ok": False,
            "message": f"浏览器忙碌中（{info.get('holder') or 'busy'}），请稍后再试",
        }

    settings.ensure_dirs()
    # Always show browser for publish so user can finish captcha / see blockers.
    use_headless = False
    try:
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
                if cover_v or cover_h:
                    progress("分别上传横/竖封面(跳过AI)...")
                    ok_cover = await _set_covers(page, cover_v=cover_v, cover_h=cover_h, progress=progress)
                    await _dismiss_guides(page)
                    await _close_cover_modal_if_open(page)
                    # DOM + DeepSeek text judge (deepseek-chat 无视觉，看页面事实)
                    cover_check = await _verify_covers_with_llm(
                        page,
                        expect_v=bool(cover_v),
                        expect_h=bool(cover_h),
                        progress=progress,
                    )
                    if cover_check.get("ok") is False:
                        ok_cover = False
                        progress(f"封面质检未通过: {cover_check.get('reason')}")
                    elif cover_check.get("ok") is True:
                        ok_cover = True
                        progress("封面质检通过（DeepSeek）")

                if location:
                    progress(f"设置定位: {location}")
                    await _set_location(page, location)

                # Gate: never click 发布 until title + cover + topics OK
                missing: list[str] = []
                title_now = await _read_title_text(page)
                if not ok_meta.get("title") or not (title_now or "").strip():
                    missing.append("标题为空")
                if (cover_v or cover_h) and not ok_cover:
                    missing.append("封面未上传成功")
                if not ok_meta.get("topics"):
                    missing.append("话题未写入作品简介")
                if await _cover_modal_open(page):
                    missing.append("封面设置弹窗仍打开")
                if missing:
                    await _save_debug_shot(page, "prepublish_blocked")
                    msg = "；".join(missing) + " — 未点击发布，请检查后重试"
                    progress(msg)
                    return {
                        "ok": False,
                        "message": msg,
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
                publish_result = await _click_publish_and_confirm(page, progress)
                if not publish_result.get("ok"):
                    await _save_debug_shot(page, "publish_unconfirmed")
                    return {
                        "ok": False,
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
                return {"ok": False, "message": str(e)}
            finally:
                await context.close()
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


async def _wait_upload_ready(page: Page, progress: ProgressCb | None = None) -> None:
    """Wait until publish form is fully loaded (title field visible, not 加载中)."""
    hard_cap = min(float(settings.upload_timeout_ms) / 1000.0, 180.0)
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
            uploading = page.locator("text=上传中").first
            try:
                if await uploading.count() > 0 and await uploading.is_visible():
                    if progress and time.time() - last_log > 5:
                        progress("视频仍在上传中...")
                        last_log = time.time()
                    await page.wait_for_timeout(1500)
                    continue
            except Exception:
                pass
            # Stabilize: require title editor still present after short wait
            await page.wait_for_timeout(1200)
            if await _form_ready(page):
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


async def _cover_slot_has_image(page: Page, labels: tuple[str, ...]) -> bool:
    """Heuristic: cover card near label contains a non-tiny img/canvas."""
    for label in labels:
        loc = page.locator(f"text={label}").first
        try:
            if await loc.count() == 0:
                continue
            parent = loc.locator("xpath=ancestor::div[position()<=8][1]")
            imgs = parent.locator("img")
            for i in range(min(await imgs.count(), 4)):
                img = imgs.nth(i)
                try:
                    box = await img.bounding_box()
                    src = (await img.get_attribute("src")) or ""
                    if box and box.get("width", 0) >= 40 and box.get("height", 0) >= 40:
                        if src and not src.startswith("data:image/svg"):
                            return True
                except Exception:
                    continue
            canv = parent.locator("canvas")
            if await canv.count() > 0:
                return True
        except Exception:
            continue
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
    cover_v_ok = await _cover_slot_has_image(page, ("竖封面3:4", "竖封面", "3:4"))
    cover_h_ok = await _cover_slot_has_image(page, ("横封面4:3", "横封面", "4:3"))
    missing_tips = await _detect_missing_cover_kinds(page)
    if "竖" in missing_tips:
        cover_v_ok = False
    if "横" in missing_tips:
        cover_h_ok = False
    return {
        "loading": await _page_still_loading(page),
        "cover_modal_open": await _cover_modal_open(page),
        "title_text": title_text[:80],
        "target_title": (target_title or "")[:80],
        "title_ok": bool(title_text.strip()),
        "expect_covers": expect_v or expect_h,
        "cover_v_ok": cover_v_ok if expect_v else True,
        "cover_h_ok": cover_h_ok if expect_h else True,
        "missing_cover_tips": missing_tips,
        "topics_ok": topics_ok,
        "url": (page.url or "")[-120:],
    }


async def _verify_covers_with_llm(
    page: Page,
    *,
    expect_v: bool,
    expect_h: bool,
    progress: ProgressCb | None = None,
) -> dict[str, Any]:
    """DOM heuristics + DeepSeek text judge (no vision)."""
    facts = await _collect_form_facts(page, expect_v=expect_v, expect_h=expect_h)
    dom_ok = (
        not facts["loading"]
        and not facts["cover_modal_open"]
        and facts["cover_v_ok"]
        and facts["cover_h_ok"]
    )
    if progress:
        progress(
            f"封面DOM检测 竖={'OK' if facts['cover_v_ok'] else '缺'} "
            f"横={'OK' if facts['cover_h_ok'] else '缺'}"
        )

    from app.llm_judge import judge_publish_form

    try:
        judged = await asyncio.to_thread(judge_publish_form, facts)
    except Exception as e:
        logger.warning("llm cover judge error: %s", e)
        judged = {"ok": None, "skipped": True, "reason": str(e)}

    if judged.get("skipped"):
        # Fall back to DOM only
        return {
            "ok": dom_ok if (expect_v or expect_h) else True,
            "reason": judged.get("reason") or ("DOM通过" if dom_ok else "DOM未检测到封面图"),
            "facts": facts,
            "llm": judged,
        }

    # Combine: LLM ready + cover_ok; if LLM says cover fail, trust it
    cover_ok = bool(judged.get("cover_ok", dom_ok))
    if not dom_ok:
        cover_ok = False
    return {
        "ok": cover_ok,
        "reason": judged.get("reason") or ("通过" if cover_ok else "未通过"),
        "facts": facts,
        "llm": judged,
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

    # If a leftover 设置封面 modal is open, save or close first
    if await _cover_modal_open(page):
        prog("发现未关闭的封面弹窗，先点「保存」...")
        if not await _click_cover_save_or_done(page):
            await _close_cover_modal_if_open(page)

    # Horizontal first — Douyin 快速检测常报「横封面缺失」
    required: list[tuple[str, Path]] = []
    if cover_h:
        required.append(("横", cover_h))
    if cover_v:
        required.append(("竖", cover_v))

    ok_all = True
    for kind, path in required:
        prog(f"上传{kind}封面: {path.name}")
        ok = await _upload_one_cover_via_modal(page, kind=kind, image=path, progress=progress)
        if ok:
            prog(f"{kind}封面已保存")
        else:
            ok_all = False
            prog(f"{kind}封面上传失败: {path.name}")
            await _save_debug_shot(page, f"cover_fail_{kind}")
            await _close_cover_modal_if_open(page)

    # Platform tip: 横封面缺失 / 竖封面缺失 → one more retry
    for attempt in range(2):
        missing = await _detect_missing_cover_kinds(page)
        if not missing:
            break
        prog(f"检测到封面缺失提示: {','.join(missing)}，补传…")
        for kind in missing:
            path = cover_h if kind == "横" else cover_v
            if not path:
                ok_all = False
                continue
            ok = await _upload_one_cover_via_modal(page, kind=kind, image=path, progress=progress)
            if not ok:
                ok_all = False
            await page.wait_for_timeout(800)
        # Re-run 快速检测 if button exists
        try:
            recheck = page.locator("text=重新检测").first
            if await recheck.count() > 0 and await recheck.is_visible():
                await recheck.click(timeout=2000)
                await page.wait_for_timeout(1500)
        except Exception:
            pass

    if await _detect_missing_cover_kinds(page):
        ok_all = False
        prog("补传后仍有封面缺失提示")
    return ok_all


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
    # New UI: title「设置封面」+ 保存/重新上传; old UI: 设置竖/横封面
    for sel in (
        "text=设置封面",
        "text=设置竖封面",
        "text=设置横封面",
        "text=竖封面预览",
        "text=横封面预览",
        "text=重新上传",
        "button:has-text('保存')",
    ):
        loc = page.locator(sel).first
        try:
            if await loc.count() == 0 or not await loc.is_visible():
                continue
            # Avoid matching the form section label alone — need modal chrome
            if sel == "text=设置封面":
                save = page.locator("button:has-text('保存')").first
                reup = page.locator("text=重新上传").first
                if (await save.count() > 0 and await save.is_visible()) or (
                    await reup.count() > 0 and await reup.is_visible()
                ):
                    return True
                continue
            if sel == "button:has-text('保存')":
                # Save on main page? Prefer when 重新上传 / 设置封面 modal nearby
                if await page.locator("text=重新上传").count() > 0:
                    return True
                continue
            return True
        except Exception:
            continue
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


async def _upload_one_cover_via_modal(
    page: Page,
    *,
    kind: str,
    image: Path,
    progress: ProgressCb | None = None,
) -> bool:
    """kind = 竖|横. Open cover card → modal → +上传封面 → 完成; fallbacks if modal missing."""

    def prog(msg: str) -> None:
        if progress:
            progress(msg)

    tab_title = "设置竖封面" if kind == "竖" else "设置横封面"
    # Exact UI labels from Douyin form
    slot_texts = (
        ("竖封面3:4", "竖封面", "3:4", "封面（竖版）")
        if kind == "竖"
        else ("横封面4:3", "横封面", "4:3", "封面（横版）")
    )

    await page.evaluate("window.scrollTo(0, 400)")
    await page.wait_for_timeout(400)
    # Scroll 设置封面 into view if present
    try:
        sec = page.locator("text=设置封面").first
        if await sec.count() > 0:
            await sec.scroll_into_view_if_needed()
            await page.wait_for_timeout(300)
    except Exception:
        pass

    if await _cover_modal_open(page):
        try:
            tab = page.locator(f"text={tab_title}").first
            if await tab.count() > 0:
                await tab.click(timeout=3000)
                await page.wait_for_timeout(600)
        except Exception:
            pass
    else:
        opened = await _open_cover_slot(page, slot_texts, kind=kind, progress=progress)
        if not opened:
            # Fallback without modal: file chooser / set_input_files near slot
            prog(f"{kind}封面弹窗未开，尝试直接选文件...")
            if await _direct_cover_file_near_slot(page, slot_texts, image):
                await _confirm_cover_if_possible(page)
                return True
            prog(f"未打开{kind}封面弹窗")
            await _save_debug_shot(page, f"cover_no_modal_{kind}")
            return False

    # Ensure correct tab
    try:
        tab = page.locator(f"text={tab_title}").first
        if await tab.count() > 0:
            await tab.click(timeout=2500)
            await page.wait_for_timeout(500)
    except Exception:
        pass

    uploaded = await _modal_pick_cover_file(page, image)
    if not uploaded:
        prog(f"{kind}封面：未能选择本地文件")
        await _save_debug_shot(page, f"cover_nofile_{kind}")
        return False

    if not await _wait_cover_save_enabled(page, timeout_ms=90_000):
        prog(f"{kind}封面：等待「保存/完成」可点超时")
        await _save_debug_shot(page, f"cover_wait_{kind}")
        return False

    if not await _click_cover_save_or_done(page):
        prog(f"{kind}封面：点击「保存/完成」失败")
        return False
    # Wait modal close
    for _ in range(20):
        if not await _cover_modal_open(page):
            break
        await page.wait_for_timeout(300)
    return True


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
    """Inside cover modal: 上传封面 / 重新上传 + file chooser."""
    upload_sels = (
        "button:has-text('重新上传')",
        "text=重新上传",
        "button:has-text('上传封面')",
        "text=+ 上传封面",
        "text=上传封面",
        "[class*='upload']:has-text('上传封面')",
        "[class*='upload']:has-text('重新上传')",
    )
    for sel in upload_sels:
        btn = page.locator(sel).first
        try:
            if await btn.count() == 0 or not await btn.is_visible():
                continue
            try:
                async with page.expect_file_chooser(timeout=4000) as fc_info:
                    await btn.click(timeout=3000)
                chooser = await fc_info.value
                await chooser.set_files(str(image))
                await page.wait_for_timeout(1500)
                return True
            except Exception:
                before = await _count_image_inputs(page)
                await btn.click(timeout=3000)
                await page.wait_for_timeout(600)
                if await _set_image_file_input(page, image, prefer_after=before):
                    await page.wait_for_timeout(1500)
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
            if disabled is not None or aria in ("true", "True") or "disabled" in cls:
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
    "内容由AI生成",
)


async def _visible_any(page: Page, keywords: tuple[str, ...]) -> str | None:
    for kw in keywords:
        loc = page.locator(f"text={kw}").first
        try:
            if await loc.count() > 0 and await loc.is_visible():
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
    wait_sec: int = 240,
) -> dict[str, Any]:
    """Click publish; SUCCESS only if navigated to 作品管理 (/content/manage)."""

    def prog(msg: str) -> None:
        if progress:
            progress(msg)

    async def click_once() -> bool:
        btn = await _find_publish_button(page)
        if btn is None:
            return False
        try:
            await btn.scroll_into_view_if_needed(timeout=3000)
        except Exception:
            pass
        try:
            await btn.click(timeout=5000)
        except Exception:
            return False
        await page.wait_for_timeout(1200)
        for confirm in (
            page.get_by_role("button", name="确认发布", exact=True),
            page.locator("button:has-text('确认发布')"),
        ):
            try:
                if await confirm.count() > 0 and await confirm.first.is_visible():
                    await confirm.first.click(timeout=3000)
                    await page.wait_for_timeout(800)
                    break
            except Exception:
                continue
        return True

    if not await click_once():
        await _save_debug_shot(page, "publish_no_button")
        return {"ok": False, "message": "未找到可点的「发布」按钮", "url": page.url}

    deadline = time.time() + max(wait_sec, 90)
    verify_hint = False
    last_blocker = ""
    retries = 0

    while time.time() < deadline:
        url = page.url or ""

        # Hard success: must land on content manage.
        if _is_manage_url(url):
            return {"ok": True, "message": "发布成功（已进入作品管理）", "url": url}

        # Soft success copy only after leaving editor pages.
        if not _is_editor_url(url):
            hit = await _visible_any(page, _SUCCESS_KW)
            if hit:
                return {"ok": True, "message": f"发布成功（{hit}）", "url": url}

        blocker = await _visible_any(page, _BLOCKER_KW)
        if blocker and blocker != last_blocker:
            last_blocker = blocker
            prog(f"发布受阻提示：{blocker}")
            await _prepare_before_publish(page)

        vkw = await _visible_any(page, _VERIFY_KW)
        if vkw:
            if not verify_hint:
                verify_hint = True
                prog(f"抖音要求人工验证（{vkw}），请在浏览器中完成，最长等待 {wait_sec}s")
                await _save_debug_shot(page, "publish_verify")
            await page.wait_for_timeout(2000)
            continue

        # Never spam 发布: cover modal / cover blocker → stop retrying
        if await _cover_modal_open(page):
            prog("封面弹窗仍打开，停止重复点击发布")
            await _save_debug_shot(page, "publish_cover_modal")
            return {
                "ok": False,
                "message": "封面设置弹窗未关闭，未继续点击发布",
                "url": url,
            }
        if last_blocker and any(k in last_blocker for k in ("封面", "标题")):
            prog(f"表单未就绪（{last_blocker}），停止重复点击发布")
            return {
                "ok": False,
                "message": f"发布受阻：{last_blocker}（未重复点击）",
                "url": url,
            }

        # At most one gentle re-click if still on editor and no blocker
        if _is_editor_url(url) and retries < 1 and not last_blocker and not verify_hint:
            still = await _find_publish_button(page)
            if still is not None:
                try:
                    if await still.is_enabled():
                        retries += 1
                        prog("仍在编辑页，再点一次发布确认...")
                        await click_once()
                except Exception:
                    pass

        await page.wait_for_timeout(2000)

    url = page.url or ""
    await _save_debug_shot(page, "publish_unconfirmed")
    if verify_hint:
        return {
            "ok": False,
            "message": "发布被验证码/风控拦住，等待超时未进入作品管理",
            "url": url,
        }
    if last_blocker:
        return {
            "ok": False,
            "message": f"发布未成功，页面提示：{last_blocker}（未进入作品管理）",
            "url": url,
        }
    return {
        "ok": False,
        "message": "已点发布但未进入作品管理页，判定为失败。请打开创作者中心核对；截图见 data/debug",
        "url": url,
    }
