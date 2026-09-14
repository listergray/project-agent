"""
答案忠实度校验 + 图级 HITL 门控

【技能点】
  ✅ LCEL 忠实度评分（抗幻觉）
  ✅ langgraph.types.interrupt 人机协同（检索不足 / 忠实度失败）
"""
from __future__ import annotations

from typing import Any, Dict

from langgraph.types import interrupt
from loguru import logger
from pydantic import BaseModel, Field

from project_agent.clients.lcel import lcel_json
from project_agent.core import get_settings
from project_agent.utils import load


class FaithfulnessOut(BaseModel):
    grounded: bool = Field(..., description="答案是否可由上下文/工具支撑")
    score: float = Field(..., ge=0, le=1)
    reason: str = Field("")
    unsupported_claims: list[str] = Field(default_factory=list)


def q_n6c_hitl_retrieval(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    检索不足且已达 Self-RAG 重试上限 → 图级 interrupt。
    resume 后：rewrite 则回到 N2；approve 则带着弱上下文继续生成。
    """
    settings = get_settings()
    grade = state.get("self_rag_grade") or {}
    suggested = (grade.get("better_query") or state.get("rewritten_query") or state.get("user_query") or "")
    if not settings.enable_graph_hitl:
        logger.info("[HITL] 检索不足但未开启图级 HITL，继续生成")
        return {
            "hitl_skipped": True,
            "interrupted": False,
            "need_human_review": False,
        }

    payload = {
        "reason": "retrieval_insufficient",
        "message": "检索上下文不足以支撑可靠回答，请确认是否改写问题或仍要继续生成。",
        "suggested_query": suggested,
        "draft_answer": "",
        "sources": state.get("sources") or [],
        "self_rag_grade": grade,
        "user_query": state.get("user_query"),
    }
    decision = interrupt(payload)
    if not isinstance(decision, dict):
        decision = {"action": "approve"}

    action = str(decision.get("action") or "approve").lower()
    out: Dict[str, Any] = {
        "hitl_decision": decision,
        "interrupted": False,
        "need_human_review": False,
    }
    if action == "rewrite":
        new_q = (decision.get("rewritten_query") or suggested or "").strip()
        out.update({
            "rewritten_query": new_q,
            "self_rag_need_retry": True,
            "self_rag_retries": 0,
            "multi_queries": [new_q] if new_q else state.get("multi_queries") or [],
        })
        logger.info(f"[HITL] resume rewrite → {new_q[:80]!r}")
    else:
        out["self_rag_need_retry"] = False
        logger.info("[HITL] resume approve → 继续弱上下文生成")
    return out


def q_n7b_faithfulness(state: Dict[str, Any]) -> Dict[str, Any]:
    """N7b：LCEL 忠实度；失败时可 interrupt 或追加警告。"""
    settings = get_settings()
    answer = (state.get("answer") or "").strip()
    if not settings.enable_faithfulness or not answer:
        return {
            "faithfulness": {"grounded": True, "score": 1.0, "reason": "skipped", "unsupported_claims": []},
            "faithfulness_score": 1.0,
            "need_human_review": False,
        }
    # 跳过 RAG 时无文档上下文，仅靠工具结果；仍校验，但空工具+空上下文则放行避免误打断
    if state.get("need_rag") is False and not (state.get("reranked_candidates") or []) and not (state.get("tool_calls") or []):
        return {
            "faithfulness": {
                "grounded": True,
                "score": 1.0,
                "reason": "need_rag=false 且无工具结果，跳过文档忠实度",
                "unsupported_claims": [],
            },
            "faithfulness_score": 1.0,
            "need_human_review": False,
        }

    ctx = state.get("reranked_candidates") or []
    tools = state.get("tool_calls") or []
    snippets = []
    for i, c in enumerate(ctx[:5], 1):
        snippets.append(f"[{i}] {(c.get('content') or '')[:300]}")
    tool_snip = str(tools)[:1500]
    sys = load("rag_search_faithfulness") or (
        "你是答案忠实度评审。判断回答是否都能被「上下文」或「工具结果」支撑。\n"
        '只输出 JSON：{"grounded": bool, "score": 0~1, "reason": str, "unsupported_claims": [str]}'
    )
    user = (
        f"用户问题：{state.get('user_query')}\n\n"
        f"回答：\n{answer[:2000]}\n\n"
        f"上下文：\n{chr(10).join(snippets) or '（空）'}\n\n"
        f"工具结果摘要：\n{tool_snip or '（无）'}"
    )
    try:
        grade = lcel_json(sys, user, model=FaithfulnessOut, temperature=0)
        assert isinstance(grade, FaithfulnessOut)
        data = grade.model_dump()
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[Faithfulness] LCEL 失败，默认放行: {e}")
        data = {"grounded": True, "score": 0.5, "reason": f"校验失败放行: {e}", "unsupported_claims": []}

    score = float(data.get("score") or 0)
    grounded = bool(data.get("grounded"))
    logger.info(f"[Faithfulness] grounded={grounded} score={score} reason={data.get('reason','')[:80]}")

    if grounded and score >= 0.55:
        return {
            "faithfulness": data,
            "faithfulness_score": score,
            "need_human_review": False,
        }

    if settings.enable_graph_hitl:
        decision = interrupt({
            "reason": "faithfulness_failed",
            "message": "自动校验认为回答可能含有缺少出处的内容，请确认放行或改写问题。",
            "suggested_query": state.get("rewritten_query") or state.get("user_query"),
            "draft_answer": answer,
            "sources": state.get("sources") or [],
            "faithfulness": data,
            "user_query": state.get("user_query"),
        })
        if not isinstance(decision, dict):
            decision = {"action": "approve"}
        action = str(decision.get("action") or "approve").lower()
        if action == "rewrite":
            note = "\n\n> ⚠️ 已请求改写问题，请用新问法重新提问。"
            return {
                "faithfulness": data,
                "faithfulness_score": score,
                "need_human_review": True,
                "hitl_decision": decision,
                "answer": answer + note,
            }
        return {
            "faithfulness": data,
            "faithfulness_score": score,
            "need_human_review": False,
            "hitl_decision": decision,
        }

    warn = "\n\n> ⚠️ 自动忠实度校验：部分表述可能缺少出处支撑，请谨慎采信。"
    return {
        "faithfulness": data,
        "faithfulness_score": score,
        "need_human_review": True,
        "answer": answer + warn,
    }
