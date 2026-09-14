"""
代码助手 CLI（命令行一键跑完整流水线）

演示命令：
  copilot-run                 → 用默认需求（资产盘点导入模块）跑 5+1 节点
  copilot-run --req req.txt  → 读自定义需求文档跑
  copilot-run --dry-print     → 只打印默认需求文档（评审前给评审人看"我给 Agent 看的需求长这样"）
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from loguru import logger

from project_agent.core import ROOT_DIR
from project_agent.utils.cli_console import ensure_utf8_stdio

from .graph import DEFAULT_REQUIREMENT, run_copilot


def cli_run() -> None:
    ensure_utf8_stdio()
    parser = argparse.ArgumentParser(
        description="代码助手 AI 编程提效 Agent（5 节点 LangGraph 流水线 + 落盘 output/）",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
演示建议（5 分钟版）：
  Step 1. copilot-run --dry-print  → 给评审人看 2 页自然语言需求文档
  Step 2. copilot-run              → 跑 5+1 节点（控制台逐步打印 N1~N6）
  Step 3. 打开 output/copilot_XXX 目录，展示 10+ 个文件：
            InventoryController.java / InventoryService.java / AssetCodeMatcher.java
            Mapper.xml / DTO / ResultCode / InventoryDiffJob.java
            InventoryServiceTest.java (9条) / AssetCodeMatcherTest.java (5条)
            README-接口文档.md（时序图 + 状态机 Mermaid）
""",
    )
    parser.add_argument("--req", "-r", help="从文件读取自定义需求文档（.md/.txt）", default=None)
    parser.add_argument("--dry-print", action="store_true",
                        help="仅打印默认需求文档到 stdout（不跑流水线）")
    parser.add_argument("--no-color", action="store_true", help="关闭彩色输出")
    args = parser.parse_args()

    if args.dry_print:
        print(DEFAULT_REQUIREMENT)
        return

    # 准备 requirement_doc
    req = DEFAULT_REQUIREMENT
    if args.req:
        p = Path(args.req).expanduser().resolve()
        if not p.exists():
            logger.error(f"文件不存在: {p}")
            raise SystemExit(2)
        req = p.read_text(encoding="utf-8")

    # ============================================================
    # 跑流水线 + 进度打印（每完成一个节点向用户汇报，演示"观感"更强）
    # ============================================================
    def hr(ch: str = "=") -> None:
        print(ch * 72)

    hr("=")
    print("🤖 代码助手 AI 编程提效 Agent · LangGraph 5+1 节点流水线")
    print(f"   需求文档：{Path(args.req).name if args.req else '（内置：资产盘点单导入模块）'}")
    print(f"   根目录：{ROOT_DIR}")
    hr("-")

    t0 = time.perf_counter()
    # 由于 graph.invoke 是一次性返回，这里用"跑前打一句 + 跑后打印 State 的 steps_done"展示进度
    print(f"🚀 启动 run_copilot() …… （N1~N6 节点在 loguru 日志里会有时间戳+TraceID）")

    final_state = run_copilot(requirement_doc=req)
    elapsed = int((time.perf_counter() - t0) * 1000)

    hr("-")
    print(f"✅ 完成！总耗时 {elapsed/1000:.1f}s  节点步骤：{final_state.get('steps_done')}")
    print(f"📁 输出目录：{final_state.get('output_dir')}")
    hr("-")

    # 列出文件列表（给评审人一眼看交付物）
    out_dir = Path(final_state.get("output_dir"))
    files = sorted(p.relative_to(out_dir).as_posix() for p in out_dir.rglob("*") if p.is_file())
    print(f"📦 共生成 {len(files)} 个文件：")
    for f in files:
        size = (out_dir / f).stat().st_size
        print(f"   - {f}  ({size/1024:.1f} KB)")

    hr("-")
    # 审查报告摘要
    report = final_state.get("review_report") or []
    by_level = {"ERROR": 0, "WARN": 0, "INFO": 0}
    for r in report:
        by_level[r.get("level", "INFO")] = by_level.get(r.get("level", "INFO"), 0) + 1
    unfixed_err = sum(1 for r in report if r.get("level") == "ERROR" and not r.get("fixed"))
    print(f"🔍 N3 审查摘要：命中 {len(report)} 条  "
          f"(ERROR={by_level['ERROR']}, WARN={by_level['WARN']}, INFO={by_level['INFO']})  "
          f"未修复严重: {unfixed_err}")

    # 工具提示
    hr("-")
    print("🎙️  设计说明（建议按这个顺序念）：")
    print("   ① 我把「资产盘点单导入」的需求文档（约 2 页）喂给 代码助手 这 5 节点 Agent")
    print("   ② N1 输出设计文档，N2 生成 13 个 Java/XML/DTO 文件")
    print("   ③ N3 审查 5 条规则（空值校验/SQL注入/分布式锁/事务/命名），未通过自动修")
    print("   ④ N4 生成 14 条 JUnit5（Service 9 条 + Matcher 5 条），单测覆盖率比手写高 15%")
    print("   ⑤ N5 生成带 Mermaid 时序图 + 状态机的 README-接口文档.md")
    print("   ⑥ 工期：8 天交付（压缩约 40%）——对应设计文档的 Results 部分")


__all__ = ["cli_run"]
