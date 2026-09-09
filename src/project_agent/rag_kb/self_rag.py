"""
Self-RAG：检索文档质量评估 + 不合格则改写 Query 再检索

【技能点 · Self-RAG】
  ✅ Grade：判断精排上下文是否足以回答问题
  ✅ Transform：不足则 LLM 改写 rewritten_query
  ✅ Retry：条件边回到定位/召回节点（有上限，避免死循环）
"""
from __future__ import annotations

import json
from typing import Any, Dict

from loguru import logger
from pydantic import BaseModel, Field

from project_agent.clients import achain
from project_agent.core import get_settings
from project_agent.utils import load


class GradeOutput(BaseModel):
    relevant: bool = Field(..., description="当前检索上下文是否足以支撑回答")
    score: float = Field(..., ge=0, le=1, description="相关度 0~1")
    reason: str = Field("", description="简要理由")
    better_query: str = Field("", description="若不相关，给出更利于检索的改写问句")


def q_n6b_self_rag_grade(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    N6b Self-RAG Grade：评估 reranked_candidates。
    - 相关 → 进入 N7 生成
    - 不相关且未超重试次数 → 改写 query，标记 self_rag_need_retry=True
    """
    settings = get_settings()
    max_retries = max(0, int(getattr(settings, "self_rag_max_retries", 1)))
    retries = int(state.get("self_rag_retries") or 0)
    docs = state.get("reranked_candidates") or []
    q = state.get("rewritten_query") or state.get("user_query") or ""

    # 无文档：TOOL_FIRST 仍可走工具，不必强行重检索
    intent = state.get("intent") or "MIXED"
    if not docs:
        if intent == "TOOL_FIRST":
            logger.info("[Self-RAG] 无文档但 TOOL_FIRST，跳过重试直接生成")
            return {
                "self_rag_need_retry": False,
                "self_rag_exhausted": False,
                "self_rag_grade": {"relevant": True, "score": 0.0, "reason": "无文档，依赖工具", "better_query": ""},
            }
        grade = _grade_with_llm(q, docs) if retries < max_retries else {
            "relevant": False, "score": 0.0, "reason": "无检索结果且已达重试上限", "better_query": "",
        }
        return _decide_retry(state, grade, retries, max_retries)

    # 启发式：平均分数过低则倾向不相关（LLM 失败时兜底）
    heuristic_ok = _heuristic_relevant(docs)
    grade = _grade_with_llm(q, docs)
    if not grade.get("relevant") and heuristic_ok and grade.get("score", 0) >= 0.35:
        # LLM 过严时用启发式放行，避免无谓重试
        grade["relevant"] = True
        grade["reason"] = (grade.get("reason") or "") + "（启发式放行）"

    return _decide_retry(state, grade, retries, max_retries)


def _heuristic_relevant(docs: list) -> bool:
    scores = []
    for d in docs[:5]:
        for k in ("score", "rrf_score"):
            if isinstance(d.get(k), (int, float)):
                scores.append(float(d[k]))
                break
    if not scores:
        return len(docs) > 0
    return (sum(scores) / len(scores)) >= 0.08 or max(scores) >= 0.15


def _grade_with_llm(query: str, docs: list) -> Dict[str, Any]:
    snippets = []
    for i, c in enumerate(docs[:5], 1):
        snippets.append(
            f"[{i}] {c.get('item_name','')}/{c.get('title_path','')}: "
            f"{(c.get('content') or '')[:280]}"
        )
    sys = load("rag_search_self_rag_grade") or (
        "你是 Self-RAG 检索评估器。判断给定上下文能否支撑回答用户问题。\n"
        "只输出 JSON：{\"relevant\": bool, \"score\": 0~1, \"reason\": str, \"better_query\": str}\n"
        "relevant=false 时 better_query 必须给出更具体、含关键词的检索问句。"
    )
    user = f"用户问题：{query}\n\n检索上下文：\n" + ("\n".join(snippets) if snippets else "（空）")
    try:
        txt = achain(sys, user, json_mode=True, temperature=0)
        obj = json.loads(txt if isinstance(txt, str) else str(txt))
        return GradeOutput.model_validate(obj).model_dump()
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[Self-RAG] LLM grade 失败，启发式兜底: {e}")
        ok = _heuristic_relevant(docs) if docs else False
        return {
            "relevant": ok,
            "score": 0.5 if ok else 0.1,
            "reason": f"LLM 失败兜底 heuristic_ok={ok}",
            "better_query": query if not ok else "",
        }


def _decide_retry(
    state: Dict[str, Any],
    grade: Dict[str, Any],
    retries: int,
    max_retries: int,
) -> Dict[str, Any]:
    relevant = bool(grade.get("relevant"))
    need = (not relevant) and (retries < max_retries)
    exhausted = (not relevant) and (retries >= max_retries)
    out: Dict[str, Any] = {
        "self_rag_grade": grade,
        "self_rag_need_retry": need,
        "self_rag_retries": retries + (1 if need else 0),
        "self_rag_exhausted": exhausted,
    }
    if need:
        better = (grade.get("better_query") or "").strip() or state.get("user_query") or ""
        out["rewritten_query"] = better
        out["multi_queries"] = [better]
        logger.info(
            f"[Self-RAG] 上下文不足 → 重试#{retries + 1}/{max_retries} "
            f"new_query={better[:80]!r} reason={grade.get('reason','')[:80]!r}"
        )
    else:
        logger.info(
            f"[Self-RAG] grade relevant={relevant} score={grade.get('score')} "
            f"retries={retries} exhausted={exhausted} → 下一跳"
        )
    return out
