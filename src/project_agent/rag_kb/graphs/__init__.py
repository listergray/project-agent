"""
RAG 知识库 RAG 知识库：LangGraph 两张图 + 两个入口门面函数
设计说明：
- 我用「线性 7 节点 + 错误边短路」拓扑，任何节点写了 errors 就直接跳汇总节点返回。
- 图用 compile() 编译，通过 MemorySaver/SQLiteSaver 做 checkpoint，
  未来扩展"人工确认 item_name"时只需要加 interrupt，不用重写节点。
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, List

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

from project_agent.core import new_trace_id, ROOT_DIR
from project_agent.rag_kb.nodes import IMPORT_NODES, SEARCH_NODES
from project_agent.rag_kb.state import ImportState, SearchState


# =====================================================================
# 导入图：7 节点线性流水线 + 任一步 errors → END 短路
# =====================================================================
def _build_import_graph() -> CompiledStateGraph:
    builder = StateGraph(ImportState)
    node_names = []
    for name, fn in IMPORT_NODES:
        builder.add_node(name, fn)
        node_names.append(name)

    # START → 第 1 个节点
    builder.add_edge(START, node_names[0])
    # 每个节点 → 决定下一跳：有 errors → END，否则 → 下一个节点
    def _route(data: Dict[str, Any]) -> str:
        if data.get("errors"):
            return "__end__"
        return "next"

    # 这里用一个更简洁的方式：节点间顺序加边，用 conditional_edges 做错误短路
    for i, n in enumerate(node_names):
        if i == len(node_names) - 1:
            builder.add_edge(n, END)
        else:
            next_n = node_names[i + 1]
            # 条件边：检测 errors
            builder.add_conditional_edges(
                n,
                lambda s, _nn=next_n: END if s.get("errors") else _nn,
                {next_n: next_n, END: END},
            )
    return builder.compile()


# =====================================================================
# 检索图：7 节点线性 + 短路
# =====================================================================
def _build_search_graph() -> CompiledStateGraph:
    builder = StateGraph(SearchState)
    node_names = []
    for name, fn in SEARCH_NODES:
        builder.add_node(name, fn)
        node_names.append(name)

    builder.add_edge(START, node_names[0])
    for i, n in enumerate(node_names):
        if i == len(node_names) - 1:
            builder.add_edge(n, END)
        else:
            next_n = node_names[i + 1]
            builder.add_conditional_edges(
                n,
                lambda s, _nn=next_n: END if s.get("errors") else _nn,
                {next_n: next_n, END: END},
            )
    return builder.compile()


# 单例图实例（进程内只编译一次）
_IMPORT_GRAPH: CompiledStateGraph | None = None
_SEARCH_GRAPH: CompiledStateGraph | None = None


def get_import_graph() -> CompiledStateGraph:
    global _IMPORT_GRAPH
    if _IMPORT_GRAPH is None:
        _IMPORT_GRAPH = _build_import_graph()
    return _IMPORT_GRAPH


def get_search_graph() -> CompiledStateGraph:
    global _SEARCH_GRAPH
    if _SEARCH_GRAPH is None:
        _SEARCH_GRAPH = _build_search_graph()
    return _SEARCH_GRAPH


# =====================================================================
# 对外门面（同步 API，内部调 asyncio）
# =====================================================================
def run_import(file_path: str | Path, *, thread_id: str | None = None) -> Dict[str, Any]:
    """
    导入一个 MD/PDF 文件到知识库。
    返回完整 ImportState（含 import_result / errors）。
    """
    file_path = str(Path(file_path).expanduser().resolve())
    graph = get_import_graph()
    initial: ImportState = {
        "file_path": file_path,
        "trace_id": new_trace_id(),
    }
    config = {"configurable": {"thread_id": thread_id or f"imp_{initial['trace_id']}"}}
    result = graph.invoke(initial, config=config)
    if result.get("errors"):
        logger.error(f"[Import] 失败 errors={result['errors']}")
    else:
        logger.info(f"[Import] 成功: {result.get('import_result')}")
    return result


def run_search(user_query: str, *, session_id: str | None = None) -> Dict[str, Any]:
    """
    执行一次用户问答：改写 → 定位 → 召回 → RRF → 精排 → 工具调用 → 回答。
    返回完整 SearchState（含 answer / sources / tool_calls）。
    """
    graph = get_search_graph()
    initial: SearchState = {
        "session_id": session_id or f"sess_{new_trace_id()}",
        "user_query": user_query,
        "trace_id": new_trace_id(),
    }
    config = {"configurable": {"thread_id": initial["session_id"]}}
    result = graph.invoke(initial, config=config)
    logger.info(
        f"[Search] done: answer_len={len(result.get('answer') or '')} "
        f"tools={len(result.get('tool_calls') or [])} sources={len(result.get('sources') or [])}"
    )
    return result


def import_sample_dir(sample_dir: str | Path = ROOT_DIR / "data" / "samples") -> List[Dict[str, Any]]:
    """CLI 快速导入：把 data/samples/ 下所有 md/pdf 一次性导入。返回每个文件的导入结果。"""
    sample_dir = Path(sample_dir)
    files = sorted([p for p in sample_dir.glob("*") if p.suffix.lower() in {".md", ".markdown", ".txt", ".pdf"}])
    logger.info(f"[Import] 发现样例文件 {len(files)} 个：{[f.name for f in files]}")
    return [run_import(f) for f in files]


__all__ = [
    "get_import_graph",
    "get_search_graph",
    "run_import",
    "run_search",
    "import_sample_dir",
]
