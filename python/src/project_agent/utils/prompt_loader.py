"""Prompt 模板加载器：读 prompts/*.txt，可直接打开 txt 文件展示"调优过的 Prompt"。"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict

from project_agent.core import ROOT_DIR

PROMPT_DIR = ROOT_DIR / "python" / "prompts"


@lru_cache(maxsize=256)
def load(name: str) -> str:
    """name 是 prompts/ 目录下的文件名（不带 .txt 也行）。找不到返回空字符串。"""
    if not name.endswith(".txt"):
        name += ".txt"
    p = PROMPT_DIR / name
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8").strip()


def load_all() -> Dict[str, str]:
    """返回 {文件名(不含txt): 内容}，用于 API 展示 prompt 列表。"""
    out: Dict[str, str] = {}
    for p in sorted(PROMPT_DIR.glob("*.txt")):
        out[p.stem] = p.read_text(encoding="utf-8").strip()
    return out


__all__ = ["load", "load_all", "PROMPT_DIR"]
