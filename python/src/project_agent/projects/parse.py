"""从立项文档中解析项目字段（LLM 优先，规则兜底）。"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, Tuple

from loguru import logger

from project_agent.projects.models import ProjectCreate


def _normalize_date_token(val: str) -> str:
    """把 2026年01月01日 / 2026/09/30 / 2026.9.30 规范为 YYYY-MM-DD。"""
    if not val:
        return ""
    m = re.search(r"(20\d{2})\s*[-/年.]\s*(\d{1,2})\s*[-/月.]\s*(\d{1,2})", val)
    if not m:
        return ""
    y, mo, d = m.group(1), int(m.group(2)), int(m.group(3))
    return f"{y}-{mo:02d}-{d:02d}"


_SYSTEM = """你是项目管理助手。请从用户提供的立项/需求文档中提取结构化字段，只返回 JSON，不要解释。
字段定义：
- project_code: 项目编号
- project_name: 项目名称（必填，尽量从标题提取）
- project_type: 研发/实施/运维/预研/其他
- owner: 项目负责人
- department: 所属部门
- sponsor: 业务发起人
- start_date: 计划开始 YYYY-MM-DD（「计划时间」「计划开始」都算开始）
- end_date: 计划结束 YYYY-MM-DD（注意图片/OCR 里标签与日期可能分行）
- budget: 数字预算（元，没有则 0）
- priority: P0/P1/P2
- risk_level: 低/中/高
- members: 核心成员，逗号分隔字符串
- description: 项目概述（2-5 句）
- goals: 目标与交付物
- remark: 备注
文档可能包含「## [图片内容: xxx]」段落，那是截图 OCR 结果，请一并提取，尤其是计划结束日期。
"""


def _rule_parse(text: str) -> Dict[str, Any]:
    """简单键值/标题规则解析，保证无 LLM 也能出草稿。"""
    data: Dict[str, Any] = {
        "project_code": "",
        "project_name": "",
        "project_type": "研发",
        "owner": "",
        "department": "",
        "sponsor": "",
        "start_date": "",
        "end_date": "",
        "budget": 0,
        "priority": "P1",
        "risk_level": "中",
        "members": "",
        "description": "",
        "goals": "",
        "remark": "",
    }

    # 第一行 # 标题作项目名
    for line in text.splitlines():
        m = re.match(r"^#\s+(.+)$", line.strip())
        if m:
            data["project_name"] = m.group(1).strip()
            break
    if not data["project_name"]:
        for line in text.splitlines():
            if line.strip():
                data["project_name"] = line.strip()[:80]
                break

    kv_map = {
        "项目编号": "project_code",
        "编号": "project_code",
        "项目名称": "project_name",
        "名称": "project_name",
        "项目类型": "project_type",
        "类型": "project_type",
        "负责人": "owner",
        "项目负责人": "owner",
        "所属部门": "department",
        "部门": "department",
        "发起人": "sponsor",
        "业务方": "sponsor",
        "赞助人": "sponsor",
        "开始日期": "start_date",
        "计划开始": "start_date",
        "计划时间": "start_date",
        "计划启动": "start_date",
        "结束日期": "end_date",
        "计划结束": "end_date",
        "截止时间": "end_date",
        "预算": "budget",
        "金额": "budget",
        "优先级": "priority",
        "风险": "risk_level",
        "风险等级": "risk_level",
        "成员": "members",
        "核心成员": "members",
        "项目概述": "description",
        "概述": "description",
        "描述": "description",
        "目标": "goals",
        "交付物": "goals",
        "备注": "remark",
    }

    lines = [ln.strip().lstrip("-*·").strip() for ln in text.splitlines()]
    for i, line in enumerate(lines):
        if not line:
            continue
        for cn, key in kv_map.items():
            m = re.match(rf"^{re.escape(cn)}\s*[：:]\s*(.+)$", line)
            if m:
                val = m.group(1).strip()
            else:
                # OCR 常见：标签单独一行，下一行才是值（如「计划结束」+「2026/09/30」）
                if re.match(rf"^{re.escape(cn)}\s*[：:]?\s*$", line):
                    nxt = lines[i + 1] if i + 1 < len(lines) else ""
                    if not nxt or re.match(r"^[\u4e00-\u9fff]{1,8}\s*[：:]?\s*$", nxt):
                        continue
                    val = nxt
                else:
                    continue
            if key == "budget":
                nums = re.findall(r"[\d.]+", val.replace(",", ""))
                data["budget"] = float(nums[0]) if nums else 0
            elif key in ("start_date", "end_date"):
                data[key] = _normalize_date_token(val) or val
            else:
                data[key] = val
            break

    # 日期兜底（按出现顺序：首个→开始，末个不同值→结束）
    dates = re.findall(r"20\d{2}[-/年.]\d{1,2}[-/月.]\d{1,2}", text)
    norm = []
    for d in dates:
        nd = _normalize_date_token(d)
        if nd and nd not in norm:
            norm.append(nd)
    if norm and not data["start_date"]:
        data["start_date"] = norm[0]
    if len(norm) > 1 and not data["end_date"]:
        data["end_date"] = norm[-1]
    elif len(norm) == 1 and data["start_date"] and not data["end_date"]:
        pass

    if not data["description"]:
        # 取前 300 字非空正文
        body = re.sub(r"\s+", " ", text).strip()
        data["description"] = body[:300]

    return data


def _safe_json(raw: str) -> Dict[str, Any]:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        obj = json.loads(raw)
        return obj if isinstance(obj, dict) else {}
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", raw)
        if m:
            try:
                obj = json.loads(m.group(0))
                return obj if isinstance(obj, dict) else {}
            except json.JSONDecodeError:
                return {}
        return {}


def parse_project_from_text(text: str, *, filename: str = "") -> Tuple[ProjectCreate, float, str]:
    """
    返回 (表单数据, 置信度 0~1, 解析方式说明)。
    """
    text = (text or "").strip()
    if not text:
        raise ValueError("文档内容为空，无法解析")

    # 再次清掉残留 data URL，避免占满上下文
    text = re.sub(
        r"data:image/[a-zA-Z0-9.+-]+;base64,[A-Za-z0-9+/=\s]+",
        "[内嵌图片]",
        text,
        flags=re.IGNORECASE,
    )
    clipped = text[:12000]
    method = "rule"
    confidence = 0.55
    merged = _rule_parse(clipped)

    try:
        from project_agent.clients.llm_client import achain

        raw = achain(_SYSTEM, f"文件名: {filename}\n\n文档内容:\n{clipped}", json_mode=True, temperature=0.1)
        llm_data = _safe_json(raw)
        if llm_data:
            for k, v in llm_data.items():
                if k not in merged:
                    continue
                if v is None or v == "":
                    continue
                if k == "budget":
                    try:
                        merged["budget"] = float(v)
                    except (TypeError, ValueError):
                        pass
                else:
                    merged[k] = str(v).strip()
            method = "llm+rule"
            confidence = 0.88
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[Projects] LLM 解析失败，使用规则兜底: {e}")

    merged["source_file"] = filename or merged.get("source_file", "")
    if not (merged.get("project_name") or "").strip():
        merged["project_name"] = (filename or "未命名项目").rsplit(".", 1)[0]

    payload = ProjectCreate.model_validate(merged)
    return payload, confidence, method
