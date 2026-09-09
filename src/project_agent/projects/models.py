"""项目字段与审批状态模型。"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    draft = "draft"          # 草稿（确认中）
    pending = "pending"      # 待审批
    approved = "approved"    # 已通过
    rejected = "rejected"    # 已驳回


class ProjectCreate(BaseModel):
    """立项表单字段（人工录入 / 文件解析后确认）。"""

    project_code: str = Field("", description="项目编号，如 PRJ-2026-001")
    project_name: str = Field(..., min_length=1, max_length=200, description="项目名称")
    project_type: str = Field("研发", description="项目类型：研发/实施/运维/预研/其他")
    owner: str = Field("", description="项目负责人")
    department: str = Field("", description="所属部门")
    sponsor: str = Field("", description="业务发起人 / 赞助人")
    start_date: str = Field("", description="计划开始日期 YYYY-MM-DD")
    end_date: str = Field("", description="计划结束日期 YYYY-MM-DD")
    budget: float = Field(0, ge=0, description="预算金额（元）")
    priority: str = Field("P1", description="优先级：P0 / P1 / P2")
    risk_level: str = Field("中", description="风险等级：低 / 中 / 高")
    members: str = Field("", description="核心成员，逗号分隔")
    description: str = Field("", description="项目概述")
    goals: str = Field("", description="目标与交付物")
    source_file: str = Field("", description="来源文件名（解析时自动填充）")
    remark: str = Field("", description="备注")


class ProjectRecord(ProjectCreate):
    id: str
    status: ProjectStatus = ProjectStatus.draft
    created_at: str = ""
    updated_at: str = ""
    submitted_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    reviewer: str = ""
    review_comment: str = ""
    created_by: str = "申请人"
    parse_confidence: Optional[float] = None
    rag_item_pk: Optional[str] = Field(None, description="同步到 Milvus 后的 item_pk")
    history: List[dict] = Field(default_factory=list)


class ApproveReq(BaseModel):
    action: str = Field(..., description="approve | reject")
    reviewer: str = Field("审批人", max_length=64)
    comment: str = Field("", max_length=1000)


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
