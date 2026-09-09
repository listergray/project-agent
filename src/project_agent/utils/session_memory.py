"""
会话记忆 + 消息窗口裁剪

【技能点 · LLM 工程化】
  ✅ 按 session_id 持久化多轮对话（本地 JSON）
  ✅ 窗口裁剪：保留 system + 最近 N 轮，并限制总字符数
"""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import List, Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from loguru import logger

from project_agent.core import ROOT_DIR, get_settings

_lock = threading.Lock()
_SESSION_DIR = ROOT_DIR / "data" / "sessions"


def _path(session_id: str) -> Path:
    safe = "".join(c for c in session_id if c.isalnum() or c in "-_")[:80] or "default"
    _SESSION_DIR.mkdir(parents=True, exist_ok=True)
    return _SESSION_DIR / f"{safe}.json"


def load_turns(session_id: str) -> List[dict]:
    """返回 [{role: user|assistant, content: str}, ...]"""
    p = _path(session_id)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[Session] 读取失败 {session_id}: {e}")
        return []


def append_turn(session_id: str, role: str, content: str) -> None:
    if not session_id or not content:
        return
    with _lock:
        turns = load_turns(session_id)
        turns.append({"role": role, "content": content})
        # 落盘前先粗裁，避免文件无限增长
        settings = get_settings()
        max_turns = max(2, int(getattr(settings, "chat_max_history_turns", 12)) * 2)
        if len(turns) > max_turns:
            turns = turns[-max_turns:]
        _path(session_id).write_text(
            json.dumps(turns, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def trim_messages(
    messages: Sequence[BaseMessage],
    *,
    max_messages: int | None = None,
    max_chars: int | None = None,
) -> List[BaseMessage]:
    """
    保留开头连续的 SystemMessage，再保留尾部消息，使总条数/总字符受控。
    """
    settings = get_settings()
    max_messages = max_messages if max_messages is not None else int(
        getattr(settings, "chat_max_history_messages", 16)
    )
    max_chars = max_chars if max_chars is not None else int(
        getattr(settings, "chat_max_history_chars", 6000)
    )

    msgs = list(messages)
    systems: List[BaseMessage] = []
    rest: List[BaseMessage] = []
    for m in msgs:
        if isinstance(m, SystemMessage) and not rest:
            systems.append(m)
        else:
            rest.append(m)

    # 先按条数裁剪 rest
    keep_n = max(0, max_messages - len(systems))
    if len(rest) > keep_n:
        rest = rest[-keep_n:]

    # 再按字符从尾部累加
    def _len(m: BaseMessage) -> int:
        c = m.content
        return len(c) if isinstance(c, str) else len(str(c))

    picked: List[BaseMessage] = []
    total = sum(_len(s) for s in systems)
    for m in reversed(rest):
        L = _len(m)
        if picked and total + L > max_chars:
            break
        picked.append(m)
        total += L
    picked.reverse()
    return systems + picked


def turns_to_messages(turns: List[dict]) -> List[BaseMessage]:
    out: List[BaseMessage] = []
    for t in turns:
        role = (t.get("role") or "").lower()
        content = t.get("content") or ""
        if role in ("user", "human"):
            out.append(HumanMessage(content=content))
        elif role in ("assistant", "ai"):
            out.append(AIMessage(content=content))
        elif role == "system":
            out.append(SystemMessage(content=content))
    return out


def format_history_for_prompt(messages: Sequence[BaseMessage]) -> str:
    lines = []
    for m in messages:
        if isinstance(m, SystemMessage):
            continue
        role = "用户" if isinstance(m, HumanMessage) else "助手"
        content = m.content if isinstance(m.content, str) else str(m.content)
        lines.append(f"{role}：{content[:800]}")
    return "\n".join(lines) if lines else "（无历史）"


def load_trimmed_history(session_id: str) -> List[BaseMessage]:
    turns = load_turns(session_id)
    return trim_messages(turns_to_messages(turns))
