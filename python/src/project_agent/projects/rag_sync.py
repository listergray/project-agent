"""审批通过后：项目 → Markdown → RAG 导入流水线 → Milvus。"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

from project_agent.clients import delete_by_item_pk
from project_agent.core import new_trace_id
from project_agent.projects.models import ProjectRecord, ProjectStatus
from project_agent.rag_kb import run_import


def project_doc_title(rec: ProjectRecord) -> str:
    code = (rec.project_code or "").strip() or rec.id
    name = (rec.project_name or "未命名项目").strip()
    # 控制长度，贴近导入 N5「≤30 字」习惯，同时保持稳定可读
    title = f"立项-{code}-{name}"
    return title[:48]


def project_to_markdown(rec: ProjectRecord) -> str:
    """把已审批项目渲染为可被 RAG 分块检索的 Markdown。"""
    title = project_doc_title(rec)
    lines = [
        f"# {title}",
        "",
        "## 基本信息",
        f"- 项目编号：{rec.project_code or '（无）'}",
        f"- 项目名称：{rec.project_name}",
        f"- 项目类型：{rec.project_type}",
        f"- 项目负责人：{rec.owner or '（未指定）'}",
        f"- 所属部门：{rec.department or '（未指定）'}",
        f"- 业务发起人：{rec.sponsor or '（未指定）'}",
        f"- 计划开始：{rec.start_date or '（未填）'}",
        f"- 计划结束：{rec.end_date or '（未填）'}",
        f"- 预算（元）：{rec.budget}",
        f"- 优先级：{rec.priority}",
        f"- 风险等级：{rec.risk_level}",
        f"- 核心成员：{rec.members or '（未填）'}",
        f"- 审批状态：已通过",
        f"- 审批人：{rec.reviewer or '（无）'}",
        f"- 审批时间：{rec.reviewed_at or rec.updated_at or '（无）'}",
        f"- 业务主键：{rec.id}",
        "",
        "## 项目概述",
        rec.description.strip() or "（无概述）",
        "",
        "## 目标与交付物",
        rec.goals.strip() or "（无）",
        "",
        "## 备注",
        rec.remark.strip() or "（无）",
        "",
        "## 审批意见",
        rec.review_comment.strip() or "（无）",
    ]
    if rec.source_file:
        lines.extend(["", f"## 来源文件", rec.source_file])
    return "\n".join(lines) + "\n"


def sync_approved_project(rec: ProjectRecord) -> Dict[str, Any]:
    """
    将已通过项目同步进 Milvus 知识库。
    若记录上已有 rag_item_pk，先删除旧向量再导入，避免内容变更导致重复条目。
    """
    if rec.status != ProjectStatus.approved:
        raise ValueError(f"仅已通过项目可同步知识库，当前 status={rec.status}")

    old_pk = getattr(rec, "rag_item_pk", None) or None
    if old_pk:
        try:
            deleted = delete_by_item_pk(old_pk)
            logger.info(f"[Projects.RAG] 清理旧向量 pk={old_pk} deleted_chunks={deleted}")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[Projects.RAG] 清理旧向量失败 pk={old_pk}: {e}")

    tmp_dir = Path("./.tmp_uploads")
    tmp_dir.mkdir(exist_ok=True)
    # 文件名稳定，便于审计；内容变化不影响先删后导
    dest = tmp_dir / f"project_{rec.id}_{new_trace_id()[:8]}.md"
    dest.write_text(project_to_markdown(rec), encoding="utf-8")

    try:
        result = run_import(str(dest))
    finally:
        try:
            dest.unlink(missing_ok=True)
        except Exception:  # noqa: BLE001
            pass

    if result.get("errors"):
        raise RuntimeError(f"RAG 导入失败: {result['errors']}")

    item_pk = str(result.get("item_pk") or "")
    return {
        "rag_synced": True,
        "rag_item_pk": item_pk,
        "item_name": result.get("item_name") or project_doc_title(rec),
        "import_result": result.get("import_result") or {},
        "trace_id": result.get("trace_id") or "",
    }


def try_sync_approved_project(rec: ProjectRecord) -> Dict[str, Any]:
    """审批钩子用：失败不抛出，返回 rag_synced 标记。"""
    try:
        return sync_approved_project(rec)
    except Exception as e:  # noqa: BLE001
        logger.exception(f"[Projects.RAG] 同步失败 project_id={rec.id}: {e}")
        return {
            "rag_synced": False,
            "rag_error": str(e),
            "rag_item_pk": getattr(rec, "rag_item_pk", None) or "",
        }
