"""
企业资源知识库 RAG：两个 LangGraph 状态定义
- ImportState（7 节点导入流水线）
- SearchState（7 节点检索 + Function Calling）
设计说明：我用 TypedDict State + StateGraph，每个节点只负责把"自己的字段"写回 State，
便于 replay / checkpoint / 中断恢复，也能让日志一眼看到"哪一步写了多少数据"。
"""
from __future__ import annotations

from typing import Annotated, List, Literal, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


# =====================================================================
# 导入流水线 State（文件 → 解析 → 分块 → item 抽取 → 编码 → 入库）
# =====================================================================
class ImportState(TypedDict, total=False):
    # --- 输入 ---
    file_path: str                          # 用户传入的本地文件路径（.md / .pdf）
    file_url: str                           # 或 MinIO URL（MVP 用 file_path）

    # --- 节点输出 ---
    file_meta: dict                         # N1 解析出的 {name, suffix, size_bytes}
    raw_markdown: str                       # N2/N3 PDF→MD 或 直接读 MD
    chunks: List[dict]                      # N4 语义分块（含 content/title_path/index/file_title）
    item_name: str                          # N5 LLM 抽取的"这本书/手册名"
    item_category: Literal["ASSET", "HR", "FIN", "OTHER"]
    item_summary: str                       # N5 总结：文档一句话摘要（≤100字）
    item_pk: str                            # 文档主键：hash(item_name+file_title)
    encoded_item_vector: List[float]        # N6 文档级向量（给 kb_item_names）
    encoded_chunk_vectors: List[List[float]]# N6 每个 chunk 的稠密向量（与 chunks 等长）
    import_result: dict                     # N7 Milvus 入库结果 {item_rows, chunk_rows, item_pk}

    # --- 通用 ---
    errors: List[str]                       # 任意节点报错
    trace_id: str


# =====================================================================
# 检索流水线 State（用户问 → 改写 → 定位 item → 召回 → 融合 → 精排 → 工具调用 → 回答）
# =====================================================================
class SearchState(TypedDict, total=False):
    # --- 输入 ---
    session_id: str                         # 会话 ID（给 MemorySaver）
    user_query: str                         # 用户原始提问

    # --- 节点输出 ---
    # N1 意图识别 + 改写
    intent: Literal["RETRIEVAL", "TOOL_FIRST", "MIXED"]
    rewritten_query: str                    # HyDE/改写后的标准问题
    target_modules: List[Literal["ASSET", "HR", "FIN"]]  # 识别出的模块

    # N2 定位 item（知识库是哪本手册）
    item_candidates: List[dict]             # search_item_names 返回的候选
    confirmed_item_pk: Optional[str]        # 定位到的 item_pk（可 None = 跨手册搜）
    confirmed_item_name: Optional[str]

    # N3 混合检索（召回 Top30）
    recalled_chunks: List[dict]             # 向量召回结果 {pk, score, content, ...}

    # N4 模糊匹配（召回工具侧的数据，跟 N3 做 RRF 融合）
    fuzzy_candidates: List[dict]            # fuzzy_match_resource 返回的

    # N5 RRF 融合 + 去重 + Top20
    fused_candidates: List[dict]

    # N6 Rerank 精排 → Top5
    reranked_candidates: List[dict]         # 最终喂给 LLM 的上下文

    # N7 生成回答（含 Function Calling）
    messages: Annotated[List[BaseMessage], add_messages]  # ReAct 消息历史
    tool_calls: List[dict]                  # 记录本次对话调用过的工具 [{name,args,result}]
    answer: str                             # 最终 Markdown 回答
    sources: List[str]                      # 来源引用（文档章节）

    # --- 通用 ---
    cost_ms: int
    errors: List[str]
    trace_id: str
