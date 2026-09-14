"""
节点内 LCEL 短链封装（图编排仍用 LangGraph）

【技能点 · LCEL】
  ✅ ChatPromptTemplate | ChatOpenAI | StrOutputParser
  ✅ 可选 JSON 模式；失败时由调用方兜底
"""
from __future__ import annotations

import json
from typing import Any, Dict, Optional, Type, TypeVar

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger
from pydantic import BaseModel

from project_agent.clients.llm_client import _get_llm
from project_agent.utils import load

T = TypeVar("T", bound=BaseModel)


def lcel_text_chain(
    system_prompt: str,
    *,
    temperature: float | None = 0,
    json_mode: bool = False,
):
    """构建 LCEL：system+user → LLM → 字符串。"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "{system}"),
        ("human", "{user}"),
    ])
    llm = _get_llm()
    if temperature is not None:
        llm = llm.bind(temperature=temperature)
    if json_mode:
        llm = llm.bind(response_format={"type": "json_object"})
    return prompt | llm | StrOutputParser()


def lcel_invoke(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float | None = 0,
    json_mode: bool = False,
) -> str:
    chain = lcel_text_chain(system_prompt, temperature=temperature, json_mode=json_mode)
    return chain.invoke({"system": system_prompt, "user": user_prompt})


def lcel_json(
    system_prompt: str,
    user_prompt: str,
    *,
    model: Optional[Type[T]] = None,
    temperature: float | None = 0,
) -> Dict[str, Any] | T:
    """LCEL JSON 调用；可选 Pydantic 校验。"""
    raw = lcel_invoke(system_prompt, user_prompt, temperature=temperature, json_mode=True)
    obj = json.loads(raw if isinstance(raw, str) else str(raw))
    if model is not None:
        return model.model_validate(obj)
    return obj


def lcel_from_prompt_file(
    prompt_name: str,
    user_prompt: str,
    *,
    fallback_system: str = "",
    json_mode: bool = True,
    temperature: float | None = 0,
) -> str:
    sys = load(prompt_name) or fallback_system
    if not sys:
        raise ValueError(f"prompt missing: {prompt_name}")
    try:
        return lcel_invoke(sys, user_prompt, temperature=temperature, json_mode=json_mode)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[LCEL] {prompt_name} 失败: {e}")
        raise
