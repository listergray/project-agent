"""
LLM 客户端统一封装（LangChain ChatOpenAI 兼容协议，支持 DeepSeek / Qwen / 通义 / 硅基流动）
设计说明：
1. 用单例缓存 ChatOpenAI 实例，避免每个节点重复构造 + 重复加载连接池
2. 统一超时 + 指数退避重试 2 次 + Token 消耗日志
3. 非流式 / 流式接口统一封装，上层业务不用区分底层模型差异
"""
from __future__ import annotations

import time
from functools import lru_cache
from typing import AsyncIterator, List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from loguru import logger

from project_agent.core import get_settings, get_trace_id


@lru_cache(maxsize=1)
def _get_llm() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        timeout=settings.llm_timeout,
        max_retries=0,  # 我们自己做重试 + 打点，更可控
        streaming=False,
    )


async def async_achain(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float | None = None,
    json_mode: bool = False,
    retry: int = 2,
) -> str:
    """统一非流式调用。返回纯字符串。json_mode=True 时用 model_kwargs 约束返回 JSON。"""
    settings = get_settings()
    msgs: List[BaseMessage] = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    llm = _get_llm()
    if temperature is not None:
        llm = llm.bind(temperature=temperature)
    if json_mode:
        llm = llm.bind(response_format={"type": "json_object"})

    last_err: Exception | None = None
    for attempt in range(1, retry + 2):  # 最多 retry+1 次
        t0 = time.perf_counter()
        try:
            resp: AIMessage = await llm.ainvoke(msgs)
            content = resp.content or ""
            # Token 计量（DeepSeek/Qwen 都会返回 usage_metadata）
            usage = getattr(resp, "usage_metadata", None) or {}
            cost = _estimate_cost(usage)
            logger.info(
                f"[LLM] ok | trace={get_trace_id()} | attempt={attempt} | "
                f"tokens={usage} | cost≈${cost:.4f} | elapsed={(time.perf_counter()-t0)*1000:.0f}ms"
            )
            return content if isinstance(content, str) else str(content)
        except Exception as e:  # noqa: BLE001
            last_err = e
            logger.warning(
                f"[LLM] fail | trace={get_trace_id()} | attempt={attempt} | "
                f"err={type(e).__name__}: {str(e)[:120]} | elapsed={(time.perf_counter()-t0)*1000:.0f}ms"
            )
            if attempt <= retry:
                await _sleep_backoff(attempt)
    assert last_err is not None
    raise RuntimeError(f"LLM 调用失败 {retry+1} 次: {last_err}") from last_err


def achain(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float | None = None,
    json_mode: bool = False,
    retry: int = 2,
) -> str:
    """同步 LLM 调用（LangGraph 同步节点 / CLI 用）。"""
    import asyncio
    import concurrent.futures

    coro = async_achain(
        system_prompt,
        user_prompt,
        temperature=temperature,
        json_mode=json_mode,
        retry=retry,
    )
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


async def astream(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float | None = None,
) -> AsyncIterator[str]:
    """SSE 流式调用。按 token 迭代产出字符串。"""
    llm = _get_llm()
    if temperature is not None:
        llm = llm.bind(temperature=temperature)
    msgs: List[BaseMessage] = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    stream = llm.astream(msgs)
    full: list[str] = []
    async for chunk in stream:
        txt = getattr(chunk, "content", None)
        if isinstance(txt, str) and txt:
            full.append(txt)
            yield txt
    logger.info(f"[LLM] stream done | trace={get_trace_id()} | total_chars={len(''.join(full))}")


# ---------- 内部辅助 ----------

async def _sleep_backoff(attempt: int) -> None:
    import asyncio

    # 指数退避：1s / 2s
    await asyncio.sleep(min(2 ** (attempt - 1), 2))


def _estimate_cost(usage: dict) -> float:
    """粗略成本估算（DeepSeek 价格量级，用于日志观测，不是精确计费）。"""
    if not usage:
        return 0.0
    in_tokens = usage.get("input_tokens", 0) or 0
    out_tokens = usage.get("output_tokens", 0) or 0
    # DeepSeek-V3: $0.14 / 1M in, $0.28 / 1M out
    return (in_tokens * 0.14 + out_tokens * 0.28) / 1_000_000
