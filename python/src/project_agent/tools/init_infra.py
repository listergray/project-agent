"""
一键初始化中间件资源（`docker/up.ps1` 调用，也能手动 `python -m project_agent.tools.init_infra`）：
  1. 确保 Milvus 两个集合存在（幂等）
  2. 确保 MinIO 的知识库 bucket 存在
  3. 打印当前 stats
设计说明：把"环境初始化"收敛成一条命令，不会把评审人卡在"先手动 docker exec 建 bucket / create collection…"。
"""
from __future__ import annotations

import sys

from loguru import logger

from project_agent.clients import ensure_collections, stats


def _ensure_minio_bucket() -> None:
    try:
        from minio import Minio
        from project_agent.core import get_settings
        s = get_settings()
        client = Minio(s.minio_endpoint,
                       access_key=s.minio_access_key,
                       secret_key=s.minio_secret_key,
                       secure=s.minio_secure)
        if not client.bucket_exists(s.minio_bucket_kb):
            client.make_bucket(s.minio_bucket_kb)
            logger.info(f"[MinIO] 创建 bucket {s.minio_bucket_kb!r}")
        else:
            logger.info(f"[MinIO] bucket {s.minio_bucket_kb!r} 已存在")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[MinIO] 初始化跳过（可能 SDK 未装 / MinIO 还没完全就绪）：{e}")


def main() -> None:
    try:
        created = ensure_collections()
    except Exception as e:  # noqa: BLE001
        logger.error(f"Milvus ensure_collections 失败: {e}")
        sys.exit(2)
    logger.info(f"[Milvus] 集合情况 (created_now: True=刚创建, False=已存在): {created}")
    logger.info(f"[Milvus] 当前 entities stats: {stats()}")

    _ensure_minio_bucket()
    logger.info("✅ init_infra 完成")


if __name__ == "__main__":
    main()
