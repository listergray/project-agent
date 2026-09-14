"""
全链路日志 + TraceID 注入
设计说明：每个 LangGraph 节点入口/出口都打日志（耗时+状态大小+错误），带统一 TraceID，
排查"为什么回答不对"能直接定位到是召回问题还是生成问题。
"""
from __future__ import annotations

import sys
import uuid
from contextvars import ContextVar
from typing import Optional

from loguru import logger

from .config import get_settings

_TRACE_ID: ContextVar[str] = ContextVar("trace_id", default="no-trace")


def new_trace_id() -> str:
    tid = uuid.uuid4().hex[:16]
    _TRACE_ID.set(tid)
    return tid


def get_trace_id() -> str:
    return _TRACE_ID.get()


def set_trace_id(tid: Optional[str]) -> None:
    _TRACE_ID.set(tid or uuid.uuid4().hex[:16])


def _trace_id_formatter(record: dict) -> str:
    record["extra"]["trace_id"] = get_trace_id()
    return (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <7}</level> | "
        "<cyan>{extra[trace_id]}</cyan> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>\n"
    )


def setup_logger() -> None:
    settings = get_settings()
    logger.remove()

    # 控制台：彩色 + TraceID
    logger.add(
        sys.stdout,
        level=settings.log_level.upper(),
        format=_trace_id_formatter,
        colorize=True,
        backtrace=False,
        diagnose=False,
    )

    # 文件：按天切割，保留 14 天
    log_dir = settings.embed_model_cache_dir.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    logger.add(
        log_dir / "app_{time:YYYYMMDD}.log",
        level="DEBUG",
        rotation="00:00",
        retention="14 days",
        encoding="utf-8",
        enqueue=True,
        backtrace=True,
        diagnose=False,
        format=_trace_id_formatter,
    )


# 项目首次 import core.logger 即自动初始化
setup_logger()
