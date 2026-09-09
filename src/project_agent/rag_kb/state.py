"""
企业资源知识库 RAG：两个 LangGraph 状态定义

【技能点 · State 状态管理】
  ✅ TypedDict State：ImportState / SearchState
  ✅ messages + add_messages；session_id 对接 Checkpoint thread_id
  ✅ Self-RAG / multi_queries / faithfulness / HITL 字段
"""
from __future__ import annotations

from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ImportState(TypedDict, total=False):
    file_path: str
    file_url: str
    file_meta: dict
    raw_markdown: str
    chunks: List[dict]
    item_name: str
    item_category: Literal["ASSET", "HR", "FIN", "OTHER"]
    item_summary: str
    item_pk: str
    encoded_item_vector: List[float]
    encoded_chunk_vectors: List[List[float]]
    import_result: dict
    errors: List[str]
    trace_id: str


class SearchState(TypedDict, total=False):
    session_id: str
    user_query: str

    intent: Literal["RETRIEVAL", "TOOL_FIRST", "MIXED"]
    rewritten_query: str
    target_modules: List[Literal["ASSET", "HR", "FIN"]]
    multi_queries: List[str]

    item_candidates: List[dict]
    confirmed_item_pk: Optional[str]
    confirmed_item_name: Optional[str]

    recalled_chunks: List[dict]
    fuzzy_candidates: List[dict]
    fused_candidates: List[dict]
    reranked_candidates: List[dict]
    retrieval_paths: Dict[str, Any]

    self_rag_grade: Dict[str, Any]
    self_rag_need_retry: bool
    self_rag_retries: int
    self_rag_exhausted: bool

    messages: Annotated[List[BaseMessage], add_messages]
    tool_calls: List[dict]
    answer: str
    sources: List[str]

    faithfulness: Dict[str, Any]
    faithfulness_score: float
    need_human_review: bool
    hitl_decision: Dict[str, Any]
    hitl_skipped: bool
    interrupted: bool

    cost_ms: int
    errors: List[str]
    trace_id: str
