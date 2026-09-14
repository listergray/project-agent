"""Windows 控制台 UTF-8 输出（避免 emoji / 中文在 GBK 终端报 UnicodeEncodeError）。"""
from __future__ import annotations

import sys


def ensure_utf8_stdio() -> None:
    if not hasattr(sys.stdout, "reconfigure"):
        return
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
