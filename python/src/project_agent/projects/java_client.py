"""
项目库业务 HTTP 客户端（兼容 NestJS / 芋道 CommonResult）

【架构】基础 CRUD/审批走业务服务（推荐 java/_nest-biz-stub/packages/server）；本模块只做协议适配。
AI 解析与 RAG 同步仍在 Python。
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


def _request(method: str, url: str, **kwargs: Any) -> Any:
    """发 HTTP 并 unwrap；连接失败时给出可读错误。"""
    base = _base()
    try:
        with httpx.Client(base_url=base, timeout=float(getattr(get_settings(), "project_biz_timeout", 15) or 15)) as c:
            r = c.request(method, url, **kwargs)
            r.raise_for_status()
            return _unwrap(r.json())
    except httpx.ConnectError as e:
        raise RuntimeError(
            f"无法连接项目业务库 {base}（请确认 Nest stub 已启动，"
            f"本机一般用 http://127.0.0.1:48080）: {e}"
        ) from e
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"业务库 HTTP {e.response.status_code}: {e.response.text[:300]}") from e


class JavaProjectStore:
    """与 ProjectStore 同形的远程实现。"""

    def __init__(self) -> None:
        self.timeout = float(getattr(get_settings(), "project_biz_timeout", 15) or 15)

    def list(self, status: Optional[str] = None, q: Optional[str] = None) -> List[ProjectRecord]:
        params: Dict[str, Any] = {"pageNo": 1, "pageSize": 500}
        if status:
            params["status"] = status
        if q:
            params["q"] = q
        data = _request("GET", "/admin-api/project-agent/project/page", params=params)
        rows = data.get("list") if isinstance(data, dict) else data
        return [_from_java(x) for x in (rows or [])]

    def get(self, project_id: str) -> Optional[ProjectRecord]:
        base = _base()
        try:
            with httpx.Client(
                base_url=base,
                timeout=float(getattr(get_settings(), "project_biz_timeout", 15) or 15),
            ) as c:
                r = c.get("/admin-api/project-agent/project/get", params={"id": project_id})
                if r.status_code == 404:
                    return None
                r.raise_for_status()
                data = _unwrap(r.json())
        except httpx.ConnectError as e:
            raise RuntimeError(
                f"无法连接项目业务库 {base}（请确认 Nest stub 已启动，"
                f"本机一般用 http://127.0.0.1:48080）: {e}"
            ) from e
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
        new_id = _request("POST", "/admin-api/project-agent/project/create", json=body)
        if isinstance(new_id, dict):
            new_id = new_id.get("id") or new_id
        rec = self.get(str(new_id))
        if not rec:
            raise RuntimeError(f"业务库创建成功但无法回读 id={new_id}")
        if parse_confidence is not None:
            rec.parse_confidence = parse_confidence
        _ = status
        _ = created_by
        return rec

    def update_fields(self, project_id: str, payload: ProjectCreate) -> ProjectRecord:
        body = _to_java_body(payload, id_=project_id)
        _request("PUT", "/admin-api/project-agent/project/update", json=body)
        rec = self.get(project_id)
        if not rec:
            raise KeyError(f"项目不存在: {project_id}")
        return rec

    def submit(self, project_id: str) -> ProjectRecord:
        _request("POST", "/admin-api/project-agent/project/submit", params={"id": project_id})
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
        _request("POST", "/admin-api/project-agent/project/review", json=body)
        rec = self.get(project_id)
        if not rec:
            raise KeyError(f"项目不存在: {project_id}")
        return rec

    def set_rag_item_pk(self, project_id: str, rag_item_pk: str) -> ProjectRecord:
        _request(
            "PUT",
            "/admin-api/project-agent/project/rag-item-pk",
            params={"id": project_id, "ragItemPk": rag_item_pk},
        )
        rec = self.get(project_id)
        if not rec:
            raise KeyError(f"项目不存在: {project_id}")
        return rec

    def stats(self) -> Dict[str, int]:
        data = _request("GET", "/admin-api/project-agent/project/stats") or {}
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
