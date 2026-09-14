"""
Milvus 向量库客户端（生产向）

【技能点 · 向量库】
  ✅ Milvus：双集合 kb_item_names（文档级）+ kb_chunks（段落级）
  ✅ Embedding 维度对齐 BGE；检索 metric=COSINE（余弦相似度）
  ✅ 向量索引：当前 IVF_FLAT（小数据友好）；大规模可改为 HNSW（见 _auto_index 注释）
  ✅ 元数据过滤：hybrid_search_chunks 支持 item_pk / item_name 的 expr 过滤
  ❌ Chroma：本仓未接（本地轻量开发可用 Chroma 做同接口替身，生产保持 Milvus）

幂等：按 pk 先删后插，避免重复导入膨胀。
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
    # 建集合时不要同步加载 embedding 模型（会卡死 API 启动，导致门户 CSS 不可用）
    # bge-small-zh-v1.5 = 512；真正编码时仍以模型维度为准
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
        # 索引策略：小数据 IVF_FLAT；生产大规模建议改 HNSW（nlist→M/efConstruction）
        # 技能点：熟悉 IVF / HNSW 选型差异（召回率 vs 构建/查询成本）
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


def delete_by_item_pk(item_pk: str) -> int:
    """联动删除：文档级 + 段落级。返回删除的 chunks 总数（精确值）。

    Milvus 的 num_entities 是段级统计，flush 后不一定立即更新（要走 segment merge），
    所以不依赖 num_entities 差值。改成「先 query 出所有 pk，统计 pk 数，再 delete」。
    """
    _connect()
    deleted_chunks = 0
    if utility.has_collection(COLL_CHUNKS):
        col = Collection(COLL_CHUNKS)
        # 先列出该 item_pk 下的所有 pk（Milvus query 限制 max 16384，足够业务）
        rows = col.query(
            expr=f'item_pk == "{_escape(item_pk)}"',
            output_fields=["pk"],
            limit=16384,
        )
        deleted_chunks = len(rows)
        col.delete(expr=f'item_pk == "{_escape(item_pk)}"')
        col.flush()
    if utility.has_collection(COLL_ITEM_NAMES):
        Collection(COLL_ITEM_NAMES).delete(expr=f'pk == "{_escape(item_pk)}"')
        Collection(COLL_ITEM_NAMES).flush()
    logger.info(f"[Milvus] deleted item_pk={item_pk} chunks_deleted={deleted_chunks}")
    return deleted_chunks


def list_chunks_by_item_pk(item_pk: str, *, max_chars: int = 200) -> List[Dict[str, Any]]:
    """按 item_pk 列所有 chunks（不跑向量检索，纯 expr 查全）。前端预览用。"""
    _connect()
    col = Collection(COLL_CHUNKS)
    # Milvus query() 必须加载 collection；load() 是幂等的
    col.load()
    res = col.query(
        expr=f'item_pk == "{_escape(item_pk)}"',
        output_fields=["pk", "item_pk", "item_name", "file_title", "title_path", "content", "chunk_index"],
        limit=16384,
    )
    out: List[Dict[str, Any]] = []
    for r in res:
        c = r.get("content") or ""
        out.append({
            "pk": r.get("pk"),
            "item_pk": r.get("item_pk"),
            "item_name": r.get("item_name"),
            "file_title": r.get("file_title"),
            "title_path": r.get("title_path"),
            "chunk_index": r.get("chunk_index"),
            "content_preview": c[:max_chars] + ("…" if len(c) > max_chars else ""),
            "char_count": len(c),
        })
    out.sort(key=lambda x: x.get("chunk_index", 0))
    return out


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
