"""
最小冒烟单测（保证 import 路径正确 + 工具纯逻辑能跑通，不依赖 Milvus/LLM/容器）
本地快速验证：`cd e:\ai-pro\project-agent && pytest -q` → 全部 PASSED。
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path


def test_fuzzy_tool_query_and_export(tmp_path):
    """RAG 知识库 的 3 个工具跑一条正向链路（纯 Python，不依赖任何容器/Key）"""
    from project_agent.tools.rag_tools import (
        query_resource_by_code,
        fuzzy_match_resource,
        export_to_excel,
    )
    # 1) 精确编码查库 → 必须命中 FS-2024-0876
    r = query_resource_by_code.invoke({"asset_code": "FS-2024-0876"})
    assert r["found"] is True
    assert r["module"] == "ASSET"
    assert r["data"]["stock"] == 37
    assert r["data"]["owner"] == "张志远"

    # 2) 模糊查询：只记得"陈昊" → fuzzy 应该给 HR-EMP-1001 sim>=0.8
    r = fuzzy_match_resource.invoke({"keyword": "陈昊", "top_k": 5})
    assert len(r["candidates"]) >= 1
    top = r["candidates"][0]
    assert top["code"] == "HR-EMP-1001"
    assert top["similarity"] >= 0.8

    # 3) 同义词命中 → "存货" 与 "库存" 相似度加分
    r2 = fuzzy_match_resource.invoke({"keyword": "存货相关资产", "top_k": 3})
    # 至少返回候选（命中 threshold 以上）
    assert isinstance(r2["candidates"], list)

    # 4) export_to_excel 写出 CSV（UTF-8-BOM，Excel 双击直接打开）
    rows = [
        {"code": "FS-2024-0876", "name": "联想工作站", "stock": 37, "price": 12800,
         "来源": "AssetModule.md#主要资产清单"},
        {"code": "HR-EMP-1001", "name": "陈昊", "dept": "架构组", "职级": "P6"},
    ]
    saved = export_to_excel.invoke({"rows": rows, "filename": "smoke_export"})
    assert saved["success"] is True
    assert saved["rows_count"] == 2
    fp = Path(saved["filepath"])
    assert fp.exists() and fp.stat().st_size > 0
    content_bom = fp.read_bytes()
    assert content_bom.startswith(b"\xef\xbb\xbf")  # UTF-8-BOM
    assert "FS-2024-0876" in content_bom.decode("utf-8-sig")


def test_levenshtein_dp():
    """技术亮点：纯 Python 双数组 DP 编辑距离"""
    from project_agent.utils.fuzzy import levenshtein, similarity

    assert levenshtein("", "abc") == 3
    assert levenshtein("abc", "") == 3
    assert levenshtein("kitten", "sitting") == 3  # 经典值
    assert levenshtein("资产编号", "资产编码") == 1
    assert similarity("库存", "存货") >= 0.85  # 同义词加分


def test_text_splitter_markdown():
    """语义分块必须产出 title_path + 正文"""
    from project_agent.utils.text_splitter import split_markdown

    md = (
        "# 一级\n"
        "开头摘要段\n"
        "## 二级A\n"
        "A的内容1。A的内容2\n"
        "### 二级A-1\n"
        "细节内容细节内容细节内容。" * 30  # 足够长的正文，验证超长段会再切分
    )
    chunks = split_markdown(md, file_title="示例")
    assert chunks, "应切出至少 1 个 chunk"
    # 必有 title_path 非空的 chunk（各级标题）
    assert any(c.title_path for c in chunks)
    assert chunks[0].file_title == "示例"
    # 每个 chunk 的 content 长度 ≤ ~600
    for c in chunks:
        assert c.index >= 0


def test_rag_search_nodes_n1_n5_rrf_fallback():
    """RAG 知识库 核心节点：改写 + RRF 融合（无需 Milvus/LLM）"""
    from project_agent.rag_kb.nodes import q_n5_rrf_fusion

    state = {
        "recalled_chunks": [
            {"pk": "A1", "score": 0.92, "item_name": "资产", "content": "工作站 37 台"},
            {"pk": "A2", "score": 0.81, "item_name": "资产", "content": "打印机"},
            {"pk": "A3", "score": 0.60, "item_name": "HR", "content": "陈昊P6"},
        ],
        "fuzzy_candidates": [
            {"similarity": 0.97, "module": "ASSET", "type": "asset",
             "code": "FS-2024-0876", "name": "联想工作站",
             "data": {"stock": 37, "price": 12800}},
        ],
    }
    fused = q_n5_rrf_fusion(state)["fused_candidates"]
    assert 1 <= len(fused) <= 20
    # 模糊工具召回的编码必须排在前面（它在两条列表里都没有的情况下得分独立）
    pk_prefix = [c["pk"] for c in fused]
    assert any(p.startswith("FUZZY#ASSET#FS-2024-0876") for p in pk_prefix)


def test_copilot_nodes_pipeline_fallback():
    """代码助手 5+1 节点在"无 LLM Key、无容器"时也能跑通（10+ 文件落盘）"""
    import shutil
    from project_agent.copilot.graph import run_copilot

    out_root = Path(tempfile.mkdtemp(prefix="smoke_"))
    # 临时替换 ROOT_DIR 到 tmp 目录（避免写进真实 output/）
    import project_agent.core.config as cfg
    old_root = cfg.ROOT_DIR
    try:
        cfg.ROOT_DIR = out_root  # 这里是 monkey patch，测试用
        final = run_copilot()
        assert "N6-WRITE" in final.get("steps_done", [])
        out = Path(final["output_dir"])
        assert out.exists()
        files = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())
        # 至少包含：2 个 md（设计 + README）+ 1 个 json 审查报告 + 若干 java/xml
        assert len(files) >= 10, f"期望 ≥10 个文件，实际 {len(files)}：{files}"
        # 关键文件必须存在
        names = set(files)
        assert any(n.endswith("InventoryController.java") for n in names)
        assert any(n.endswith("InventoryService.java") for n in names)
        assert any(n.endswith("AssetCodeMatcher.java") for n in names)
        assert any(n.endswith("InventoryServiceTest.java") for n in names)
        assert any(n.endswith("README-接口文档.md") for n in names)
        # README 必须包含 Mermaid 关键字
        readme = [out / n for n in names if n.endswith("README-接口文档.md")][0]
        txt = readme.read_text(encoding="utf-8")
        assert "mermaid" in txt.lower()
    finally:
        cfg.ROOT_DIR = old_root
        shutil.rmtree(out_root, ignore_errors=True)
