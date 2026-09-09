"""项目持久化：默认本地 JSON；配置 PROJECT_BIZ_BASE_URL 后转发芋道/Java。"""
from __future__ import annotations

import json
import threading
import uuid
from pathlib import Path
from typing import List, Optional, Union

from loguru import logger

from project_agent.projects.models import (
    ApproveReq,
    ProjectCreate,
    ProjectRecord,
    ProjectStatus,
    now_iso,
)

_ROOT = Path(__file__).resolve().parents[3]
_DATA_PATH = _ROOT / "data" / "projects.json"
_lock = threading.Lock()
_store: Optional["ProjectStore"] = None
_repo: Optional[Union["ProjectStore", object]] = None


class ProjectStore:
    def __init__(self, path: Path = _DATA_PATH) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write([])

    def _read(self) -> List[dict]:
        try:
            raw = self.path.read_text(encoding="utf-8")
            data = json.loads(raw or "[]")
            return data if isinstance(data, list) else []
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[Projects] 读取失败: {e}")
            return []

    def _write(self, rows: List[dict]) -> None:
        self.path.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def list(self, status: Optional[str] = None) -> List[ProjectRecord]:
        with _lock:
            rows = self._read()
        items = [ProjectRecord.model_validate(r) for r in rows]
        if status:
            items = [i for i in items if i.status.value == status]
        items.sort(key=lambda x: x.updated_at or x.created_at, reverse=True)
        return items

    def get(self, project_id: str) -> Optional[ProjectRecord]:
        for item in self.list():
            if item.id == project_id:
                return item
        return None

    def create(self, payload: ProjectCreate, *, created_by: str = "申请人",
               parse_confidence: Optional[float] = None,
               status: ProjectStatus = ProjectStatus.draft) -> ProjectRecord:
        ts = now_iso()
        rec = ProjectRecord(
            id=f"prj_{uuid.uuid4().hex[:12]}",
            status=status,
            created_at=ts,
            updated_at=ts,
            created_by=created_by,
            parse_confidence=parse_confidence,
            history=[{"at": ts, "action": "created", "by": created_by, "note": "创建立项草稿"}],
            **payload.model_dump(),
        )
        with _lock:
            rows = self._read()
            rows.append(rec.model_dump())
            self._write(rows)
        return rec

    def update_fields(self, project_id: str, payload: ProjectCreate) -> ProjectRecord:
        with _lock:
            rows = self._read()
            for i, row in enumerate(rows):
                if row.get("id") != project_id:
                    continue
                if row.get("status") not in (ProjectStatus.draft.value, ProjectStatus.rejected.value):
                    raise ValueError("仅草稿或已驳回项目可编辑")
                ts = now_iso()
                row.update(payload.model_dump())
                row["updated_at"] = ts
                hist = list(row.get("history") or [])
                hist.append({"at": ts, "action": "updated", "by": row.get("created_by", "申请人"), "note": "确认/修改表单"})
                row["history"] = hist
                # 驳回后编辑回到草稿
                if row.get("status") == ProjectStatus.rejected.value:
                    row["status"] = ProjectStatus.draft.value
                    hist.append({"at": ts, "action": "reopened", "by": row.get("created_by", "申请人"), "note": "驳回后重新编辑"})
                rows[i] = row
                self._write(rows)
                return ProjectRecord.model_validate(row)
        raise KeyError(f"项目不存在: {project_id}")

    def submit(self, project_id: str) -> ProjectRecord:
        with _lock:
            rows = self._read()
            for i, row in enumerate(rows):
                if row.get("id") != project_id:
                    continue
                if row.get("status") not in (ProjectStatus.draft.value, ProjectStatus.rejected.value):
                    raise ValueError("仅草稿或已驳回项目可提交审批")
                if not (row.get("project_name") or "").strip():
                    raise ValueError("项目名称不能为空")
                ts = now_iso()
                row["status"] = ProjectStatus.pending.value
                row["submitted_at"] = ts
                row["updated_at"] = ts
                row["review_comment"] = ""
                row["reviewer"] = ""
                row["reviewed_at"] = None
                hist = list(row.get("history") or [])
                hist.append({"at": ts, "action": "submitted", "by": row.get("created_by", "申请人"), "note": "提交审批"})
                row["history"] = hist
                rows[i] = row
                self._write(rows)
                return ProjectRecord.model_validate(row)
        raise KeyError(f"项目不存在: {project_id}")

    def review(self, project_id: str, req: ApproveReq) -> ProjectRecord:
        action = (req.action or "").strip().lower()
        if action not in ("approve", "reject"):
            raise ValueError("action 必须是 approve 或 reject")
        with _lock:
            rows = self._read()
            for i, row in enumerate(rows):
                if row.get("id") != project_id:
                    continue
                if row.get("status") != ProjectStatus.pending.value:
                    raise ValueError("仅待审批项目可审批")
                ts = now_iso()
                row["status"] = ProjectStatus.approved.value if action == "approve" else ProjectStatus.rejected.value
                row["reviewer"] = req.reviewer or "审批人"
                row["review_comment"] = req.comment or ""
                row["reviewed_at"] = ts
                row["updated_at"] = ts
                hist = list(row.get("history") or [])
                hist.append({
                    "at": ts,
                    "action": "approved" if action == "approve" else "rejected",
                    "by": row["reviewer"],
                    "note": req.comment or ("通过" if action == "approve" else "驳回"),
                })
                row["history"] = hist
                rows[i] = row
                self._write(rows)
                return ProjectRecord.model_validate(row)
        raise KeyError(f"项目不存在: {project_id}")

    def set_rag_item_pk(self, project_id: str, rag_item_pk: str) -> ProjectRecord:
        """审批同步知识库成功后回写 Milvus item_pk。"""
        with _lock:
            rows = self._read()
            for i, row in enumerate(rows):
                if row.get("id") != project_id:
                    continue
                ts = now_iso()
                row["rag_item_pk"] = rag_item_pk
                row["updated_at"] = ts
                hist = list(row.get("history") or [])
                hist.append({
                    "at": ts,
                    "action": "rag_synced",
                    "by": "system",
                    "note": f"同步知识库 pk={rag_item_pk}",
                })
                row["history"] = hist
                rows[i] = row
                self._write(rows)
                return ProjectRecord.model_validate(row)
        raise KeyError(f"项目不存在: {project_id}")

    def stats(self) -> dict:
        items = self.list()
        return {
            "total": len(items),
            "draft": sum(1 for i in items if i.status == ProjectStatus.draft),
            "pending": sum(1 for i in items if i.status == ProjectStatus.pending),
            "approved": sum(1 for i in items if i.status == ProjectStatus.approved),
            "rejected": sum(1 for i in items if i.status == ProjectStatus.rejected),
        }


def get_local_store() -> ProjectStore:
    """强制使用本地 JSON（演示 / 单测）。"""
    global _store
    if _store is None:
        _store = ProjectStore()
    return _store


def get_store():
    """
    项目库仓储入口：
    - 未配置 PROJECT_BIZ_BASE_URL → 本地 JSON（MVP 演示）
    - 已配置 → Java/芋道 HTTP（基础业务正式实现）
    """
    global _repo
    from project_agent.core import get_settings
    from project_agent.projects.java_client import enabled, get_java_store

    if _repo is not None:
        return _repo
    if enabled():
        _repo = get_java_store()
        logger.info(f"[Projects] backend=java url={get_settings().project_biz_base_url}")
    else:
        _repo = get_local_store()
        logger.info("[Projects] backend=local-json（演示；生产请接芋道 PROJECT_BIZ_BASE_URL）")
    return _repo


def reset_store_cache() -> None:
    """测试或热切换后端时清空缓存。"""
    global _repo, _store
    _repo = None
    _store = None
