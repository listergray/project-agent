"""
LLM 客户端统一封装（OpenAI 兼容协议）

【技能点 · LLM 工程化 / 模型接入】
  ✅ 兼容接口：langchain_openai.ChatOpenAI + base_url/api_key/model
     可切换 DeepSeek / 通义千问 / 硅基流动等（改 conf/.env 即可）
  ✅ 超时：settings.llm_timeout；重试：async_achain 指数退避（默认 2 次）
  ✅ 流式：astream；非流式：achain / async_achain；json_mode 约束结构化输出
  ✅ 会话记忆 / 消息窗口裁剪：utils.session_memory（run_search / N7 接入）
  ✅ LangSmith：core.tracing.configure_langsmith（LANGSMITH_* / LANGCHAIN_*）
  ✅ 节点内 LCEL：clients.lcel（多查询 / 忠实度等短链）

单例缓存 ChatOpenAI，避免每个 LangGraph 节点重复建连。
"""
from __future__ import annotations

import time
from functools import lru_cache
from typing import AsyncIterator, List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from loguru import logger

from project_agent.core import configure_langsmith, get_settings, get_trace_id


@lru_cache(maxsize=1)
def _get_llm() -> ChatOpenAI:
    configure_langsmith()
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
    # 强制开启 streaming，避免单例 streaming=False 挡住真流式
    llm = llm.bind(streaming=True)
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


def stream_achain(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float | None = None,
):
    """同步 token 迭代（LangGraph 同步节点 / 自定义 stream writer 用）。"""
    import asyncio
    import concurrent.futures
    import queue as queue_mod

    q: queue_mod.Queue[str | None] = queue_mod.Queue()

    async def _pump() -> None:
        try:
            async for t in astream(system_prompt, user_prompt, temperature=temperature):
                q.put(t)
        finally:
            q.put(None)

    def _runner() -> None:
        asyncio.run(_pump())

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(_runner)
        while True:
            item = q.get()
            if item is None:
                break
            yield item
        fut.result()


def _get_vision_llm() -> ChatOpenAI:
    """多模态模型（立项文档截图理解）。未单独配置时回落到主 LLM。"""
    settings = get_settings()
    return ChatOpenAI(
        base_url=(settings.llm_vision_base_url or settings.llm_base_url),
        api_key=(settings.llm_vision_api_key or settings.llm_api_key),
        model=(settings.llm_vision_model or settings.llm_model),
        temperature=0.1,
        timeout=max(settings.llm_timeout, 90),
        max_retries=0,
        streaming=False,
    )


async def async_vision_achain(prompt: str, image_data_url: str, *, retry: int = 1) -> str:
    """OpenAI 兼容多模态：text + image_url。"""
    msgs: List[BaseMessage] = [
        SystemMessage(
            content="你是文档图片文字提取助手，只输出图中可见文字，不要解释。"
        ),
        HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_data_url}},
            ]
        ),
    ]
    llm = _get_vision_llm()
    last_err: Exception | None = None
    for attempt in range(1, retry + 2):
        t0 = time.perf_counter()
        try:
            resp: AIMessage = await llm.ainvoke(msgs)
            content = resp.content or ""
            logger.info(
                f"[LLM-Vision] ok | trace={get_trace_id()} | attempt={attempt} | "
                f"elapsed={(time.perf_counter()-t0)*1000:.0f}ms | chars={len(str(content))}"
            )
            return content if isinstance(content, str) else str(content)
        except Exception as e:  # noqa: BLE001
            last_err = e
            logger.warning(
                f"[LLM-Vision] fail | attempt={attempt} | err={type(e).__name__}: {str(e)[:160]}"
            )
            if attempt <= retry:
                await _sleep_backoff(attempt)
    assert last_err is not None
    raise RuntimeError(f"Vision LLM 调用失败: {last_err}") from last_err


def vision_achain(prompt: str, image_data_url: str, *, retry: int = 1) -> str:
    """同步多模态调用。"""
    import asyncio
    import concurrent.futures

    coro = async_vision_achain(prompt, image_data_url, retry=retry)
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


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
