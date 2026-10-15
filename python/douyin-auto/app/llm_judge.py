"""DeepSeek (OpenAI-compatible) judge for Douyin publish form state.

deepseek-chat has NO vision - we send page text / DOM facts, not screenshots.
Optional vision endpoint can be configured separately (LLM_VISION_*).
"""
from __future__ import annotations

import json
import logging
import re
import urllib.request
from typing import Any

from app.config import settings

logger = logging.getLogger("douyin-auto.llm_judge")


def judge_publish_form(facts: dict[str, Any]) -> dict[str, Any]:
    """Ask LLM whether title / covers / topics look ready. Returns structured result."""
    if not settings.llm_enabled or not (settings.llm_api_key or "").strip():
        return {"ok": None, "skipped": True, "reason": "LLM not configured"}

    prompt = (
        "????????????????????? JSON ???????????????\n"
        "???\n"
        "1) title_ok ??? true?????????????\n"
        "2) ? expect_covers ? true?? cover_v_ok ? cover_h_ok ??? true\n"
        "3) topics_ok ??? true?????? #ai?? ? #???\n"
        "4) loading ? true ? cover_modal_open ? true ?????\n"
        "????? JSON ??????????\n"
        '{"ready":true/false,"title_ok":true/false,"cover_ok":true/false,'
        '"topics_ok":true/false,"reason":"??????"}\n\n'
        f"???\n{json.dumps(facts, ensure_ascii=False)}"
    )
    try:
        raw = _chat(prompt)
    except Exception as e:
        logger.warning("llm judge call failed: %s", e)
        return {"ok": None, "skipped": True, "reason": f"LLM call failed: {e}"}

    parsed = _parse_json_obj(raw)
    if not parsed:
        return {"ok": None, "skipped": True, "reason": f"LLM unparseable: {raw[:200]}"}
    ready = bool(parsed.get("ready"))
    return {
        "ok": ready,
        "skipped": False,
        "ready": ready,
        "title_ok": bool(parsed.get("title_ok")),
        "cover_ok": bool(parsed.get("cover_ok")),
        "topics_ok": bool(parsed.get("topics_ok")),
        "reason": str(parsed.get("reason") or ""),
        "raw": raw[:500],
    }


def _chat(user_prompt: str) -> str:
    base = (settings.llm_base_url or "https://api.deepseek.com").rstrip("/")
    if not base.endswith("/v1"):
        url = f"{base}/v1/chat/completions"
    else:
        url = f"{base}/chat/completions"
    body = {
        "model": settings.llm_model or "deepseek-chat",
        "temperature": 0,
        "messages": [
            {"role": "system", "content": "????? JSON??? Markdown?"},
            {"role": "user", "content": user_prompt},
        ],
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.llm_api_key}",
        },
        method="POST",
    )
    timeout = max(15, int(settings.llm_timeout or 60))
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    choices = payload.get("choices") or []
    if not choices:
        raise RuntimeError("empty choices")
    content = choices[0].get("message", {}).get("content") or ""
    return content if isinstance(content, str) else str(content)


def _parse_json_obj(text: str) -> dict[str, Any] | None:
    t = (text or "").strip()
    if not t:
        return None
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    try:
        obj = json.loads(t)
        return obj if isinstance(obj, dict) else None
    except Exception:
        m = re.search(r"\{[\s\S]*\}", t)
        if not m:
            return None
        try:
            obj = json.loads(m.group(0))
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None
