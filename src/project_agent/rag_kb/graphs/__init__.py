"""
RAG 知识库：LangGraph 图 + Checkpoint + 门面（run_import / run_search / resume_search）

【技能点 · LangGraph】
  ✅ StateGraph + 条件边（Self-RAG 回跳 / HITL / 忠实度）
  ✅ Sqlite Checkpoint（thread_id=session_id）
  ✅ 图级 interrupt HITL + Command(resume=...)
  ✅ 会话 JSON 记忆窗口裁剪

【技能点 · LCEL / Fusion】
  ✅ 节点内 LCEL（多查询、忠实度等）；图本身非 LCEL 管道
  ✅ 多查询 RAG-Fusion + RRF
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.errors import GraphInterrupt
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command
from loguru import logger

from project_agent.core import ROOT_DIR, get_settings, new_trace_id
from project_agent.rag_kb.nodes import IMPORT_NODES, SEARCH_NODES
from project_agent.rag_kb.state import ImportState, SearchState
from project_agent.utils import append_turn, load_trimmed_history

_CHECKPOINTER: SqliteSaver | None = None
_CKPT_CONN: sqlite3.Connection | None = None


def _get_checkpointer() -> SqliteSaver:
    global _CHECKPOINTER, _CKPT_CONN
    if _CHECKPOINTER is not None:
        return _CHECKPOINTER
    settings = get_settings()
    path = Path(settings.checkpoint_db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # SqliteSaver 需要保持 connection 存活
    _CKPT_CONN = sqlite3.connect(str(path), check_same_thread=False)
    _CHECKPOINTER = SqliteSaver(_CKPT_CONN)
    logger.info(f"[Checkpoint] SqliteSaver → {path}")
    return _CHECKPOINTER


def _build_import_graph() -> CompiledStateGraph:
    builder = StateGraph(ImportState)
    node_names = []
    for name, fn in IMPORT_NODES:
        builder.add_node(name, fn)
        node_names.append(name)

    builder.add_edge(START, node_names[0])
    for i, n in enumerate(node_names):
        if i == len(node_names) - 1:
            builder.add_edge(n, END)
        else:
            next_n = node_names[i + 1]
            builder.add_conditional_edges(
                n,
                lambda s, _nn=next_n: END if s.get("errors") else _nn,
                {next_n: next_n, END: END},
            )
    return builder.compile()


def _build_search_graph() -> CompiledStateGraph:
    """
    N1 → N1b → N2 → N3 → N4 → N5 → N6 → N6b
      ├─ retry → N2
      ├─ exhausted → N6c HITL → (rewrite→N2 | approve→N7)
      └─ ok → N7 → N7b → END
    """
    builder = StateGraph(SearchState)
    for name, fn in SEARCH_NODES:
        builder.add_node(name, fn)

    linear = [
        "q_n1_rewrite_intent",
        "q_n1b_multi_query",
        "q_n2_locate_item",
        "q_n3_vector_recall",
        "q_n4_tool_fuzzy_recall",
        "q_n5_rrf_fusion",
        "q_n6_rerank",
    ]
    builder.add_edge(START, linear[0])
    for i, n in enumerate(linear):
        next_n = linear[i + 1] if i + 1 < len(linear) else "q_n6b_self_rag_grade"
        builder.add_conditional_edges(
            n,
            lambda s, _nn=next_n: END if s.get("errors") else _nn,
            {next_n: next_n, END: END},
        )

    def _route_self_rag(s: Dict[str, Any]) -> Any:
        if s.get("errors"):
            return END
        if s.get("self_rag_need_retry"):
            return "q_n2_locate_item"
        if s.get("self_rag_exhausted"):
            return "q_n6c_hitl_retrieval"
        return "q_n7_answer_with_tools"

    builder.add_conditional_edges(
        "q_n6b_self_rag_grade",
        _route_self_rag,
        {
            "q_n2_locate_item": "q_n2_locate_item",
            "q_n6c_hitl_retrieval": "q_n6c_hitl_retrieval",
            "q_n7_answer_with_tools": "q_n7_answer_with_tools",
            END: END,
        },
    )

    def _route_hitl(s: Dict[str, Any]) -> Any:
        if s.get("errors"):
            return END
        if s.get("self_rag_need_retry"):
            return "q_n2_locate_item"
        return "q_n7_answer_with_tools"

    builder.add_conditional_edges(
        "q_n6c_hitl_retrieval",
        _route_hitl,
        {
            "q_n2_locate_item": "q_n2_locate_item",
            "q_n7_answer_with_tools": "q_n7_answer_with_tools",
            END: END,
        },
    )
    builder.add_edge("q_n7_answer_with_tools", "q_n7b_faithfulness")
    builder.add_edge("q_n7b_faithfulness", END)

    return builder.compile(checkpointer=_get_checkpointer())


_IMPORT_GRAPH: CompiledStateGraph | None = None
_SEARCH_GRAPH: CompiledStateGraph | None = None


def get_import_graph() -> CompiledStateGraph:
    global _IMPORT_GRAPH
    if _IMPORT_GRAPH is None:
        _IMPORT_GRAPH = _build_import_graph()
    return _IMPORT_GRAPH


def get_search_graph() -> CompiledStateGraph:
    global _SEARCH_GRAPH
    if _SEARCH_GRAPH is None:
        _SEARCH_GRAPH = _build_search_graph()
    return _SEARCH_GRAPH


def _search_config(sid: str, extra_meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    settings = get_settings()
    meta = {
        "session_id": sid,
        "enable_multi_query": settings.enable_multi_query,
        "enable_faithfulness": settings.enable_faithfulness,
        "enable_graph_hitl": settings.enable_graph_hitl,
    }
    if extra_meta:
        meta.update(extra_meta)
    return {
        "configurable": {"thread_id": sid},
        "run_name": "rag_search",
        "tags": ["project-agent", "rag", "self-rag", "fusion", "hitl"],
        "metadata": meta,
        "recursion_limit": 40,
    }


def _interrupt_payload_from_exc(exc: GraphInterrupt) -> Dict[str, Any]:
    raw = exc.args[0] if exc.args else ()
    if isinstance(raw, (list, tuple)) and raw:
        first = raw[0]
        val = getattr(first, "value", first)
        return val if isinstance(val, dict) else {"message": str(val)}
    if isinstance(raw, dict):
        return raw
    return {"message": str(exc)}


def _finalize_search_result(result: Dict[str, Any], sid: str, user_query: str) -> Dict[str, Any]:
    result = dict(result)
    result["session_id"] = sid
    result.setdefault("interrupted", False)
    append_turn(sid, "user", user_query)
    if result.get("answer") and not result.get("interrupted"):
        append_turn(sid, "assistant", str(result["answer"]))
    grade = result.get("self_rag_grade") or {}
    logger.info(
        f"[Search] done interrupted={result.get('interrupted')} "
        f"answer_len={len(result.get('answer') or '')} "
        f"self_rag_retries={result.get('self_rag_retries', 0)} "
        f"faithfulness={result.get('faithfulness_score')} "
        f"multi_q={len(result.get('multi_queries') or [])} session={sid[:12]}"
    )
    # enrich metadata for observability
    result.setdefault("retrieval_paths", result.get("retrieval_paths") or {})
    return result


def run_import(file_path: str | Path, *, thread_id: str | None = None) -> Dict[str, Any]:
    file_path = str(Path(file_path).expanduser().resolve())
    graph = get_import_graph()
    initial: ImportState = {
        "file_path": file_path,
        "trace_id": new_trace_id(),
    }
    config = {"configurable": {"thread_id": thread_id or f"imp_{initial['trace_id']}"}}
    result = graph.invoke(initial, config=config)
    if result.get("errors"):
        logger.error(f"[Import] 失败 errors={result['errors']}")
    else:
        logger.info(f"[Import] 成功: {result.get('import_result')}")
    return result


def run_search(user_query: str, *, session_id: str | None = None) -> Dict[str, Any]:
    from project_agent.core import configure_langsmith

    configure_langsmith()
    graph = get_search_graph()
    sid = session_id or f"sess_{new_trace_id()}"
    history = load_trimmed_history(sid)
    initial: SearchState = {
        "session_id": sid,
        "user_query": user_query,
        "trace_id": new_trace_id(),
        "messages": history,
        "self_rag_retries": 0,
        "self_rag_need_retry": False,
        "self_rag_exhausted": False,
        "interrupted": False,
    }
    config = _search_config(sid)
    try:
        result = graph.invoke(initial, config=config)
    except GraphInterrupt as e:
        payload = _interrupt_payload_from_exc(e)
        snap = graph.get_state(config)
        values = dict(snap.values) if snap and snap.values else {}
        values.update({
            "session_id": sid,
            "user_query": user_query,
            "interrupted": True,
            "interrupt_payload": payload,
            "answer": values.get("answer") or payload.get("draft_answer") or "",
        })
        logger.info(f"[Search] interrupted reason={payload.get('reason')} session={sid[:12]}")
        return values

    # 部分版本 interrupt 不抛异常，靠 next 判断
    snap = graph.get_state(config)
    if snap and snap.next:
        tasks = getattr(snap, "tasks", ()) or ()
        payload: Dict[str, Any] = {}
        for t in tasks:
            ints = getattr(t, "interrupts", ()) or ()
            for it in ints:
                val = getattr(it, "value", None)
                if isinstance(val, dict):
                    payload = val
                    break
        result = dict(snap.values or {})
        result.update({
            "session_id": sid,
            "interrupted": True,
            "interrupt_payload": payload,
            "answer": result.get("answer") or payload.get("draft_answer") or "",
        })
        logger.info(f"[Search] interrupted(state) reason={payload.get('reason')} session={sid[:12]}")
        return result

    return _finalize_search_result(result, sid, user_query)


def resume_search(
    session_id: str,
    *,
    action: str = "approve",
    rewritten_query: str | None = None,
) -> Dict[str, Any]:
    """从图级 interrupt 恢复：action=approve|rewrite。"""
    from project_agent.core import configure_langsmith

    configure_langsmith()
    graph = get_search_graph()
    sid = session_id
    config = _search_config(sid)
    resume_val: Dict[str, Any] = {"action": action}
    if rewritten_query:
        resume_val["rewritten_query"] = rewritten_query

    try:
        result = graph.invoke(Command(resume=resume_val), config=config)
    except GraphInterrupt as e:
        payload = _interrupt_payload_from_exc(e)
        snap = graph.get_state(config)
        values = dict(snap.values) if snap and snap.values else {}
        values.update({
            "session_id": sid,
            "interrupted": True,
            "interrupt_payload": payload,
            "answer": values.get("answer") or payload.get("draft_answer") or "",
        })
        return values

    snap = graph.get_state(config)
    if snap and snap.next:
        tasks = getattr(snap, "tasks", ()) or ()
        payload = {}
        for t in tasks:
            for it in getattr(t, "interrupts", ()) or ():
                val = getattr(it, "value", None)
                if isinstance(val, dict):
                    payload = val
                    break
        result = dict(snap.values or {})
        result.update({
            "session_id": sid,
            "interrupted": True,
            "interrupt_payload": payload,
        })
        return result

    user_query = str(result.get("user_query") or "")
    return _finalize_search_result(result, sid, user_query)


def import_sample_dir(sample_dir: str | Path = ROOT_DIR / "data" / "samples") -> List[Dict[str, Any]]:
    sample_dir = Path(sample_dir)
    files = sorted([p for p in sample_dir.glob("*") if p.suffix.lower() in {".md", ".markdown", ".txt", ".pdf"}])
    logger.info(f"[Import] 发现样例文件 {len(files)} 个：{[f.name for f in files]}")
    return [run_import(f) for f in files]


__all__ = [
    "get_import_graph",
    "get_search_graph",
    "run_import",
    "run_search",
    "resume_search",
    "import_sample_dir",
]
