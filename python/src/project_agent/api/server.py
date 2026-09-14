"""
FastAPI 统一服务入口（Python AI 编排服务）

【技能点 · 混合架构理解】
  ✅ 本服务 = Python AI 编排（RAG / Copilot / 立项）对外 HTTP
  📘 企业落地常见形态：Java 微服务扛业务交易，本仓类服务扛 Agent/RAG；
     代码助手生成的 Java 样板可落到业务仓；工具层可回调 Java API（当前为 Mock DB）

启动：agent-api 或 uvicorn project_agent.api.server:app --port 8080

主要路由：
  POST /api/v1/rag/import|preview|rollback|chat|chat/stream
  POST /api/v1/copilot/run
  /api/v1/projects/*（录入审批 + 通过后同步知识库）
  GET  /api/v1/health
  SPA：python-frontend/dist（React）
"""
from __future__ import annotations

import json
import re
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel, Field

from project_agent.clients import (
    delete_by_item_pk,
    ensure_collections,
    list_chunks_by_item_pk,
    stats as milvus_stats,
)
from project_agent.core import ROOT_DIR, get_settings, get_trace_id, new_trace_id
from project_agent.rag_kb import PRESET_QUERIES, run_import, run_search, resume_search, iter_search_events
from project_agent.copilot import run_copilot
from project_agent.projects import get_store, parse_project_from_text, try_sync_approved_project
from project_agent.projects.models import ApproveReq, ProjectCreate, ProjectStatus
from project_agent.utils import load_all, load_text_file

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: D401
    import threading

    from project_agent.core import configure_langsmith

    configure_langsmith()

    def _warm_milvus() -> None:
        try:
            ensure_collections()
            logger.info(f"[API] Milvus ready stats={milvus_stats()}")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[API] Milvus 未就绪，跳过集合初始化（代码助手 / 工具层仍可用）: {e}")

    # 不阻塞启动：embedding 模型加载较慢，否则 /assets/*.css 长时间不可用，iframe 页会「裸 HTML」
    threading.Thread(target=_warm_milvus, name="milvus-warm", daemon=True).start()
    logger.info(f"[API] Server accepting traffic on port={settings.port} (Milvus warming in background)")
    yield


app = FastAPI(
    title="Project Agent API",
    description=(
        "预研项目 2 个 Agent 的 HTTP 入口：\n"
        "- RAG 知识库 RAG+Agent（7+7 节点 LangGraph + 3 个 Function Calling 工具）\n"
        "- 代码助手 AI 编程提效 Agent（5 节点流水线：需求→代码→审查→单测→文档）"
    ),
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# 前端 SPA（Vite React：python-frontend/dist）
# 路由 fallback 注册在全部 API 之后，见文件末尾
# ============================================================
_DIST_DIR = ROOT_DIR / "python-frontend" / "dist"
if not _DIST_DIR.is_dir():
    _DIST_DIR = ROOT_DIR / "python-frontend" / "vue" / "dist"



# ============================================================
# Health / Meta
# ============================================================
@app.get("/api/v1/health", tags=["元信息"])
def health() -> Dict[str, Any]:
    """liveness=进程存活；readiness=Milvus 可统计（RAG 主依赖就绪）。"""
    try:
        ms = milvus_stats()
    except Exception as e:  # noqa: BLE001
        ms = {"error": str(e)}
    milvus_ok = isinstance(ms, dict) and "error" not in ms and (
        ms.get("kb_chunks") is not None or ms.get("kb_item_names") is not None
    )
    return {
        "liveness": True,
        "readiness": bool(milvus_ok),
        "milvus": ms,
        "trace_id": get_trace_id(),
    }


@app.get("/api/v1/prompts", tags=["元信息"], summary="查看所有 Prompt 模板（展示调优过哪些 Prompt）")
def list_prompts() -> Dict[str, List[str]]:
    return {"files": sorted(load_all().keys())}


@app.get("/api/v1/rag/presets", tags=["RAG 知识库"])
def rag_presets() -> List[Dict[str, str]]:
    return [{"tag": t, "query": q} for t, q in PRESET_QUERIES]


# ============================================================
# RAG 知识库
# ============================================================
class ChatReq(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="用户自然语言问题")
    session_id: Optional[str] = Field(None, description="会话 ID，用于后续多轮")


class ChatResumeReq(BaseModel):
    session_id: str = Field(..., min_length=1, description="中断时的会话 ID")
    action: str = Field("approve", description="approve | rewrite")
    rewritten_query: Optional[str] = Field(None, description="action=rewrite 时的新问句")


class ChatResp(BaseModel):
    session_id: str
    answer: str
    sources: List[str]
    tool_calls: List[Dict[str, Any]]
    intent: str
    elapsed_ms: int
    need_rag: Optional[bool] = None
    self_rag_route_reason: Optional[str] = None
    self_rag_retries: int = 0
    self_rag_grade: Optional[Dict[str, Any]] = None
    multi_queries: List[str] = Field(default_factory=list)
    retrieval_paths: Optional[Dict[str, Any]] = None
    faithfulness_score: Optional[float] = None
    faithfulness: Optional[Dict[str, Any]] = None
    interrupted: bool = False
    interrupt_payload: Optional[Dict[str, Any]] = None
    need_human_review: bool = False


def _chat_resp_from_result(res: Dict[str, Any], elapsed_ms: int) -> ChatResp:
    return ChatResp(
        session_id=str(res.get("session_id", "")),
        answer=str(res.get("answer", "")),
        sources=list(res.get("sources") or []),
        tool_calls=list(res.get("tool_calls") or []),
        intent=str(res.get("intent", "MIXED")),
        elapsed_ms=elapsed_ms,
        need_rag=res.get("need_rag") if "need_rag" in res else None,
        self_rag_route_reason=res.get("self_rag_route_reason"),
        self_rag_retries=int(res.get("self_rag_retries") or 0),
        self_rag_grade=res.get("self_rag_grade"),
        multi_queries=list(res.get("multi_queries") or []),
        retrieval_paths=res.get("retrieval_paths"),
        faithfulness_score=res.get("faithfulness_score"),
        faithfulness=res.get("faithfulness"),
        interrupted=bool(res.get("interrupted")),
        interrupt_payload=res.get("interrupt_payload"),
        need_human_review=bool(res.get("need_human_review")),
    )


@app.post("/api/v1/rag/chat", tags=["RAG 知识库"], response_model=ChatResp)
def rag_chat(req: ChatReq) -> ChatResp:
    t0 = time.perf_counter()
    res = run_search(req.query, session_id=req.session_id)
    if res.get("errors") and not res.get("interrupted"):
        raise HTTPException(status_code=500, detail={"errors": res["errors"]})
    return _chat_resp_from_result(res, int((time.perf_counter() - t0) * 1000))


@app.post("/api/v1/rag/chat/resume", tags=["RAG 知识库"], response_model=ChatResp, summary="图级 HITL 恢复")
def rag_chat_resume(req: ChatResumeReq) -> ChatResp:
    t0 = time.perf_counter()
    action = (req.action or "approve").strip().lower()
    if action not in {"approve", "rewrite"}:
        raise HTTPException(400, detail="action 仅支持 approve|rewrite")
    res = resume_search(req.session_id, action=action, rewritten_query=req.rewritten_query)
    if res.get("errors") and not res.get("interrupted"):
        raise HTTPException(status_code=500, detail={"errors": res["errors"]})
    return _chat_resp_from_result(res, int((time.perf_counter() - t0) * 1000))


async def _chat_stream(req: ChatReq):
    """SSE：节点 status + N7 真 token 流 + meta / done | interrupted。"""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()
    sentinel = object()

    def _produce() -> None:
        try:
            for ev in iter_search_events(req.query, session_id=req.session_id):
                loop.call_soon_threadsafe(queue.put_nowait, ev)
        except Exception as e:  # noqa: BLE001
            logger.exception(f"[Chat.stream] iter_search_events 失败: {e}")
            loop.call_soon_threadsafe(
                queue.put_nowait,
                {"event": "error", "detail": str(e)},
            )
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, sentinel)

    t0 = time.perf_counter()
    executor = ThreadPoolExecutor(max_workers=1)
    executor.submit(_produce)

    streamed_answer = False
    meta_sent = False
    res: Dict[str, Any] = {}
    try:
        while True:
            item = await queue.get()
            if item is sentinel:
                break
            if not isinstance(item, dict):
                continue
            et = item.get("event")
            if et == "status":
                sid0 = item.get("session_id")
                if sid0 and not meta_sent:
                    meta_sent = True
                    yield "event: meta\ndata: " + json.dumps(
                        {
                            "session_id": sid0,
                            "intent": "",
                            "tool_calls": [],
                            "sources": [],
                            "elapsed_ms": 0,
                        },
                        ensure_ascii=False,
                    ) + "\n\n"
                yield "event: status\ndata: " + json.dumps(
                    {
                        "stage": item.get("stage"),
                        "message": item.get("message"),
                        "session_id": item.get("session_id"),
                    },
                    ensure_ascii=False,
                ) + "\n\n"
            elif et == "token":
                streamed_answer = True
                if not meta_sent and item.get("session_id"):
                    meta_sent = True
                    yield "event: meta\ndata: " + json.dumps(
                        {
                            "session_id": item.get("session_id"),
                            "intent": "",
                            "tool_calls": [],
                            "sources": [],
                            "elapsed_ms": 0,
                        },
                        ensure_ascii=False,
                    ) + "\n\n"
                yield "event: token\ndata: " + json.dumps(
                    {"text": item.get("text", "")},
                    ensure_ascii=False,
                ) + "\n\n"
            elif et == "error":
                yield "event: error\ndata: " + json.dumps(
                    {"detail": item.get("detail")},
                    ensure_ascii=False,
                ) + "\n\n"
                return
            elif et == "result":
                res = item.get("data") or {}
    finally:
        executor.shutdown(wait=False)

    if res.get("errors") and not res.get("interrupted"):
        yield "event: error\ndata: " + json.dumps(
            {"detail": res["errors"]},
            ensure_ascii=False,
        ) + "\n\n"
        return

    elapsed = int((time.perf_counter() - t0) * 1000)
    meta = {
        "session_id": str(res.get("session_id", "")),
        "intent": str(res.get("intent", "")),
        "tool_calls": list(res.get("tool_calls") or []),
        "sources": list(res.get("sources") or []),
        "elapsed_ms": elapsed,
        "need_rag": res.get("need_rag"),
        "self_rag_route_reason": res.get("self_rag_route_reason"),
        "self_rag_retries": int(res.get("self_rag_retries") or 0),
        "self_rag_grade": res.get("self_rag_grade"),
        "multi_queries": list(res.get("multi_queries") or []),
        "retrieval_paths": res.get("retrieval_paths"),
        "faithfulness_score": res.get("faithfulness_score"),
        "faithfulness": res.get("faithfulness"),
        "interrupted": bool(res.get("interrupted")),
        "interrupt_payload": res.get("interrupt_payload"),
        "need_human_review": bool(res.get("need_human_review")),
        "streamed": streamed_answer,
    }
    yield "event: meta\ndata: " + json.dumps(meta, ensure_ascii=False) + "\n\n"

    if res.get("interrupted"):
        yield "event: interrupted\ndata: " + json.dumps(meta, ensure_ascii=False) + "\n\n"
        return

    # 若未收到 custom token（旧路径/中断旁路），兜底推送完整答案
    if not streamed_answer:
        ans = str(res.get("answer", ""))
        if ans:
            yield "event: token\ndata: " + json.dumps({"text": ans}, ensure_ascii=False) + "\n\n"

    yield "event: done\ndata: " + json.dumps({"elapsed_ms": elapsed}, ensure_ascii=False) + "\n\n"


@app.post("/api/v1/rag/chat/stream", tags=["RAG 知识库"], summary="SSE 流式问答")
async def rag_chat_stream(req: ChatReq) -> StreamingResponse:
    return StreamingResponse(
        _chat_stream(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _chat_resume_stream(req: ChatResumeReq):
    import asyncio

    yield "event: status\ndata: " + json.dumps(
        {"stage": "resume", "message": "继续推理中…"},
        ensure_ascii=False,
    ) + "\n\n"
    t0 = time.perf_counter()
    try:
        res = await asyncio.to_thread(
            resume_search,
            req.session_id,
            action=(req.action or "approve").strip().lower(),
            rewritten_query=req.rewritten_query,
        )
    except Exception as e:  # noqa: BLE001
        logger.exception(f"[Chat.resume.stream] 失败: {e}")
        yield "event: error\ndata: " + json.dumps({"detail": str(e)}, ensure_ascii=False) + "\n\n"
        return
    elapsed = int((time.perf_counter() - t0) * 1000)
    meta = {
        "session_id": str(res.get("session_id", "")),
        "intent": str(res.get("intent", "")),
        "tool_calls": list(res.get("tool_calls") or []),
        "sources": list(res.get("sources") or []),
        "elapsed_ms": elapsed,
        "need_rag": res.get("need_rag"),
        "self_rag_route_reason": res.get("self_rag_route_reason"),
        "self_rag_retries": int(res.get("self_rag_retries") or 0),
        "self_rag_grade": res.get("self_rag_grade"),
        "multi_queries": list(res.get("multi_queries") or []),
        "retrieval_paths": res.get("retrieval_paths"),
        "faithfulness_score": res.get("faithfulness_score"),
        "faithfulness": res.get("faithfulness"),
        "interrupted": bool(res.get("interrupted")),
        "interrupt_payload": res.get("interrupt_payload"),
        "need_human_review": bool(res.get("need_human_review")),
    }
    yield "event: meta\ndata: " + json.dumps(meta, ensure_ascii=False) + "\n\n"
    if res.get("interrupted"):
        yield "event: interrupted\ndata: " + json.dumps(meta, ensure_ascii=False) + "\n\n"
        return
    ans = str(res.get("answer", ""))
    for i in range(0, len(ans), 4):
        yield "event: token\ndata: " + json.dumps({"text": ans[i:i + 4]}, ensure_ascii=False) + "\n\n"
        await asyncio.sleep(0.012)
    yield "event: done\ndata: " + json.dumps({"elapsed_ms": elapsed}, ensure_ascii=False) + "\n\n"


@app.post("/api/v1/rag/chat/resume/stream", tags=["RAG 知识库"], summary="HITL 恢复 SSE")
async def rag_chat_resume_stream(req: ChatResumeReq) -> StreamingResponse:
    return StreamingResponse(
        _chat_resume_stream(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/v1/rag/import", tags=["RAG 知识库"])
async def rag_import(
    file: UploadFile = File(..., description="MD/TXT/PDF 知识库文档"),
) -> Dict[str, Any]:
    tmp_dir = Path("./.tmp_uploads")
    tmp_dir.mkdir(exist_ok=True)
    dest = tmp_dir / f"{new_trace_id()}_{file.filename or 'document'}"
    try:
        content = await file.read()
        dest.write_bytes(content)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, detail=f"保存上传文件失败: {e}") from e
    result = run_import(str(dest))
    if result.get("errors"):
        raise HTTPException(500, detail={"errors": result["errors"]})
    return {"import_result": result.get("import_result"), "file_meta": result.get("file_meta")}


@app.post("/api/v1/rag/preview", tags=["RAG 知识库"], summary="上传并解析（先入库→预览→可回滚）")
async def rag_preview(
    file: UploadFile = File(..., description="MD/TXT/PDF 知识库文档"),
    preview_chars: int = Form(160, description="每条 chunk 预览字符数"),
    chunk_limit: int = Form(200, description="最多返回多少条 chunk 预览（200 封顶）"),
) -> Dict[str, Any]:
    """
    上传文件 → 跑 7 节点导入流水线 → 立即写入 Milvus →
    返回文件元信息 + 项目级元数据 + chunks 列表（预览用）。
    如不需要该文档，调 `POST /api/v1/rag/rollback` 删除（item_pk 联动删 chunks + item_names）。
    """
    tmp_dir = Path("./.tmp_uploads")
    tmp_dir.mkdir(exist_ok=True)
    dest = tmp_dir / f"{new_trace_id()}_{file.filename or 'document'}"
    try:
        content = await file.read()
        dest.write_bytes(content)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, detail=f"保存上传文件失败: {e}") from e

    stats_before = milvus_stats()

    t0 = time.perf_counter()
    try:
        result = run_import(str(dest))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, detail=f"导入流水线异常: {e}") from e
    if result.get("errors"):
        raise HTTPException(500, detail={"errors": result["errors"]})

    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    stats_after = milvus_stats()

    item_pk = result.get("item_pk", "")
    chunks_in_state = result.get("chunks") or []
    chunk_limit = max(1, min(int(chunk_limit), 200))
    preview_chars = max(50, min(int(preview_chars), 1000))

    # 直接从 ImportState.chunks 取（N4 已生成）—— 避免再查 Milvus，节省一次 round-trip
    chunks_preview: List[Dict[str, Any]] = []
    for i, c in enumerate(chunks_in_state[:chunk_limit]):
        text = c.get("content") or ""
        chunks_preview.append({
            "seq": i + 1,
            "chunk_index": c.get("index") or c.get("chunk_index") or i,
            "title_path": c.get("title_path") or "",
            "file_title": c.get("file_title") or "",
            "content_preview": text[:preview_chars] + ("…" if len(text) > preview_chars else ""),
            "char_count": len(text),
        })

    return {
        "item": {
            "pk": item_pk,
            "name": result.get("item_name", ""),
            "category": result.get("item_category", "OTHER"),
            "summary": result.get("item_summary", ""),
        },
        "file_meta": result.get("file_meta") or {},
        "chunks_total": len(chunks_in_state),
        "chunks_preview": chunks_preview,
        "truncated": len(chunks_in_state) > chunk_limit,
        "import_result": result.get("import_result") or {},
        "stats": {
            "before": stats_before,
            "after": stats_after,
            "delta_chunks": stats_after.get("kb_chunks", 0) - stats_before.get("kb_chunks", 0),
            "delta_items": stats_after.get("kb_item_names", 0) - stats_before.get("kb_item_names", 0),
        },
        "elapsed_ms": elapsed_ms,
        "trace_id": result.get("trace_id", ""),
    }


class RollbackReq(BaseModel):
    item_pk: str = Field(..., description="要撤销的 item_pk（来自 preview 返回值 item.pk）")


@app.post("/api/v1/rag/rollback", tags=["RAG 知识库"], summary="撤销一次 preview/import")
def rag_rollback(req: RollbackReq) -> Dict[str, Any]:
    """按 item_pk 联动删除 kb_chunks 和 kb_item_names 中的所有对应记录。"""
    if not req.item_pk:
        raise HTTPException(400, detail="item_pk 不能为空")
    try:
        before = milvus_stats()
        chunks_now = delete_by_item_pk(req.item_pk)
        after = milvus_stats()
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, detail=f"撤销失败: {e}") from e
    return {
        "deleted": True,
        "item_pk": req.item_pk,
        "chunks_deleted": chunks_now,
        "stats_before": before,
        "stats_after": after,
        "note": "stats_after 的 num_entities 可能延迟更新（Milvus 内部统计异步），实际数据已删除，可通过 /api/v1/rag/chunks/{item_pk} 验证。",
    }


@app.get("/api/v1/rag/chunks/{item_pk}", tags=["RAG 知识库"], summary="列出某文档的所有 chunks（预览用）")
def rag_chunks(
    item_pk: str,
    max_chars: int = 200,
    limit: int = 200,
) -> Dict[str, Any]:
    """纯 expr 查询，不跑向量检索。前端用于刷新预览。"""
    max_chars = max(50, min(int(max_chars), 1000))
    limit = max(1, min(int(limit), 1000))
    try:
        rows = list_chunks_by_item_pk(item_pk, max_chars=max_chars)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, detail=f"查询失败: {e}") from e
    rows = rows[:limit]
    return {
        "item_pk": item_pk,
        "total": len(rows),
        "truncated": len(rows) > limit,
        "chunks": rows,
    }


# ============================================================
# 项目管理
# 基础 CRUD/审批：get_store() → 本地 JSON 或芋道/Java（PROJECT_BIZ_BASE_URL）
# AI：parse 文档解析；审批通过后 try_sync_approved_project → Milvus
# ============================================================
@app.post("/api/v1/projects/parse", tags=["项目管理"], summary="上传立项文档并解析为表单字段（AI）")
async def projects_parse(
    file: UploadFile = File(..., description="立项文档 .md/.docx/.xlsx/.pdf/.zip 等"),
    images: Optional[List[UploadFile]] = File(None, description="可选：配套外置图片"),
) -> Dict[str, Any]:
    """解析后不直接入库，仅返回字段供前端确认。支持 Word/Excel/PDF/MD 及文档内嵌图 OCR。"""
    from project_agent.projects.doc_extract import extract_document, is_supported_doc
    from project_agent.projects.md_images import enrich_text_with_images, unpack_zip_doc

    name = file.filename or "document"
    ext = Path(name).suffix.lower()
    allowed = {".md", ".markdown", ".txt", ".pdf", ".docx", ".xlsx", ".xlsm", ".zip"}
    if ext not in allowed:
        if ext in {".doc", ".xls"}:
            raise HTTPException(400, detail=f"暂不支持旧版 {ext}，请另存为 .docx / .xlsx")
        raise HTTPException(
            400,
            detail="仅支持 .md / .docx / .xlsx / .pdf / .txt / .zip",
        )
    raw = await file.read()
    if len(raw) > 20 * 1024 * 1024:
        raise HTTPException(400, detail="文件超过 20MB")

    tmp_dir = Path("./.tmp_uploads")
    tmp_dir.mkdir(exist_ok=True)
    trace = new_trace_id()
    work = tmp_dir / f"{trace}_work"
    work.mkdir(exist_ok=True)
    dest = work / name
    extra_images: List[tuple[str, bytes]] = []
    warnings: List[str] = []
    img_ok = 0
    doc_name = name
    try:
        dest.write_bytes(raw)
        doc_path = dest
        embedded: List[tuple[str, bytes, str]] = []

        if ext == ".zip":
            doc_path, unzip_root = unpack_zip_doc(dest, work / "_unzip")
            doc_name = doc_path.name
            extracted = extract_document(doc_path)
            text = extracted.text
            embedded = list(extracted.images)
            warnings.extend(extracted.warnings)
            base_dirs = [doc_path.parent, unzip_root, work]
        elif is_supported_doc(doc_path):
            extracted = extract_document(doc_path)
            text = extracted.text
            embedded = list(extracted.images)
            warnings.extend(extracted.warnings)
            base_dirs = [work, doc_path.parent]
        else:
            text = load_text_file(doc_path)
            base_dirs = [work, doc_path.parent]

        for mime, ibytes, label in embedded:
            # enrich 接受 (name, bytes)；用 label 当文件名提示
            safe = re.sub(r"[^\w.\-]+", "_", label)[:80] or "embedded.png"
            if not Path(safe).suffix:
                safe += ".png"
            extra_images.append((safe, ibytes))

        for img in images or []:
            iname = img.filename or "image.png"
            if Path(iname).suffix.lower() not in {
                ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp",
            }:
                continue
            ibytes = await img.read()
            if ibytes:
                extra_images.append((iname, ibytes))
                (work / Path(iname).name).write_bytes(ibytes)

        text, img_ok, enrich_warns = enrich_text_with_images(
            text,
            base_dirs=base_dirs,
            extra_images=extra_images,
        )
        warnings.extend(enrich_warns)
        fields, confidence, method = parse_project_from_text(text, filename=doc_name)
        if img_ok:
            method = f"{method}+vision({img_ok})"
    except ValueError as e:
        raise HTTPException(400, detail=str(e)) from e
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, detail=f"解析失败: {e}") from e
    finally:
        try:
            import shutil

            shutil.rmtree(work, ignore_errors=True)
        except Exception:  # noqa: BLE001
            pass

    return {
        "fields": fields.model_dump(),
        "confidence": confidence,
        "method": method,
        "filename": doc_name,
        "images_parsed": img_ok,
        "warnings": warnings,
        "trace_id": get_trace_id(),
    }


@app.get("/api/v1/projects/stats", tags=["项目管理"])
def projects_stats() -> Dict[str, Any]:
    return get_store().stats()


@app.get("/api/v1/projects", tags=["项目管理"])
def projects_list(status: Optional[str] = None, q: Optional[str] = None) -> Dict[str, Any]:
    items = get_store().list(status=status, q=q)
    return {"items": [i.model_dump() for i in items], "total": len(items)}


@app.post("/api/v1/projects", tags=["项目管理"], summary="创建立项草稿")
def projects_create(payload: ProjectCreate) -> Dict[str, Any]:
    try:
        rec = get_store().create(payload)
        return rec.model_dump()
    except Exception as e:  # noqa: BLE001
        logger.exception(f"[Projects] create failed: {e}")
        detail = str(e)
        if "连接" in detail or "Connect" in detail or "10061" in detail or "refused" in detail.lower():
            raise HTTPException(
                503,
                detail=(
                    "项目业务库连不上。请确认 Nest stub 已启动（:48080），"
                    "且 conf/.env 中 PROJECT_BIZ_BASE_URL 指向可达地址（本机 stub 用 http://127.0.0.1:48080）"
                ),
            ) from e
        raise HTTPException(500, detail=f"保存失败: {detail}") from e


@app.put("/api/v1/projects/{project_id}", tags=["项目管理"], summary="更新草稿/驳回项目表单")
def projects_update(project_id: str, payload: ProjectCreate) -> Dict[str, Any]:
    try:
        rec = get_store().update_fields(project_id, payload)
    except KeyError as e:
        raise HTTPException(404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(400, detail=str(e)) from e
    except Exception as e:  # noqa: BLE001
        logger.exception(f"[Projects] update failed: {e}")
        raise HTTPException(500, detail=f"更新失败: {e}") from e
    return rec.model_dump()


@app.get("/api/v1/projects/{project_id}", tags=["项目管理"])
def projects_get(project_id: str) -> Dict[str, Any]:
    rec = get_store().get(project_id)
    if not rec:
        raise HTTPException(404, detail="项目不存在")
    return rec.model_dump()


@app.post("/api/v1/projects/{project_id}/submit", tags=["项目管理"], summary="确认后提交审批")
def projects_submit(project_id: str) -> Dict[str, Any]:
    try:
        rec = get_store().submit(project_id)
    except KeyError as e:
        raise HTTPException(404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(400, detail=str(e)) from e
    return rec.model_dump()


@app.post("/api/v1/projects/{project_id}/review", tags=["项目管理"], summary="审批通过或驳回")
def projects_review(project_id: str, req: ApproveReq) -> Dict[str, Any]:
    try:
        rec = get_store().review(project_id, req)
    except KeyError as e:
        raise HTTPException(404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(400, detail=str(e)) from e

    payload = rec.model_dump()
    # 仅审批通过时同步到 Milvus；失败不回滚审批状态
    if rec.status == ProjectStatus.approved:
        sync_meta = try_sync_approved_project(rec)
        payload.update({
            "rag_synced": bool(sync_meta.get("rag_synced")),
            "rag_item_pk": sync_meta.get("rag_item_pk") or "",
            "rag_error": sync_meta.get("rag_error") or "",
        })
        if sync_meta.get("rag_synced") and sync_meta.get("rag_item_pk"):
            try:
                updated = get_store().set_rag_item_pk(project_id, str(sync_meta["rag_item_pk"]))
                payload = updated.model_dump()
                payload["rag_synced"] = True
                payload["rag_error"] = ""
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[Projects] 回写 rag_item_pk 失败: {e}")
    else:
        payload["rag_synced"] = False
        payload["rag_item_pk"] = rec.rag_item_pk or ""
        payload["rag_error"] = ""
    return payload


# ============================================================
# 代码助手
# ============================================================
class CopilotReq(BaseModel):
    requirement_doc: Optional[str] = Field(None, description="自定义需求文档；不填用默认需求（资产盘点模块）")


class CopilotResp(BaseModel):
    output_dir: str
    steps_done: List[str]
    files: List[Dict[str, Any]]
    total_cost_ms: int
    errors: List[str]


@app.post("/api/v1/copilot/run", tags=["代码助手"], response_model=CopilotResp)
def copilot_run(req: CopilotReq) -> CopilotResp:
    state = run_copilot(requirement_doc=req.requirement_doc)
    out = Path(state.get("output_dir"))
    files: List[Dict[str, Any]] = []
    if out.exists():
        for p in sorted(out.rglob("*")):
            if p.is_file():
                files.append({
                    "path": p.relative_to(out).as_posix(),
                    "size_bytes": p.stat().st_size,
                })
    return CopilotResp(
        output_dir=str(out),
        steps_done=list(state.get("steps_done") or []),
        files=files,
        total_cost_ms=int(state.get("total_cost_ms") or 0),
        errors=list(state.get("errors") or []),
    )


# ============================================================
# SPA 静态资源 + 前端路由 fallback（必须在所有 /api 路由之后）
# ============================================================
def _spa_index() -> FileResponse:
    index = _DIST_DIR / "index.html"
    if not index.is_file():
        raise HTTPException(
            status_code=503,
            detail="前端未构建：请先执行 cd frontend && npm install && npm run build",
        )
    # 禁止缓存入口 HTML，避免重建 dist 后仍引用旧的 /assets/*.css 导致整页无样式
    return FileResponse(
        index,
        media_type="text/html; charset=utf-8",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )


if _DIST_DIR.is_dir():
    _assets = _DIST_DIR / "assets"
    if _assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(_assets)), name="assets")

    @app.get("/", include_in_schema=False)
    def _spa_root() -> FileResponse:
        return _spa_index()

    @app.get("/{full_path:path}", include_in_schema=False)
    def _spa_fallback(full_path: str) -> FileResponse:
        """非 API 路径交给 React Router；存在的静态文件直接返回。"""
        if full_path.startswith("api/") or full_path in {"docs", "redoc", "openapi.json"}:
            raise HTTPException(status_code=404, detail="Not Found")
        candidate = (_DIST_DIR / full_path).resolve()
        try:
            candidate.relative_to(_DIST_DIR.resolve())
        except ValueError as e:
            raise HTTPException(status_code=404, detail="Not Found") from e
        if candidate.is_file():
            return FileResponse(candidate)
        return _spa_index()


def main() -> None:
    """CLI 启动：agent-api 命令"""
    import uvicorn
    uvicorn.run(
        "project_agent.api.server:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.env.lower() == "dev",
        access_log=False,
    )


if __name__ == "__main__":
    main()
