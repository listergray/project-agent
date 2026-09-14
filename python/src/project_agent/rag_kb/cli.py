"""
RAG 知识库 命令行入口（两条命令）：
  1. rag-import  → 一键导入 data/samples/ 下的样例文档（7 节点流水线跑一遍）
  2. rag-chat    → 交互式问答（7 节点检索 + 3 个 Function Calling）

演示脚本建议（5 分钟版）：
  step1: rag-import  → 等显示 "chunks_upserted=xxx success"
  step2: rag-chat    → 依次问 4 个问题：
    Q1 纯检索：「企业固定资产怎么入库？」（考向量召回+Rerank）
    Q2 纯查库：「FS-2024-0876 现在有多少库存？单价多少？」（考 query_resource_by_code）
    Q3 模糊匹配：「帮我查一下陈昊的工号和岗位」（考 fuzzy_match_resource）
    Q4 混合+导出：「给我导出所有联想/戴尔/华为设备的库存清单」（考 fuzzy + export_to_excel）
  每个问题结束屏幕会显示：工具调用次数 + 来源引用 + 最终 Markdown 回答。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loguru import logger

from project_agent.core import ROOT_DIR
from project_agent.clients import ensure_collections, stats
from project_agent.utils.cli_console import ensure_utf8_stdio

from .graphs import import_sample_dir, run_search


PRESET_QUERIES = [
    ("纯检索类（考向量召回 + Rerank）", "固定资产入库的完整流程是什么？"),
    ("纯查库类（考 query_resource_by_code 精确编码）", "FS-2024-0876 现在有多少库存？单价和总价是多少？"),
    ("模糊匹配类（考 fuzzy_match_resource + 同义词）", "帮我查一下员工陈昊的工号、部门和岗位，存货/库存相关的同义词有哪些？"),
    ("混合+导出类（考多轮工具 + export_to_excel）", "给我导出一份公司所有工作站、笔记本、服务器的库存清单到表格。"),
    ("财务类（跨模块识别）", "FIN-INV-2024-001 是什么单据？金额多少？状态是什么？"),
]


def cli_import() -> None:
    ensure_utf8_stdio()
    parser = argparse.ArgumentParser(description="RAG 知识库导入（7 节点 LangGraph）")
    parser.add_argument("--file", "-f", help="只导入单个文件（md/txt/pdf）", default=None)
    parser.add_argument("--dir", "-d", help="样例目录（默认 data/samples）",
                        default=str(ROOT_DIR / "data" / "samples"))
    args = parser.parse_args()

    logger.info("=" * 64)
    logger.info("RAG 知识库 导入：Step1 建立 Milvus 集合（幂等）")
    created = ensure_collections()
    logger.info(f"Milvus 集合创建情况: {created} | 当前 stats: {stats()}")

    logger.info("=" * 64)
    logger.info("RAG 知识库 导入：Step2 执行导入流水线（7 节点线性图）")
    if args.file:
        from .graphs import run_import
        results = [run_import(args.file)]
    else:
        results = import_sample_dir(Path(args.dir))

    logger.info("=" * 64)
    ok = sum(1 for r in results if not r.get("errors"))
    logger.info(f"导入完成：总 {len(results)}，成功 {ok}，失败 {len(results)-ok} | stats={stats()}")
    for r in results:
        if r.get("errors"):
            logger.error(f"  ❌ {(r.get('file_meta') or {}).get('name')}: {r['errors']}")
        else:
            ir = r.get("import_result") or {}
            logger.info(
                f"  ✅ {ir.get('item_name','?')} | pk={ir.get('item_pk')} "
                f"chunks={ir.get('chunks_upserted')} cost={ir.get('cost_ms')}ms"
            )


def _print_hr(char: str = "=") -> None:
    print(char * 72)


def cli_chat() -> None:
    ensure_utf8_stdio()
    parser = argparse.ArgumentParser(description="RAG 知识库交互问答（7 节点检索 + 3 个 Function Calling）")
    parser.add_argument("--once", "-q", help="只问一次（非交互），适用于脚本化演示", default=None)
    parser.add_argument("--presets", action="store_true", help="依次跑 5 个预设演示问题然后退出")
    args = parser.parse_args()

    ensure_collections()
    kb_stats = stats()
    _print_hr("=")
    print(f"  📚 RAG 知识库 RAG+Agent 控制台 | 当前 Milvus 统计: {kb_stats}")
    print(f"  🔧 可用工具：query_resource_by_code / fuzzy_match_resource / export_to_excel")
    print(f"  📝 输入 q 退出；空行打印预设问题列表；或直接输入你的问题。")
    _print_hr("=")

    def ask_once(q: str, *, tag: str = "") -> None:
        if tag:
            _print_hr("-")
            print(f"\n🗣️  [{tag}] 用户问：{q}")
        else:
            print(f"\n🗣️  你问：{q}")
        res = run_search(q)
        if res.get("errors"):
            print(f"❌ 出错：{res['errors']}")
            return
        # 工具调用记录
        tcs = res.get("tool_calls") or []
        if tcs:
            print(f"🛠️  工具调用记录（{len(tcs)} 轮）：")
            for t in tcs:
                r_short = ""
                if isinstance(t["result"], dict):
                    # 只取前 4 个字段精简展示
                    r_short = ", ".join(f"{k}={str(v)[:60]}" for k, v in list(t["result"].items())[:4])
                else:
                    r_short = str(t["result"])[:120]
                print(f"  Step{t['step']} 🔸 {t['name']}({t['args']}) → {r_short}")
        # 最终回答
        ans = res.get("answer") or "（空回答）"
        print("\n🤖 回答：")
        print(ans)
        _print_hr("-")

    if args.once:
        ask_once(args.once)
        return

    if args.presets:
        for tag, q in PRESET_QUERIES:
            ask_once(q, tag=tag)
        print("\n✅ 5 个预设问题跑完。")
        return

    # 交互模式
    while True:
        try:
            q = input("\n你 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 再见")
            return
        if not q:
            print("💡 预设问题（输入编号直接问）：")
            for i, (tag, question) in enumerate(PRESET_QUERIES, 1):
                print(f"  [{i}] {tag} → {question}")
            continue
        if q.lower() in {"q", "quit", "exit", "bye"}:
            print("👋 再见")
            return
        # 支持输入编号直接问预设
        if q.isdigit() and 1 <= int(q) <= len(PRESET_QUERIES):
            tag, question = PRESET_QUERIES[int(q) - 1]
            ask_once(question, tag=tag)
            continue
        ask_once(q)


__all__ = ["cli_import", "cli_chat", "PRESET_QUERIES"]
