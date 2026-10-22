"""Evidence for a submitted work; returning to the upload page alone is ambiguous."""
from __future__ import annotations

import re
import time
from urllib.parse import urlsplit

from playwright.async_api import Page


MANAGE_URL = "https://creator.douyin.com/creator-micro/content/manage"


def is_publish_request(url: str, method: str) -> bool:
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    return (
        method.upper() == "POST"
        and (host == "douyin.com" or host.endswith(".douyin.com"))
        and bool(re.search(r"/(?:aweme|content|video)(?:/[^/?]+){0,5}/(?:create|publish|post)(?:/|$)", parsed.path))
    )


def submission_evidence(payload: object) -> dict | None:
    if not isinstance(payload, dict):
        return None
    code = payload.get("status_code", payload.get("code"))
    if code is None or isinstance(code, bool):
        return None
    if str(code) != "0":
        return {"ok": False, "code": str(code), "message": str(payload.get("status_msg") or payload.get("message") or "发布接口拒绝提交")[:180]}
    containers = [payload]
    for key in ("data", "aweme", "aweme_info", "item"):
        child = payload.get(key)
        if isinstance(child, dict):
            containers.append(child)
            containers.extend(value for key, value in child.items() if key in ("aweme", "aweme_info", "item") and isinstance(value, dict))
    for item in containers:
        for key in ("aweme_id", "item_id"):
            work_id = str(item.get(key) or "")
            if work_id.isdigit() and len(work_id) >= 8:
                return {"ok": True, "workId": work_id, "source": "publish_response"}
    # A generic code=0 from an upload/configuration endpoint is insufficient.
    return None


async def find_work(page: Page, title: str, *, timeout_sec: float = 15) -> dict | None:
    """Match this title and a published/reviewing status in its own management row."""
    expected = title.strip()[:30]
    if not expected:
        return None
    deadline = time.monotonic() + max(0, timeout_sec)
    while True:
        if "/content/manage" not in (page.url or ""):
            return None
        matches = page.get_by_text(re.compile(r"^" + re.escape(expected) + r"(?:\s|#|$)"))
        for i in range(min(await matches.count(), 20)):
            item = matches.nth(i)
            if not await item.is_visible():
                continue
            await item.scroll_into_view_if_needed(timeout=2000)
            evidence = await item.evaluate(r"""el => {
                let node = el;
                for (let i = 0; node && node !== document.body && i < 5; i++, node = node.parentElement) {
                    if (node.matches('[role="list"]') || node.querySelectorAll('article,[role="listitem"]').length > 1) break;
                    const text = node.innerText || '';
                    if (text.length > 1500) break;
                    if (/草稿|发布失败|审核未通过/.test(text)) continue;
                    const status = text.match(/审核中|审核通过|已发布|已公开|公开可见|公开视频|仅自己可见/);
                    if (status) return {status: status[0]};
                }
                return null;
            }""")
            if evidence:
                return {"source": "content_manage", "title": expected, **evidence}
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        await page.wait_for_timeout(min(500, remaining * 1000))


async def check_management(page: Page, title: str, *, timeout_sec: float = 20) -> dict | None:
    if not title:
        return None
    await page.goto(MANAGE_URL, wait_until="domcontentloaded", timeout=max(1, int(timeout_sec * 1000)))
    return await find_work(page, title, timeout_sec=timeout_sec)
