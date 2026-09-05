"""
Milvus 客户端（向量库，封装 RAG 知识库常用的：建集合 / 查集合 / 混合检索 / 批量插入）
设计说明：
1. 我用两个 Collection 做双层索引：kb_item_names（文档级检索，定位是"哪本手册"）
   + kb_chunks（段落级，取具体章节内容），解决"长文档命中章节分散"问题
2. 混合检索：dense 向量 cosine 相似 + 关键字（item_name/title）过滤权重融合
3. 幂等：插入前按 pk 删重，避免重复导入导致向量膨胀
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, List, Optional

from loguru import logger
from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    MilvusClient,
    connections,
    utility,
)

from project_agent.core import get_settings

# ===== 常量（Collection 名 + 字段名 + 维度在 Milvus 里强绑定） =====
COLL_ITEM_NAMES = "kb_item_names"       # 文档级（知识库有哪些"书"）
COLL_CHUNKS = "kb_chunks"               # 段落级（书里分了哪些 chunk）
VECTOR_FIELD = "dense_vector"
SPARSE_FIELD = "sparse_vector"          # 预留字段（MVP 先用 dense，后续扩展 HyDE/稀疏）


def _default_dense_dim() -> int:
    # 首次编码时才去查 embed 模型真实维度；MVP 默认 512（bge-small-zh-v1.5 维度）
    try:
        from project_agent.clients.embed_client import get_embedding_dim
        return get_embedding_dim()
    except Exception:  # noqa: BLE001
        return 512


@lru_cache(maxsize=1)
def _connect() -> None:
    s = get_settings()
    connections.connect(
        alias=s.milvus_alias,
        host=s.milvus_host,
        port=s.milvus_port,
        timeout=3,
    )
    logger.info(f"[Milvus] connected {s.milvus_host}:{s.milvus_port} alias={s.milvus_alias}")


def _reset_connect_cache() -> None:
    _connect.cache_clear()


def ensure_collections() -> Dict[str, bool]:
    """幂等建集合：存在则跳过，返回 {collection_name: created_now}"""
    try:
        _connect()
    except Exception:
        _reset_connect_cache()
        raise
    dense_dim = _default_dense_dim()
    result: Dict[str, bool] = {}

    # --- kb_item_names ---
    if not utility.has_collection(COLL_ITEM_NAMES):
        fields = [
            FieldSchema(name="pk", dtype=DataType.VARCHAR, is_primary=True, max_length=128),
            FieldSchema(name="item_name", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="file_title", dtype=DataType.VARCHAR, max_length=512, default_value=""),
            FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=64, default_value=""),
            FieldSchema(name="chunk_count", dtype=DataType.INT32, default_value=0),
            FieldSchema(name="summary", dtype=DataType.VARCHAR, max_length=2000, default_value=""),
            FieldSchema(name=VECTOR_FIELD, dtype=DataType.FLOAT_VECTOR, dim=dense_dim),
            FieldSchema(name="created_at", dtype=DataType.INT64, default_value=0),
        ]
        schema = CollectionSchema(fields, description="知识库文档索引（按 item_name 粒度）")
        col = Collection(COLL_ITEM_NAMES, schema)
        col.create_index(VECTOR_FIELD, _auto_index(dense_dim))
        col.load()
        logger.info(f"[Milvus] 创建集合 {COLL_ITEM_NAMES} (dim={dense_dim})")
        result[COLL_ITEM_NAMES] = True
    else:
        result[COLL_ITEM_NAMES] = False

    # --- kb_chunks ---
    if not utility.has_collection(COLL_CHUNKS):
        fields = [
            FieldSchema(name="pk", dtype=DataType.VARCHAR, is_primary=True, max_length=256),
            FieldSchema(name="item_pk", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="item_name", dtype=DataType.VARCHAR, max_length=256, default_value=""),
            FieldSchema(name="file_title", dtype=DataType.VARCHAR, max_length=512, default_value=""),
            FieldSchema(name="title_path", dtype=DataType.VARCHAR, max_length=1024, default_value=""),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65_535),
            FieldSchema(name="chunk_index", dtype=DataType.INT32, default_value=0),
            FieldSchema(name=VECTOR_FIELD, dtype=DataType.FLOAT_VECTOR, dim=dense_dim),
            FieldSchema(name="created_at", dtype=DataType.INT64, default_value=0),
        ]
        schema = CollectionSchema(fields, description="知识库段落索引（chunk 粒度）")
        col = Collection(COLL_CHUNKS, schema)
        col.create_index(VECTOR_FIELD, _auto_index(dense_dim))
        col.load()
        logger.info(f"[Milvus] 创建集合 {COLL_CHUNKS} (dim={dense_dim})")
        result[COLL_CHUNKS] = True
    else:
        result[COLL_CHUNKS] = False

    return result


def _auto_index(dim: int) -> Dict[str, Any]:
    """小数据量用 IVF_FLAT，大规模换 HNSW；Milvus 2.x 对 IVF_FLAT 的参数约束更宽松"""
    return {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": max(64, min(1024, dim))},
    }


def upsert_item_names(rows: List[Dict[str, Any]]) -> int:
    """按 pk upsert（先删后插）。"""
    _connect()
    col = Collection(COLL_ITEM_NAMES)
    pks = [r["pk"] for r in rows]
    col.delete(expr=f"pk in {_quote_list(pks)}")
    col.insert(rows)
    col.flush()
    logger.info(f"[Milvus] {COLL_ITEM_NAMES} upsert {len(rows)} rows")
    return len(rows)


def upsert_chunks(rows: List[Dict[str, Any]]) -> int:
    _connect()
    col = Collection(COLL_CHUNKS)
    pks = [r["pk"] for r in rows]
    col.delete(expr=f"pk in {_quote_list(pks)}")
    col.insert(rows)
    col.flush()
    logger.info(f"[Milvus] {COLL_CHUNKS} upsert {len(rows)} rows")
    return len(rows)


def hybrid_search_chunks(
    query_vector: Any,
    *,
    top_k: int = 30,
    item_name_filter: Optional[str] = None,
    item_pk_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    混合检索：稠密向量 cosine 相似度 TopK，可选按 item_name / item_pk 过滤。
    返回 list[dict]，字段：pk / item_pk / item_name / file_title / title_path / content / score / source
    """
    _connect()
    col = Collection(COLL_CHUNKS)
    expr_parts: List[str] = []
    if item_name_filter:
        expr_parts.append(f'item_name == "{_escape(item_name_filter)}"')
    if item_pk_filter:
        expr_parts.append(f'item_pk == "{_escape(item_pk_filter)}"')
    expr = " && ".join(expr_parts) if expr_parts else None

    res = col.search(
        data=[query_vector],
        anns_field=VECTOR_FIELD,
        param={"metric_type": "COSINE", "params": {"nprobe": 32}},
        limit=top_k,
        expr=expr,
        output_fields=[
            "pk", "item_pk", "item_name", "file_title", "title_path", "content",
        ],
    )
    out: List[Dict[str, Any]] = []
    for hits in res:
        for h in hits:
            entity = h.entity
            out.append({
                "pk": entity.get("pk"),
                "item_pk": entity.get("item_pk"),
                "item_name": entity.get("item_name"),
                "file_title": entity.get("file_title"),
                "title_path": entity.get("title_path"),
                "content": entity.get("content"),
                "score": float(h.distance),  # COSINE 越大越相似
                "source": f"{entity.get('file_title') or ''}#"
                          f"{entity.get('title_path') or ''}",
            })
    logger.info(
        f"[Milvus] search {COLL_CHUNKS} top_k={top_k} "
        f"filter=({expr}) → hit={len(out)} top_score={out[0]['score'] if out else None}"
    )
    return out


def search_item_names(query_vector: Any, *, top_k: int = 5) -> List[Dict[str, Any]]:
    _connect()
    col = Collection(COLL_ITEM_NAMES)
    res = col.search(
        data=[query_vector],
        anns_field=VECTOR_FIELD,
        param={"metric_type": "COSINE", "params": {"nprobe": 32}},
        limit=top_k,
        output_fields=["pk", "item_name", "file_title", "category", "chunk_count", "summary"],
    )
    out: List[Dict[str, Any]] = []
    for hits in res:
        for h in hits:
            e = h.entity
            out.append({
                "pk": e.get("pk"),
                "item_name": e.get("item_name"),
                "file_title": e.get("file_title"),
                "category": e.get("category"),
                "chunk_count": e.get("chunk_count"),
                "summary": e.get("summary"),
                "score": float(h.distance),
            })
    return out


def delete_by_item_pk(item_pk: str) -> None:
    """联动删除：文档级 + 段落级"""
    _connect()
    if utility.has_collection(COLL_CHUNKS):
        Collection(COLL_CHUNKS).delete(expr=f'item_pk == "{_escape(item_pk)}"')
    if utility.has_collection(COLL_ITEM_NAMES):
        Collection(COLL_ITEM_NAMES).delete(expr=f'pk == "{_escape(item_pk)}"')
    logger.info(f"[Milvus] deleted item_pk={item_pk}")


def stats() -> Dict[str, int]:
    _connect()
    ret: Dict[str, int] = {}
    for name in (COLL_ITEM_NAMES, COLL_CHUNKS):
        if utility.has_collection(name):
            ret[name] = Collection(name).num_entities
        else:
            ret[name] = 0
    return ret


# ---------- 小工具 ----------
def _quote_list(vs: List[str]) -> str:
    return "[" + ", ".join(f'"{_escape(v)}"' for v in vs) + "]"


def _escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


__all__ = [
    "COLL_ITEM_NAMES",
    "COLL_CHUNKS",
    "ensure_collections",
    "upsert_item_names",
    "upsert_chunks",
    "hybrid_search_chunks",
    "search_item_names",
    "delete_by_item_pk",
    "stats",
]
