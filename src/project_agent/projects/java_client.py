"""
项目库 Java（芋道）HTTP 客户端

【架构】基础 CRUD/审批走 Java；本模块只做协议适配。
AI 解析与 RAG 同步仍在 Python，不经过此客户端的业务逻辑。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from project_agent.core import get_settings
from project_agent.projects.models import (
    ApproveReq,
    ProjectCreate,
    ProjectRecord,
    ProjectStatus,
)


def _base() -> str:
    return (get_settings().project_biz_base_url or "").rstrip("/")


def enabled() -> bool:
    return bool(_base())


def _unwrap(data: Any) -> Any:
    """兼容芋道 CommonResult {code,data,msg} 与裸 JSON。"""
    if isinstance(data, dict) and "code" in data and "data" in data:
        code = data.get("code")
        if code not in (0, 200, "0", "200"):
            raise RuntimeError(data.get("msg") or f"Java 业务错误 code={code}")
        return data["data"]
    return data


_FIELD_TO_JAVA = {
    "project_code": "projectCode",
    "project_name": "projectName",
    "project_type": "projectType",
    "start_date": "startDate",
    "end_date": "endDate",
    "risk_level": "riskLevel",
    "source_file": "sourceFile",
    "created_by": "createdBy",
    "review_comment": "reviewComment",
    "rag_item_pk": "ragItemPk",
    "created_at": "createTime",
    "updated_at": "updateTime",
    "submitted_at": "submittedAt",
    "reviewed_at": "reviewedAt",
}

_JAVA_TO_FIELD = {v: k for k, v in _FIELD_TO_JAVA.items()}


def _to_java_body(payload: ProjectCreate, *, id_: Optional[str] = None) -> Dict[str, Any]:
    raw = payload.model_dump()
    out: Dict[str, Any] = {}
    for k, v in raw.items():
        out[_FIELD_TO_JAVA.get(k, k)] = v
    if id_:
        out["id"] = id_
    return out


def _from_java(obj: Dict[str, Any]) -> ProjectRecord:
    mapped: Dict[str, Any] = {}
    for k, v in obj.items():
        mapped[_JAVA_TO_FIELD.get(k, k)] = v
    # status 字符串
    st = mapped.get("status") or "draft"
    if isinstance(st, str):
        mapped["status"] = st
    # 时间字段可能是 ISO，直接塞字符串字段
    for tkey in ("created_at", "updated_at", "submitted_at", "reviewed_at"):
        if mapped.get(tkey) is not None:
            mapped[tkey] = str(mapped[tkey]).replace("T", " ")[:19]
    mapped.setdefault("history", [])
    return ProjectRecord.model_validate(mapped)


class JavaProjectStore:
    """与 ProjectStore 同形的远程实现。"""

    def __init__(self) -> None:
        self.timeout = float(getattr(get_settings(), "project_biz_timeout", 15) or 15)

    def _client(self) -> httpx.Client:
        return httpx.Client(base_url=_base(), timeout=self.timeout)

    def list(self, status: Optional[str] = None) -> List[ProjectRecord]:
        params = {}
        if status:
            params["status"] = status
        with self._client() as c:
            r = c.get("/admin-api/project-agent/project/page", params=params)
            r.raise_for_status()
            data = _unwrap(r.json())
        rows = data.get("list") if isinstance(data, dict) else data
        return [_from_java(x) for x in (rows or [])]

    def get(self, project_id: str) -> Optional[ProjectRecord]:
        with self._client() as c:
            r = c.get("/admin-api/project-agent/project/get", params={"id": project_id})
            if r.status_code == 404:
                return None
            r.raise_for_status()
            data = _unwrap(r.json())
        if not data:
            return None
        return _from_java(data)

    def create(
        self,
        payload: ProjectCreate,
        *,
        created_by: str = "申请人",
        parse_confidence: Optional[float] = None,
        status: ProjectStatus = ProjectStatus.draft,
    ) -> ProjectRecord:
        body = _to_java_body(payload)
        with self._client() as c:
            r = c.post("/admin-api/project-agent/project/create", json=body)
            r.raise_for_status()
            new_id = _unwrap(r.json())
        if isinstance(new_id, dict):
            new_id = new_id.get("id") or new_id
        rec = self.get(str(new_id))
        if not rec:
            raise RuntimeError(f"Java 创建成功但无法回读 id={new_id}")
        # parse_confidence 仅 Python 侧展示用；Java 表未建该列时忽略
        if parse_confidence is not None:
            rec.parse_confidence = parse_confidence
        _ = status  # Java 创建固定 draft
        _ = created_by
        return rec

    def update_fields(self, project_id: str, payload: ProjectCreate) -> ProjectRecord:
        body = _to_java_body(payload, id_=project_id)
        with self._client() as c:
            r = c.put("/admin-api/project-agent/project/update", json=body)
            r.raise_for_status()
            _unwrap(r.json())
        rec = self.get(project_id)
        if not rec:
            raise KeyError(f"项目不存在: {project_id}")
        return rec

    def submit(self, project_id: str) -> ProjectRecord:
        with self._client() as c:
            r = c.post("/admin-api/project-agent/project/submit", params={"id": project_id})
            r.raise_for_status()
            _unwrap(r.json())
        rec = self.get(project_id)
        if not rec:
            raise KeyError(f"项目不存在: {project_id}")
        return rec

    def review(self, project_id: str, req: ApproveReq) -> ProjectRecord:
        body = {
            "id": project_id,
            "action": req.action,
            "reviewer": req.reviewer,
            "comment": req.comment,
        }
        with self._client() as c:
            r = c.post("/admin-api/project-agent/project/review", json=body)
            r.raise_for_status()
            _unwrap(r.json())
        rec = self.get(project_id)
        if not rec:
            raise KeyError(f"项目不存在: {project_id}")
        return rec

    def set_rag_item_pk(self, project_id: str, rag_item_pk: str) -> ProjectRecord:
        with self._client() as c:
            r = c.put(
                "/admin-api/project-agent/project/rag-item-pk",
                params={"id": project_id, "ragItemPk": rag_item_pk},
            )
            r.raise_for_status()
            _unwrap(r.json())
        rec = self.get(project_id)
        if not rec:
            raise KeyError(f"项目不存在: {project_id}")
        return rec

    def stats(self) -> Dict[str, int]:
        with self._client() as c:
            r = c.get("/admin-api/project-agent/project/stats")
            r.raise_for_status()
            data = _unwrap(r.json()) or {}
        out = {k: int(v) for k, v in data.items()}
        for s in ("draft", "pending", "approved", "rejected"):
            out.setdefault(s, 0)
        out["total"] = sum(out.get(s, 0) for s in ("draft", "pending", "approved", "rejected"))
        return out


_java_store: Optional[JavaProjectStore] = None


def get_java_store() -> JavaProjectStore:
    global _java_store
    if _java_store is None:
        logger.info(f"[Projects] 使用 Java 业务后端 base={_base()}")
        _java_store = JavaProjectStore()
    return _java_store
