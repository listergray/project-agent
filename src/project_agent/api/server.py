"""
FastAPI 统一服务入口（如需查看 HTTP 接口就 `uvicorn project_agent.api.server:app --port 8080`）：
  POST /api/v1/rag/import          → MultipartFile → RAG 知识库 7 节点导入 → {item, chunks}
  POST /api/v1/rag/chat            → {query} → 问答（answer + tool_calls + sources）
  GET  /api/v1/rag/chat/stream     → SSE 流式问答
  POST /api/v1/copilot/run     → {requirement_doc?} → {output_dir, steps_done, files, cost_ms}
  GET  /api/v1/health                → {milvus, redis, mysql, liveness, readiness}
"""
from __future__ import annotations

import json
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

from project_agent.clients import ensure_collections, stats as milvus_stats
from project_agent.core import get_settings, get_trace_id, new_trace_id
from project_agent.rag_kb import PRESET_QUERIES, run_import, run_search
from project_agent.copilot import run_copilot
from project_agent.utils import load_all

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: D401
    try:
        ensure_collections()
        logger.info(f"[API] Server ready on port={settings.port} Milvus stats={milvus_stats()}")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[API] Milvus 未就绪，跳过集合初始化（代码助手 / 工具层仍可用）: {e}")
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
# 演示页面（导航 / 对话 / 流水线）
# ============================================================
_WEB_DIR = Path(__file__).resolve().parent.parent.parent.parent / "web"

if _WEB_DIR.is_dir():
    app.mount("/ui", StaticFiles(directory=str(_WEB_DIR), html=True), name="ui")

    @app.get("/", include_in_schema=False)
    def _index() -> FileResponse:
        """根路径返回导航页（两个 Agent 入口）。"""
        return FileResponse(str(_WEB_DIR / "index.html"))

    @app.get("/chat", include_in_schema=False)
    def _chat() -> FileResponse:
        """RAG 知识库 对话页面（DeepSeek 风）。"""
        return FileResponse(str(_WEB_DIR / "chat.html"))

    @app.get("/pipeline", include_in_schema=False)
    def _pipeline() -> FileResponse:
        """代码助手 流水线可视化页面。"""
        return FileResponse(str(_WEB_DIR / "pipeline.html"))


# ============================================================
# Health / Meta
# ============================================================
@app.get("/api/v1/health", tags=["元信息"])
def health() -> Dict[str, Any]:
    try:
        ms = milvus_stats()
    except Exception as e:  # noqa: BLE001
        ms = {"error": str(e)}
    return {
        "liveness": True,
        "readiness": True,
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


class ChatResp(BaseModel):
    session_id: str
    answer: str
    sources: List[str]
    tool_calls: List[Dict[str, Any]]
    intent: str
    elapsed_ms: int


@app.post("/api/v1/rag/chat", tags=["RAG 知识库"], response_model=ChatResp)
def rag_chat(req: ChatReq) -> ChatResp:
    t0 = time.perf_counter()
    res = run_search(req.query, session_id=req.session_id)
    if res.get("errors"):
        raise HTTPException(status_code=500, detail={"errors": res["errors"]})
    return ChatResp(
        session_id=str(res.get("session_id", "")),
        answer=str(res.get("answer", "")),
        sources=list(res.get("sources") or []),
        tool_calls=list(res.get("tool_calls") or []),
        intent=str(res.get("intent", "MIXED")),
        elapsed_ms=int((time.perf_counter() - t0) * 1000),
    )


async def _chat_stream(req: ChatReq):
    """简易 SSE：先吐元信息 → 再吐 answer 字符。"""
    t0 = time.perf_counter()
    res = run_search(req.query, session_id=req.session_id)
    elapsed = int((time.perf_counter() - t0) * 1000)
    yield "event: meta\ndata: " + json.dumps({
        "session_id": str(res.get("session_id", "")),
        "intent": str(res.get("intent", "")),
        "tool_calls": list(res.get("tool_calls") or []),
        "sources": list(res.get("sources") or []),
        "elapsed_ms": elapsed,
    }, ensure_ascii=False) + "\n\n"
    ans = str(res.get("answer", ""))
    chunk = 3
    for i in range(0, len(ans), chunk):
        piece = ans[i:i + chunk]
        yield "event: token\ndata: " + json.dumps({"text": piece}, ensure_ascii=False) + "\n\n"
    yield "event: done\ndata: {}\n\n"


@app.post("/api/v1/rag/chat/stream", tags=["RAG 知识库"])
async def rag_chat_stream(req: ChatReq) -> StreamingResponse:
    return StreamingResponse(
        _chat_stream(req),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
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
