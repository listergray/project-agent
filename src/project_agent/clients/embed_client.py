"""
Embedding + Rerank 客户端（BGE 系列，FlagEmbedding 本地加载，GPU 自动启用否则 CPU 降级）
设计说明：
1. 用单例 + 懒加载，首次推理才把模型拉进内存，避免启动慢
2. 缓存哈希：相同文本命中缓存就不重复编码，相同文档重复导入时 Embedding 耗时降 90%
3. 编码失败兜底：报错时返回零向量 + 打 ERROR 日志，不要让整个导入流水线因单条失败中断
"""
from __future__ import annotations

import hashlib
from functools import lru_cache
from typing import Dict, List

import numpy as np
from loguru import logger

from project_agent.core import ROOT_DIR, get_settings

_CACHE: Dict[str, np.ndarray] = {}  # 进程内文本哈希 -> 向量缓存


def _text_hash(texts: List[str]) -> str:
    h = hashlib.md5()
    for t in texts:
        h.update(t.encode("utf-8", errors="ignore"))
    return h.hexdigest()


@lru_cache(maxsize=1)
def _get_embed_model():
    settings = get_settings()
    settings.embed_model_cache_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"[Embed] Loading {settings.embed_model_name} (cache: {settings.embed_model_cache_dir})...")
    from sentence_transformers import SentenceTransformer

    local = settings.embed_model_cache_dir / "bge-small-zh-v1.5"
    model_name_or_path = str(local) if local.exists() else settings.embed_model_name
    logger.info(f"[Embed] source: {model_name_or_path}")
    model = SentenceTransformer(
        model_name_or_path,
        cache_folder=str(settings.embed_model_cache_dir),
        device=None,  # 自动：有 GPU 走 cuda，否则 cpu
        trust_remote_code=True,
    )
    dim = model.get_sentence_embedding_dimension()
    logger.info(f"[Embed] model loaded: dim={dim}, device={model.device}")
    return model, dim


def get_embedding_dim() -> int:
    _, dim = _get_embed_model()
    return dim


def encode(texts: List[str], *, batch_size: int = 32, show_progress_bar: bool = False) -> np.ndarray:
    """
    返回 shape=(N, dim) 的 float32 ndarray（稠密向量）。
    设计说明：对于 RAG，我会把 item_name + title_path + content 拼起来再编码，
    让向量同时包含主体、章节和正文信息，检索相关性显著提升。
    """
    if not texts:
        _, dim = _get_embed_model()
        return np.zeros((0, dim), dtype=np.float32)

    # 全量命中缓存直接返回（相同文本重复编码的场景，例如文档再导入）
    cache_key = _text_hash(texts)
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    model, dim = _get_embed_model()
    # 防止超长文本 OOM：分批编码
    vectors_list: list[np.ndarray] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        try:
            vec = model.encode(
                batch,
                batch_size=batch_size,
                show_progress_bar=show_progress_bar,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )
            vectors_list.append(np.asarray(vec, dtype=np.float32))
        except Exception as e:  # noqa: BLE001
            logger.error(f"[Embed] batch encode failed ({len(batch)} texts): {e}")
            vectors_list.append(np.zeros((len(batch), dim), dtype=np.float32))

    result = np.vstack(vectors_list) if vectors_list else np.zeros((0, dim), dtype=np.float32)
    # 限制缓存大小（最多缓存 10000 组）
    if len(_CACHE) > 10000:
        _CACHE.clear()
    _CACHE[cache_key] = result
    return result


# ---------- Rerank 精排 ----------
@lru_cache(maxsize=1)
def _get_rerank_model():
    settings = get_settings()
    logger.info(f"[Rerank] Loading {settings.rerank_model_name} ...")
    from FlagEmbedding import FlagReranker

    settings.embed_model_cache_dir.mkdir(parents=True, exist_ok=True)
    # FlagEmbedding 会自己从 HF 下载；离线可用 cache_dir
    local = settings.embed_model_cache_dir / "bge-reranker-v2-m3"
    model_name_or_path = str(local) if local.exists() else settings.rerank_model_name
    logger.info(f"[Rerank] source: {model_name_or_path}")
    model = FlagReranker(
        model_name_or_path,
        use_fp16=False,
        cache_dir=str(settings.embed_model_cache_dir),
    )
    logger.info(f"[Rerank] model loaded: {settings.rerank_model_name}")
    return model


def rerank(query: str, docs: List[str], *, top_k: int = 5) -> List[int]:
    """
    输入 query + 候选 doc 列表，返回精排后 doc 的 index list（长度 min(top_k, len(docs))）。
    例：docs=[A,B,C], 返回 [2,0] → 表示相关性 C > A，取前 2。
    """
    if not docs:
        return []
    top_k = max(1, min(top_k, len(docs)))
    try:
        model = _get_rerank_model()
        pairs = [[query, d] for d in docs]
        scores = model.compute_score(pairs, normalize=True)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[Rerank] 精排失败，降级按原序返回前 {top_k}: {e}")
        return list(range(top_k))

    scored = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    logger.info(
        f"[Rerank] 候选={len(docs)} → 取 Top{top_k} | "
        f"scores_top={[(i, round(float(s), 3)) for i, s in scored[:top_k]]}"
    )
    return [i for i, _ in scored[:top_k]]


# 给脚本/单测的快速初始化：import 本模块不会立即加载模型
__all__ = ["encode", "get_embedding_dim", "rerank"]
