"""
代码助手 LangGraph：需求→代码→审查→单测→文档→落盘（5+1）

【技能点 · AI 开发辅助落地】
  ✅ 任务拆解（N1）→ AI 生成 Java/XML（N2）→ 人工可审的规则审查（N3）
     → 单测生成（N4）→ 文档（N5）→ 小步落盘验证（N6）
  ✅ 产物为 Spring Boot 样板，体现「Python AI 编排生成 Java 微服务脚手架」
  📘 协作模式对齐 Cursor/Trae：脚手架与样板由 Agent 生成，架构与质量靠审查节点+人工把关
  ⚠️ 本图未接 Checkpoint/HITL interrupt；并发/事务/边界在生成的 Java 注释与审查规则中强调
"""
from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

from project_agent.core import ROOT_DIR, new_trace_id

from project_agent.copilot.nodes import (
    n1_requirement_analyze,
    n2_code_gen,
    n3_code_review_refactor,
    n4_unit_test_gen,
    n5_doc_gen,
)
from project_agent.copilot.state import DEFAULT_REQUIREMENT, CopilotState


def _write_all(state: Dict[str, Any]) -> Dict[str, Any]:
    """N6 落盘：把所有代码 + 文档写入 output/copilot_<timestamp>/ 目录。"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = ROOT_DIR / "output" / f"copilot_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    merged: Dict[str, str] = {}
    merged.update(state.get("reviewed_files") or state.get("generated_files") or {})
    merged.update(state.get("test_files") or {})
    if state.get("api_doc_md"):
        merged["README-接口文档.md"] = state["api_doc_md"]
    # 设计文档也落地（便于演示展示 N1 产出）
    if state.get("design_doc"):
        merged["01-设计文档-N1输出.md"] = state["design_doc"]
    if state.get("review_report"):
        merged["02-审查报告-N3输出.json"] = json.dumps(state["review_report"],
                                                         ensure_ascii=False, indent=2)

    for rel_path, content in merged.items():
        target = (out_dir / rel_path).resolve()
        # 防路径穿越：必须在 out_dir 内
        if not str(target).startswith(str(out_dir.resolve())):
            logger.warning(f"[代码助手 N6] 跳过非法路径 {rel_path}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content or "", encoding="utf-8")
        count += 1

    steps = list(state.get("steps_done") or []) + ["N6-WRITE"]
    logger.info(f"[代码助手 N6] 落盘完成：共 {count} 个文件 → {out_dir}")
    return {"output_dir": str(out_dir), "steps_done": steps}


def _build_graph() -> CompiledStateGraph:
    builder = StateGraph(CopilotState)
    builder.add_node("n1_requirement_analyze", n1_requirement_analyze)
    builder.add_node("n2_code_gen", n2_code_gen)
    builder.add_node("n3_code_review_refactor", n3_code_review_refactor)
    builder.add_node("n4_unit_test_gen", n4_unit_test_gen)
    builder.add_node("n5_doc_gen", n5_doc_gen)
    builder.add_node("n6_write_all", _write_all)

    builder.add_edge(START, "n1_requirement_analyze")
    order = [
        "n1_requirement_analyze",
        "n2_code_gen",
        "n3_code_review_refactor",
        "n4_unit_test_gen",
        "n5_doc_gen",
        "n6_write_all",
    ]
    for i, cur in enumerate(order):
        if i == len(order) - 1:
            builder.add_edge(cur, END)
        else:
            nxt = order[i + 1]
            # errors 只做 WARN 级，不短路，保证 5 节点必跑完（演示要看到全链路产物）
            builder.add_edge(cur, nxt)
    return builder.compile()


_GRAPH: CompiledStateGraph | None = None


def get_graph() -> CompiledStateGraph:
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = _build_graph()
    return _GRAPH


def run_copilot(*, requirement_doc: str | None = None, thread_id: str | None = None) -> Dict[str, Any]:
    """
    同步执行 代码助手 5+1 流水线。返回完整最终 State（含 output_dir，打开即可看文件）。
    :param requirement_doc: 不填则用默认需求文档（资产盘点单导入模块）。
    """
    req = requirement_doc or DEFAULT_REQUIREMENT
    graph = get_graph()
    tid = new_trace_id()
    t0 = time.perf_counter()
    initial: CopilotState = {
        "requirement_doc": req,
        "trace_id": tid,
    }
    cfg = {"configurable": {"thread_id": thread_id or f"copilot_{tid}"}}
    result = graph.invoke(initial, config=cfg)
    elapsed = int((time.perf_counter() - t0) * 1000)
    logger.info(
        f"[代码助手] 完成 steps={result.get('steps_done')} "
        f"cost={elapsed}ms output={result.get('output_dir')}"
    )
    result["total_cost_ms"] = elapsed
    return result


__all__ = ["run_copilot", "get_graph", "DEFAULT_REQUIREMENT"]
