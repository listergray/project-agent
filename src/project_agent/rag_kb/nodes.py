"""
RAG 知识库节点：导入 + 检索（含 Self-RAG 路由 / Fusion / Grade / HITL / 忠实度）

【技能点】
  ✅ Prompt + 基础 RAG + 查询改写
  ✅ Self-RAG 路由（N1a need_rag）
  ✅ 多查询 RAG-Fusion（N1b LCEL + N3 多路召回 + N5 RRF）
  ✅ Self-RAG grade / 回跳（N6b）
  ✅ 图级 HITL（N6c）+ 答案忠实度 LCEL（N7b）
  ✅ Function Calling 思考-行动（N7）
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.rate_limiters import InMemoryRateLimiter
from loguru import logger
from pydantic import BaseModel, Field

from project_agent.clients import (
    achain,
    encode,
    ensure_collections,
    hybrid_search_chunks,
    search_item_names,
    upsert_chunks,
    upsert_item_names,
    get_embedding_dim,
    rerank,
)
from project_agent.core import new_trace_id
from project_agent.rag_kb.self_rag import q_n1a_self_rag_route, q_n6b_self_rag_grade
from project_agent.rag_kb.fusion import q_n1b_multi_query
from project_agent.rag_kb.faithfulness import q_n6c_hitl_retrieval, q_n7b_faithfulness
from project_agent.tools.rag_tools import RAG_TOOLS, RAG_TOOLS_BY_NAME
from project_agent.utils import (
    Chunk,
    format_history_for_prompt,
    load,
    load_text_file,
    split_markdown,
    trim_messages,
)

# =====================================================================
# 导入流水线（7 节点）
# =====================================================================

def i_n1_parse_file(state: Dict[str, Any]) -> Dict[str, Any]:
    """N1 解析：读取 file_path，返回 file_meta"""
    t0 = time.perf_counter()
    p = Path(state.get("file_path") or "").expanduser().resolve()
    if not p.exists():
        return {"errors": [f"导入失败：文件不存在 {p}"], "cost_ms": int((time.perf_counter()-t0)*1000)}
    suffix = p.suffix.lower().lstrip(".")
    if suffix not in {"md", "markdown", "txt", "pdf"}:
        return {"errors": [f"暂不支持的文件类型 .{suffix}（仅支持 md/txt/pdf）"]}
    return {
        "file_meta": {
            "name": p.name,
            "stem": p.stem,
            "suffix": suffix,
            "size_bytes": p.stat().st_size,
            "abs_path": str(p),
        },
        "trace_id": state.get("trace_id") or new_trace_id(),
    }


def i_n2_read_or_ocr(state: Dict[str, Any]) -> Dict[str, Any]:
    """N2 读 MD/TXT，或走 PDF 解析"""
    meta = state["file_meta"]
    t0 = time.perf_counter()
    try:
        md = load_text_file(Path(meta["abs_path"]))
    except Exception as e:  # noqa: BLE001
        return {"errors": [f"文件解析失败: {e}"]}
    logger.info(f"[Import N2] 解析完成: {meta['name']} md_chars={len(md)} cost={(time.perf_counter()-t0)*1000:.0f}ms")
    return {"raw_markdown": md}


def i_n3_structure(state: Dict[str, Any]) -> Dict[str, Any]:
    """N3 结构化 + 清洗（MVP 合并到 N2/N4 之间，这里做空行/超长链接清理）"""
    md = state.get("raw_markdown") or ""
    import re
    md2 = re.sub(r"[ \t]+", " ", md)                     # 多空格合并
    md2 = re.sub(r"\n{3,}", "\n\n", md2)                 # 多空行合并
    md2 = re.sub(r"https?://\S+", "[URL]", md2)          # URL 归一化，避免污染 embedding
    logger.info(f"[Import N3] 清洗后字符数: {len(md2)}")
    return {"raw_markdown": md2}


def i_n4_semantic_split(state: Dict[str, Any]) -> Dict[str, Any]:
    """N4 语义分块（Markdown 标题路径）"""
    md = state.get("raw_markdown") or ""
    meta = state.get("file_meta") or {}
    chunks: List[Chunk] = split_markdown(md, file_title=meta.get("stem", ""))
    # Chunk → dict（JSON 可序列化）
    chunk_dicts = [
        {
            "content": c.content,
            "title_path": c.title_path,
            "index": c.index,
            "file_title": c.file_title,
            "breadcrumb": c.breadcrumb,
        }
        for c in chunks
    ]
    logger.info(f"[Import N4] 语义分块 {len(chunk_dicts)} 块")
    return {"chunks": chunk_dicts}


class ItemInfoOutput(BaseModel):
    item_name: str = Field(..., description="标准化的手册/文档名称，≤30字")
    category: str = Field(..., pattern="^(ASSET|HR|FIN|OTHER)$")
    summary: str = Field(..., description="一句话摘要，≤120字")


def i_n5_extract_item(state: Dict[str, Any]) -> Dict[str, Any]:
    """N5 用 LLM 从文档前 2000 字抽取「文档名称 + 分类 + 摘要」。失败降级用文件名。"""
    md_head = (state.get("raw_markdown") or "")[:2000]
    meta = state.get("file_meta") or {}
    sys = load("rag_import_n5_iteminfo") or (
        "你是企业知识库助理。请根据用户提供的文档开头内容，抽取 3 个字段并用纯 JSON 返回：\n"
        "{\"item_name\": str(文档名称≤30字), \"category\": ASSET|HR|FIN|OTHER, "
        "\"summary\": str(一句话摘要≤120字)}"
    )
    user = (
        f"文件名: {meta.get('name','')}\n"
        f"文档前2000字内容:\n---\n{md_head}\n---\n"
        "请输出纯 JSON，不要加解释。"
    )
    fallback = ItemInfoOutput(
        item_name=meta.get("stem", "未命名文档"),
        category="OTHER",
        summary=f"（自动兜底，未走 LLM）文件名 {meta.get('name','')}",
    ).model_dump()

    try:
        txt = achain(sys, user, json_mode=True)
        obj = json.loads(txt if isinstance(txt, str) else str(txt))
        parsed = ItemInfoOutput.model_validate(obj)
        info = parsed.model_dump()
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[Import N5] LLM 抽取失败，使用兜底：{e}")
        info = fallback

    pk_src = f"{info['item_name']}|{meta.get('name','')}|{len(state.get('raw_markdown',''))}"
    item_pk = hashlib.md5(pk_src.encode("utf-8")).hexdigest()[:16]
    logger.info(f"[Import N5] item_name={info['item_name']!r} cat={info['category']} pk={item_pk}")
    return {
        "item_name": info["item_name"],
        "item_category": info["category"],
        "item_summary": info["summary"],
        "item_pk": item_pk,
    }


def i_n6_encode_vectors(state: Dict[str, Any]) -> Dict[str, Any]:
    """N6 向量编码：文档级 1 条 + 每 chunk 1 条"""
    item_name = state.get("item_name", "")
    summary = state.get("item_summary", "")
    chunks = state.get("chunks") or []
    t0 = time.perf_counter()

    item_texts = [f"【{item_name}】{summary}"]
    chunk_texts = [
        f"【{item_name}】【{c.get('breadcrumb','')}】{c.get('content','')}"
        for c in chunks
    ]

    # 编码（懒加载模型；首次 5s+ 正常，之后毫秒级）
    try:
        item_vec = encode(item_texts)[0].tolist()
    except Exception as e:  # noqa: BLE001
        logger.error(f"[Import N6] item 向量编码失败，填零向量兜底: {e}")
        item_vec = [0.0] * (get_embedding_dim())
    try:
        chunk_vecs = encode(chunk_texts).tolist() if chunk_texts else []
    except Exception as e:  # noqa: BLE001
        logger.error(f"[Import N6] chunk 向量编码失败，填零向量兜底: {e}")
        dim = len(item_vec)
        chunk_vecs = [[0.0] * dim for _ in chunks]

    if len(chunk_vecs) != len(chunks):
        # 兜底补齐
        dim = len(item_vec)
        chunk_vecs = (chunk_vecs + [[0.0] * dim] * len(chunks))[: len(chunks)]

    logger.info(
        f"[Import N6] 编码完成 vectors=(item 1 + chunks {len(chunk_vecs)}) "
        f"cost={(time.perf_counter()-t0)*1000:.0f}ms"
    )
    return {"encoded_item_vector": item_vec, "encoded_chunk_vectors": chunk_vecs}


def i_n7_write_milvus(state: Dict[str, Any]) -> Dict[str, Any]:
    """N7 写 Milvus：kb_item_names + kb_chunks（失败不 raise，写 errors 字段）"""
    ensure_collections()
    t0 = time.perf_counter()
    item_pk = state["item_pk"]
    item_name = state["item_name"]
    category = state.get("item_category", "OTHER")
    file_title = (state.get("file_meta") or {}).get("name", "")
    chunks = state.get("chunks") or []
    item_vec = state["encoded_item_vector"]
    chunk_vecs = state.get("encoded_chunk_vectors") or []
    summary = state.get("item_summary", "")
    now_ms = int(time.time() * 1000)

    item_row = {
        "pk": item_pk,
        "item_name": item_name,
        "file_title": file_title,
        "category": category,
        "chunk_count": len(chunks),
        "summary": summary,
        "dense_vector": item_vec,
        "created_at": now_ms,
    }
    chunk_rows = [
        {
            "pk": f"{item_pk}#{c['index']}",
            "item_pk": item_pk,
            "item_name": item_name,
            "file_title": file_title,
            "title_path": c.get("breadcrumb", ""),
            "content": (c.get("content") or "")[:65500],
            "chunk_index": int(c.get("index", i)),
            "dense_vector": vec,
            "created_at": now_ms,
        }
        for i, (c, vec) in enumerate(zip(chunks, chunk_vecs))
    ]
    try:
        upsert_item_names([item_row])
        upsert_chunks(chunk_rows)
    except Exception as e:  # noqa: BLE001
        return {"errors": [f"Milvus 入库失败: {e}"], "import_result": {"success": False}}

    result = {
        "success": True,
        "item_pk": item_pk,
        "item_name": item_name,
        "category": category,
        "item_upserted": 1,
        "chunks_upserted": len(chunk_rows),
        "cost_ms": int((time.perf_counter() - t0) * 1000),
    }
    logger.info(
        f"[Import N7] 导入成功 pk={item_pk} chunks={len(chunk_rows)} "
        f"cost={result['cost_ms']}ms"
    )
    return {"import_result": result}


# =====================================================================
# 检索流水线（7 节点）
# =====================================================================

class IntentRewriteOutput(BaseModel):
    intent: str = Field(..., pattern="^(RETRIEVAL|TOOL_FIRST|MIXED)$")
    rewritten_query: str = Field(..., description="改写后的标准问句，适合向量检索")
    target_modules: List[str] = Field(
        default_factory=list, description="命中的模块：ASSET/HR/FIN，空=不限"
    )


def q_n1_rewrite_intent(state: Dict[str, Any]) -> Dict[str, Any]:
    """N1 意图识别 + Query 改写"""
    user_query = state["user_query"]
    sys = load("rag_search_n1_rewrite") or (
        "你是企业知识库的意图路由器。分析用户问句，输出纯 JSON：\n"
        "{\n"
        '  "intent": "RETRIEVAL | TOOL_FIRST | MIXED",\n'
        '    RETRIEVAL: 纯检索知识类（如"工作站怎么申请"）\n'
        '    TOOL_FIRST: 纯查数类（如"FS-2024-0876 库存多少" "陈昊工号多少" "导出所有资产"）\n'
        '    MIXED: 既要检索又要查库（如"结合制度查 FS-2024-0876 的库存是否合理"）\n'
        '  "rewritten_query": "（把模糊表述改写成标准中文问句，补充同义词展开）",\n'
        '  "target_modules": ["ASSET"|"HR"|"FIN"]  # 命中的模块\n'
        "}\n"
        "3 个工具：query_resource_by_code（按编码查）、fuzzy_match_resource（名字模糊）、"
        "export_to_excel（导出结果）。识别出编码或明确查库的直接走 TOOL_FIRST。"
    )
    fallback = IntentRewriteOutput(
        intent="MIXED", rewritten_query=user_query, target_modules=[],
    ).model_dump()
    try:
        txt = achain(sys, f"用户问句：\n{user_query}\n", json_mode=True)
        obj = json.loads(txt if isinstance(txt, str) else str(txt))
        out = IntentRewriteOutput.model_validate(obj).model_dump()
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[Search N1] 意图识别 LLM 失败兜底: {e}")
        out = fallback
    logger.info(
        f"[Search N1] intent={out['intent']} modules={out['target_modules']} "
        f"rewritten={out['rewritten_query'][:60]!r}"
    )
    return {
        "intent": out["intent"],
        "rewritten_query": out["rewritten_query"],
        "target_modules": out["target_modules"],
        "trace_id": state.get("trace_id") or new_trace_id(),
    }


def q_n2_locate_item(state: Dict[str, Any]) -> Dict[str, Any]:
    """N2 定位 item（文档级粗排，确认是哪本手册）。Top2 内置信度 >0.75 则锁定；否则 None = 跨文档搜"""
    ensure_collections()
    q = state["rewritten_query"]
    q_vec = encode([q])[0]
    cands = search_item_names(q_vec, top_k=5)
    if not cands:
        return {"item_candidates": [], "confirmed_item_pk": None, "confirmed_item_name": None}
    # 锁定条件：最高分 > 0.55 且 第二名比第一名低 0.05 以上（稳定胜出）
    top = cands[0]
    second_score = cands[1]["score"] if len(cands) > 1 else 0.0
    confirmed = (top["score"] > 0.55) and (top["score"] - second_score >= 0.05)
    logger.info(
        f"[Search N2] item_top1=({top['score']:.3f},{top['item_name']!r}) "
        f"second={second_score:.3f} → confirmed={confirmed}"
    )
    return {
        "item_candidates": cands,
        "confirmed_item_pk": top["pk"] if confirmed else None,
        "confirmed_item_name": top["item_name"] if confirmed else None,
    }


def q_n3_vector_recall(state: Dict[str, Any]) -> Dict[str, Any]:
    """N3 向量召回：委托 fusion 多查询实现。"""
    from project_agent.rag_kb.fusion import q_n3_vector_recall as _multi

    return _multi(state)


def q_n4_tool_fuzzy_recall(state: Dict[str, Any]) -> Dict[str, Any]:
    """N4 模糊匹配工具召回：TOOL_FIRST / MIXED 模式调用 fuzzy_match_resource 拉业务库候选"""
    intent = state.get("intent", "MIXED")
    if intent == "RETRIEVAL":
        return {"fuzzy_candidates": []}
    q = state["user_query"]
    # 用前 80 个字符作为关键词（工具对长度有限制）
    kw = q[:80]
    module = (state.get("target_modules") or [""])[0] or None
    try:
        tool = RAG_TOOLS_BY_NAME["fuzzy_match_resource"]
        res = tool.invoke({"keyword": kw, "top_k": 10, "module": module})
        cands = res.get("candidates") or []
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[Search N4] fuzzy 工具调用失败: {e}")
        cands = []
    logger.info(f"[Search N4] 模糊匹配召回 {len(cands)} 条业务数据")
    return {"fuzzy_candidates": cands}


def q_n5_rrf_fusion(state: Dict[str, Any]) -> Dict[str, Any]:
    """N5 RRF 融合（重点"多策略融合"）：向量召回 + 模糊召回，RRF k=60"""
    chunks = {c["pk"]: c for c in state.get("recalled_chunks") or []}
    fuzzy = state.get("fuzzy_candidates") or []
    K = 60

    rrf_scores: Dict[str, float] = {}
    # 向量结果贡献 1..len
    for rank, c in enumerate(state.get("recalled_chunks") or [], start=1):
        rrf_scores[c["pk"]] = rrf_scores.get(c["pk"], 0.0) + 1.0 / (K + rank)
    # 模糊结果贡献：用 code 作 pk，构造一条"伪 chunk"放到 chunks 字典里
    for rank, f in enumerate(fuzzy, start=1):
        pseudo_pk = f"FUZZY#{f['module']}#{f['code']}"
        rrf_scores[pseudo_pk] = rrf_scores.get(pseudo_pk, 0.0) + 1.0 / (K + rank)
        data = f.get("data") or {}
        if isinstance(data, dict):
            pretty = "，".join(f"{k}={v}" for k, v in list(data.items())[:10])
        else:
            pretty = str(data)
        chunks[pseudo_pk] = {
            "pk": pseudo_pk,
            "item_pk": "FUZZY_TOOL",
            "item_name": f"[{f['module']} 业务库模糊匹配]",
            "file_title": f"query_resource_by_code / fuzzy_match_resource 工具返回",
            "title_path": f"{f['type']} 相似度 {f['similarity']}",
            "content": f"（业务库实时查回）编码 {f['code']} / {f['name']}：{pretty}",
            "score": f.get("similarity", 0.0),
            "source": f"tool:fuzzy/{f['module']}/{f['code']}",
        }

    # 降序取 Top20
    sorted_pks = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:20]
    fused = []
    for pk, s in sorted_pks:
        c = chunks[pk].copy()
        c["rrf_score"] = round(s, 5)
        fused.append(c)
    logger.info(f"[Search N5] RRF 融合：向量{len(state.get('recalled_chunks') or [])} + "
                f"模糊{len(fuzzy)} → 融合 Top{len(fused)}")
    return {"fused_candidates": fused}


def q_n6_rerank(state: Dict[str, Any]) -> Dict[str, Any]:
    """N6 精排：Rerank 模型 Top5，失败则降级按 RRF 顺序取前 5"""
    q = state["rewritten_query"]
    fused = state.get("fused_candidates") or []
    if not fused:
        return {"reranked_candidates": []}
    docs = [
        f"【{c.get('item_name','')}】【{c.get('title_path','')}】{c.get('content','')}"
        for c in fused
    ]
    # 最多给 Rerank 20 条
    top_idx = rerank(q, docs[:20], top_k=5)
    reranked = [fused[i] for i in top_idx]
    logger.info(f"[Search N6] Rerank 后取 {len(reranked)} 条（候选 {len(fused)}）")
    return {"reranked_candidates": reranked}


def q_n7_answer_with_tools(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    N7 生成最终回答：
    - 先把精排 Top5 作为上下文拼 Prompt
    - 再走一次 ReAct：允许模型最多调 3 次 3 个工具（query_resource_by_code / fuzzy / export）
    - 最后输出 Markdown 回答 + source 来源
    设计说明：我把"上下文拼接 + Function Calling + 最终生成"统一在一个节点，
    用 while 循环 + max_steps=3 控制工具调用轮次，比拆多个节点简单、可观测性更强。
    """
    q = state["user_query"]
    rewritten = state["rewritten_query"]
    ctx = state.get("reranked_candidates") or []
    intent = state.get("intent", "MIXED")

    # 1) 构造上下文 block
    ctx_blocks: List[str] = []
    sources: List[str] = []
    for i, c in enumerate(ctx, 1):
        src = c.get("source") or f"{c.get('file_title','')}#{c.get('title_path','')}"
        if src not in sources:
            sources.append(src)
        ctx_blocks.append(
            f"【上下文{i}】来源：{src}\n"
            f"标题：{c.get('item_name','')} / {c.get('title_path','')}\n"
            f"内容：{c.get('content','')}\n"
        )
    context_text = "\n".join(ctx_blocks) if ctx_blocks else "（上下文为空，完全走工具查库或直说不知道）"
    hist_text = format_history_for_prompt(trim_messages(state.get("messages") or []))
    grade = state.get("self_rag_grade") or {}
    grade_hint = ""
    if grade:
        grade_hint = (
            f"【Self-RAG 评估】relevant={grade.get('relevant')} "
            f"score={grade.get('score')} reason={grade.get('reason','')}\n"
        )

    # 2) 系统 Prompt
    sys_prompt = (
        load("rag_search_n7_answer") or (
            "你是「企业资源知识库助手」，严格按以下规则回答：\n"
            "1. 回答必须基于「上下文」+「工具返回结果」，严禁编造数据；\n"
            "2. 遇到编码类问题（FS-* / HR-EMP-* / FIN-*）先调用 query_resource_by_code；\n"
            "3. 只记得名字或部分编码 → 调用 fuzzy_match_resource；\n"
            "4. 结果 ≥3 条且用户说「导出/下载/表格」→ 调用 export_to_excel；\n"
            "5. 最终回答用 Markdown，答案前先复述用户问题，末尾列出【来源】。\n"
        )
    )
    user_prompt = (
        f"【用户原始问题】{q}\n"
        f"【改写后问题】{rewritten}\n"
        f"【识别模式】{intent}\n"
        f"{grade_hint}"
        f"【近期对话（已窗口裁剪）】\n{hist_text}\n\n"
        f"【已召回上下文（RRF + Rerank）】\n{context_text}\n\n"
        "请基于以上信息回答；必要时调用 3 个工具，最多调用 3 轮。"
    )

    # 3) 简易 ReAct 循环（最多 3 轮）
    MAX_STEPS = 3
    tool_call_trace: List[dict] = []
    # 第一轮：直接让 LLM 生成 JSON 决策（bind_tools 失败时的兜底 JSON 格式）
    decision_prompt = sys_prompt + "\n\n" + user_prompt + (
        "\n\n【输出格式二选一】：\n"
        "A) 直接回答（不再调工具）：输出纯 JSON {\"answer\": \"Markdown 回答字符串\"}\n"
        "B) 调 1 个工具：输出纯 JSON {\"tool_call\": {\"name\": \"工具名\", \"args\": {...}}}\n"
        "工具可选 3 个：query_resource_by_code / fuzzy_match_resource / export_to_excel\n"
        "工具参数按 LangChain Tool 的 args_schema（见工具 docstring）填写。"
    )

    last_answer = ""
    for step in range(1, MAX_STEPS + 1):
        try:
            txt = achain(
                "你是严格输出 JSON 的决策器，只输出 JSON，不能有其他文字。",
                decision_prompt,
                json_mode=True,
            )
            obj = json.loads(txt if isinstance(txt, str) else str(txt))
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[Search N7] step{step} 决策 JSON 解析失败: {e}")
            last_answer = f"（模型返回格式异常）原始问题：{q}\n\n当前上下文不足，建议换个问法。"
            break

        if "answer" in obj and isinstance(obj["answer"], str):
            last_answer = obj["answer"].strip()
            logger.info(f"[Search N7] step{step} 直接回答 chars={len(last_answer)}")
            break

        if "tool_call" in obj and isinstance(obj["tool_call"], dict):
            tc = obj["tool_call"]
            name = tc.get("name")
            args = tc.get("args") or {}
            if name not in RAG_TOOLS_BY_NAME:
                logger.warning(f"[Search N7] step{step} 请求了未知工具 {name!r}，终止")
                last_answer = last_answer or f"（工具 {name!r} 不存在）请重试。"
                break
            tool = RAG_TOOLS_BY_NAME[name]
            # 特判 export：用户没给 rows，就把已召回上下文 + fuzzy candidates 导出去
            if name == "export_to_excel" and not args.get("rows"):
                rows = []
                for c in ctx:
                    rows.append({"来源": c.get("source"), "标题": c.get("title_path"),
                                 "内容摘要": (c.get("content") or "")[:200],
                                 "相似度": c.get("rrf_score")})
                rows.extend([
                    {k: v for k, v in f.items() if k != "data"} | (f.get("data") or {})
                    for f in state.get("fuzzy_candidates") or []
                ])
                args["rows"] = rows
                args.setdefault("filename", "rag_export")
            try:
                result = tool.invoke(args)
            except Exception as e:  # noqa: BLE001
                result = {"error": str(e)}
            tool_call_trace.append({"step": step, "name": name, "args": args, "result": result})
            logger.info(
                f"[Search N7] step{step} 调工具 {name} args_keys={list(args.keys())} "
                f"result_keys={list(result.keys()) if isinstance(result, dict) else type(result)}"
            )
            # 把工具结果追加进 decision_prompt，让 LLM 下一轮决定"还要不要调/或者直接回答"
            decision_prompt += (
                f"\n\n【Step{step} 工具调用记录】\n"
                f"工具：{name}\n参数：{json.dumps(args, ensure_ascii=False)}\n"
                f"返回：{json.dumps(result, ensure_ascii=False, default=str)[:4000]}\n"
                "请继续输出纯 JSON：要么 {\"answer\": ...} 要么 {\"tool_call\": ...}。"
            )
            continue

        # 啥都不是，兜底
        last_answer = "（模型返回格式不符合要求）请重试。"
        break

    # 4) 把 answer 里提到的来源 + 实际来源合并
    answer = last_answer.strip()
    if answer and "【来源】" not in answer:
        answer += "\n\n【来源】\n" + "\n".join(f"- {s}" for s in sources) if sources else ""

    logger.info(
        f"[Search N7] 完成：工具调用 {len(tool_call_trace)} 次，回答 {len(answer)} 字，"
        f"来源 {len(sources)} 条"
    )
    return {
        "answer": answer,
        "sources": sources,
        "tool_calls": tool_call_trace,
    }


# 导出节点：builder.py 里按名字取
IMPORT_NODES = [
    ("i_n1_parse_file", i_n1_parse_file),
    ("i_n2_read_or_ocr", i_n2_read_or_ocr),
    ("i_n3_structure", i_n3_structure),
    ("i_n4_semantic_split", i_n4_semantic_split),
    ("i_n5_extract_item", i_n5_extract_item),
    ("i_n6_encode_vectors", i_n6_encode_vectors),
    ("i_n7_write_milvus", i_n7_write_milvus),
]

SEARCH_NODES = [
    ("q_n1_rewrite_intent", q_n1_rewrite_intent),
    ("q_n1a_self_rag_route", q_n1a_self_rag_route),
    ("q_n1b_multi_query", q_n1b_multi_query),
    ("q_n2_locate_item", q_n2_locate_item),
    ("q_n3_vector_recall", q_n3_vector_recall),
    ("q_n4_tool_fuzzy_recall", q_n4_tool_fuzzy_recall),
    ("q_n5_rrf_fusion", q_n5_rrf_fusion),
    ("q_n6_rerank", q_n6_rerank),
    ("q_n6b_self_rag_grade", q_n6b_self_rag_grade),
    ("q_n6c_hitl_retrieval", q_n6c_hitl_retrieval),
    ("q_n7_answer_with_tools", q_n7_answer_with_tools),
    ("q_n7b_faithfulness", q_n7b_faithfulness),
]

__all__ = [
    "IMPORT_NODES",
    "SEARCH_NODES",
    "i_n1_parse_file", "i_n2_read_or_ocr", "i_n3_structure",
    "i_n4_semantic_split", "i_n5_extract_item", "i_n6_encode_vectors", "i_n7_write_milvus",
    "q_n1_rewrite_intent", "q_n1a_self_rag_route", "q_n1b_multi_query", "q_n2_locate_item",
    "q_n3_vector_recall", "q_n4_tool_fuzzy_recall", "q_n5_rrf_fusion", "q_n6_rerank",
    "q_n6b_self_rag_grade", "q_n6c_hitl_retrieval",
    "q_n7_answer_with_tools", "q_n7b_faithfulness",
]
