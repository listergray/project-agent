"""
多查询 RAG-Fusion：LCEL 生成多问 + 并行向量召回合并

【技能点 · RAG-Fusion】
  ✅ 一问多改写（LCEL JSON）
  ✅ 批量 Embedding + ThreadPool 并行 Milvus 召回
  ✅ 多路向量召回后在 N5 与模糊结果一起 RRF
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Tuple

from loguru import logger
from pydantic import BaseModel, Field

from project_agent.clients import encode, hybrid_search_chunks
from project_agent.clients.lcel import lcel_json
from project_agent.core import get_settings
from project_agent.utils import load


class MultiQueryOut(BaseModel):
    queries: List[str] = Field(..., min_length=1, description="改写后的检索问句列表")


def q_n1b_multi_query(state: Dict[str, Any]) -> Dict[str, Any]:
    """N1b：生成 multi_queries（含 rewritten_query）。关闭开关时仅保留单查询。"""
    settings = get_settings()
    base = (state.get("rewritten_query") or state.get("user_query") or "").strip()
    if not settings.enable_multi_query:
        return {"multi_queries": [base] if base else []}

    n = max(2, min(5, int(settings.multi_query_count)))
    sys = load("rag_search_multi_query") or (
        "你是检索查询改写器。基于用户问题生成多个语义不同但意图一致的检索问句。\n"
        '只输出 JSON：{"queries": ["问句1", "问句2", ...]}'
    )
    user = (
        f"原问题：{state.get('user_query')}\n"
        f"已改写：{base}\n"
        f"请生成恰好 {n} 条中文检索问句（可包含已改写句），覆盖同义词与不同表述。"
    )
    queries: List[str] = []
    try:
        out = lcel_json(sys, user, model=MultiQueryOut, temperature=0)
        assert isinstance(out, MultiQueryOut)
        queries = [q.strip() for q in out.queries if q and q.strip()]
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[Search N1b] multi-query LCEL 失败，单查询兜底: {e}")
        queries = []

    if base and base not in queries:
        queries = [base] + queries
    # 去重保序，截断到 n
    seen = set()
    uniq: List[str] = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            uniq.append(q)
        if len(uniq) >= n:
            break
    if not uniq and base:
        uniq = [base]
    logger.info(f"[Search N1b] multi_queries={len(uniq)} → {uniq!r}")
    return {"multi_queries": uniq}


def _search_one(
    qi: int,
    q: str,
    q_vec: List[float],
    item_pk: Any,
    item_name: Any,
) -> Tuple[int, str, List[dict]]:
    try:
        hits = hybrid_search_chunks(
            q_vec,
            top_k=30,
            item_pk_filter=item_pk,
            item_name_filter=item_name,
        )
        return qi, q, hits or []
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[Search N3] query#{qi} 召回失败: {e}")
        return qi, q, []


def q_n3_vector_recall(state: Dict[str, Any]) -> Dict[str, Any]:
    """N3：批量 encode + 并行 Milvus 召回，打上来源标签后合并（RRF 在 N5）。"""
    queries = state.get("multi_queries") or []
    if not queries:
        q = state.get("rewritten_query") or state.get("user_query") or ""
        queries = [q] if q else []

    item_pk = state.get("confirmed_item_pk")
    item_name = state.get("confirmed_item_name")
    all_hits: List[dict] = []
    seen_pk: set = set()

    if not queries:
        return {
            "recalled_chunks": [],
            "retrieval_paths": {"vector_queries": [], "vector_hits": 0, "parallel": True},
        }

    try:
        vectors = encode(list(queries))
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[Search N3] 批量 encode 失败，逐条兜底: {e}")
        vectors = []
        for q in queries:
            try:
                vectors.append(encode([q])[0])
            except Exception as e2:  # noqa: BLE001
                logger.warning(f"[Search N3] encode 单条失败: {e2}")
                vectors.append(None)  # type: ignore[arg-type]

    workers = min(4, max(1, len(queries)))
    results: List[Tuple[int, str, List[dict]]] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = []
        for qi, q in enumerate(queries):
            vec = vectors[qi] if qi < len(vectors) else None
            if vec is None:
                results.append((qi, q, []))
                continue
            futs.append(pool.submit(_search_one, qi, q, vec, item_pk, item_name))
        for fut in as_completed(futs):
            results.append(fut.result())

    # 按 query 下标排序，保证「原改写优先」去重语义稳定
    results.sort(key=lambda x: x[0])
    for qi, q, hits in results:
        for h in hits:
            pk = h.get("pk")
            h = dict(h)
            h["fusion_query"] = q
            h["fusion_query_idx"] = qi
            if pk in seen_pk:
                continue
            seen_pk.add(pk)
            all_hits.append(h)

    logger.info(
        f"[Search N3] 并行召回 workers={workers} queries={len(queries)} "
        f"unique_chunks={len(all_hits)}"
    )
    return {
        "recalled_chunks": all_hits,
        "retrieval_paths": {
            "vector_queries": queries,
            "vector_hits": len(all_hits),
            "parallel": True,
            "workers": workers,
        },
    }
