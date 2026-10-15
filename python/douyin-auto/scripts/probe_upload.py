# -*- coding: utf-8 -*-
"""Probe Douyin creator upload page for file inputs and upload UI."""
from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path

from playwright.async_api import Frame, Page, async_playwright

UPLOAD_URL = "https://creator.douyin.com/creator-micro/content/upload"
PROFILE = Path(__file__).resolve().parents[1] / "data" / "browser-profile"
DATA = Path(__file__).resolve().parents[1] / "data"
SCREENSHOT = DATA / "debug_upload.png"
HTML_DUMP = DATA / "debug_upload.html"
MAX_HTML = 200_000

KEYWORDS = ("\u4e0a\u4f20", "\u9009\u62e9", "\u89c6\u9891", "\u53d1\u5e03")


async def file_inputs_in(root: Page | Frame) -> list[dict]:
    rows: list[dict] = []
    loc = root.locator('input[type="file"]')
    count = await loc.count()
    for i in range(count):
        inp = loc.nth(i)
        rows.append(
            {
                "accept": await inp.get_attribute("accept"),
                "visible": await inp.is_visible(),
                "attached": await inp.evaluate(
                    "el => el.isConnected && document.contains(el)"
                ),
                "name": await inp.get_attribute("name"),
                "class": await inp.get_attribute("class"),
            }
        )
    return rows


async def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    DATA.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE),
            headless=False,
            viewport={"width": 1400, "height": 900},
            locale="zh-CN",
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else await context.new_page()
        try:
            await page.goto(UPLOAD_URL, wait_until="networkidle", timeout=120_000)
            await page.wait_for_timeout(5000)

            print("=== Page ===")
            print("final URL:", page.url)
            print("title:", await page.title())

            print("\n=== input[type=file] on main frame ===")
            main_rows = await file_inputs_in(page)
            print("count:", len(main_rows))
            for i, row in enumerate(main_rows):
                print(f"  [{i}]", row)

            print("\n=== All frames ===")
            for fi, fr in enumerate(page.frames):
                rows = await file_inputs_in(fr)
                print(f"  frame[{fi}] url={fr.url!r} file_inputs={len(rows)}")
                for j, row in enumerate(rows):
                    print(f"    [{j}]", row)

            print("\n=== Text matches, first 15 ===")
            seen: list[str] = []
            for kw in KEYWORDS:
                loc = page.get_by_text(kw, exact=False)
                n = min(await loc.count(), 20)
                for j in range(n):
                    if len(seen) >= 15:
                        break
                    try:
                        el = loc.nth(j)
                        if not await el.is_visible():
                            continue
                        text = re.sub(r"\s+", " ", (await el.inner_text()).strip())[:120]
                        if text and text not in seen:
                            seen.append(text)
                            print(f"  [{kw}] {text!r}")
                    except Exception:
                        pass
                if len(seen) >= 15:
                    break

            cookies = await context.cookies()
            names = {c.get("name") for c in cookies}
            logged = bool({"sessionid", "sid_guard", "uid_tt"} & names)
            html = await page.content()
            body_lower = html.lower()
            login_wall = not logged and any(
                x in body_lower for x in ("login", "qrcode", "\u626b\u7801", "\u767b\u5f55")
            )
            print("\n=== Login ===")
            print("cookie login indicators:", logged)
            print("likely login wall:", login_wall)

            await page.screenshot(path=str(SCREENSHOT), full_page=True)
            print("\nScreenshot:", SCREENSHOT)

            snippet = await page.evaluate(
                "() => (document.body && document.body.outerHTML) || ''"
            )
            if len(snippet) > MAX_HTML:
                snippet = snippet[:MAX_HTML] + "\n<!-- truncated -->"
            HTML_DUMP.write_text(snippet, encoding="utf-8")
            print("HTML snippet:", HTML_DUMP, f"({len(snippet)} chars)")

            shadow_count = await page.evaluate(
                """() => {
                let n = 0;
                document.querySelectorAll('*').forEach(el => {
                    if (el.shadowRoot) {
                        n += el.shadowRoot.querySelectorAll('input[type="file"]').length;
                    }
                });
                return n;
            }"""
            )
            print("shadow DOM file inputs:", shadow_count)
        finally:
            await context.close()


if __name__ == "__main__":
    asyncio.run(main())
