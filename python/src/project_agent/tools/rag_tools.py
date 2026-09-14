"""
RAG Agent 业务工具（Function Calling）

【技能点 · Function-Call / Agent 循环】
  ✅ @tool + Pydantic args_schema：供 N7 按 JSON tool_call 调用
  ✅ 工具：query_resource_by_code / fuzzy_match_resource / export_to_excel /
           query_approved_projects（已审批立项，读业务库）
  ✅ 与 rag_kb.nodes.q_n7_answer_with_tools 组成「思考→选工具→行动→再答」循环（≤3 轮）
  📘 生产替换：将 _ASSET_DB/_HR_DB/_FIN_DB 换成 MySQL/MyBatis 或 Java 微服务 HTTP

本层为纯函数，可脱离 Agent 单测。
"""
from __future__ import annotations

import csv
import html
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from langchain_core.tools import tool
from loguru import logger
from pydantic import BaseModel, Field

from project_agent.core import ROOT_DIR
from project_agent.utils import similarity

# =====================================================================
# RAG 知识库：「企业资源管理平台」模拟数据（资产 / 人力 / 财务 三大模块）
# 讲：真实环境我会把这层替换成 MyBatis Mapper 查 MySQL，现在用内存 Mock 演示，
# 接口签名跟生产保持一致，所以上层业务逻辑完全不用改。
# =====================================================================

class AssetRow(BaseModel):
    """资产表一行（对应 MySQL dim_asset）"""
    code: str = Field(..., description="资产编码，形如 FS-2024-0876")
    name: str = Field(..., description="资产名称")
    category: str = Field(..., description="模块：ASSET/HR/FIN")
    stock: int = Field(..., ge=0, description="库存（数量）")
    unit_price: float = Field(..., ge=0, description="单价（元）")
    amount: float = Field(..., ge=0, description="总价（元）=stock*unit_price")
    owner: str = Field(..., description="责任人")
    status: str = Field(..., description="状态：在用/闲置/维修中/报废")
    supplier: str = Field(..., description="供应商")
    location: str = Field(..., description="存放位置")
    updated_at: str = Field(..., description="最近更新时间 ISO8601")


class HREmployeeRow(BaseModel):
    """人力表一行（对应 MySQL dim_employee）"""
    code: str = Field(..., description="员工工号，形如 HR-EMP-1001")
    name: str = Field(..., description="姓名")
    dept: str = Field(..., description="部门")
    title: str = Field(..., description="岗位")
    level: str = Field(..., description="职级")
    status: str = Field(..., description="在职/离职")
    manager: str = Field(..., description="直属上级")
    entry_date: str = Field(..., description="入职日期")


class FinanceInvoiceRow(BaseModel):
    """财务发票一行（对应 MySQL fct_invoice）"""
    code: str = Field(..., description="发票/单据编码，形如 FIN-INV-2024-001")
    type_: str = Field(..., alias="type", description="发票类型：增值税专票/普票/报销单")
    amount: float = Field(..., ge=0, description="金额（元）")
    payee: str = Field(..., description="收款方")
    payer: str = Field(..., description="付款方")
    period: str = Field(..., description="所属账期，YYYY-MM")
    status: str = Field(..., description="状态：已入账/待审核/已冲销")


# ========== 内存 Mock 数据（3 大模块，够演示 query_resource_by_code 精确 + fuzzy 模糊） ==========
_ASSET_DB: List[AssetRow] = [
    AssetRow(
        code="FS-2024-0876", name="联想ThinkStation K-C2 图形工作站",
        category="ASSET", stock=37, unit_price=12800.0, amount=37*12800.0,
        owner="张志远", status="在用", supplier="联想北京代理",
        location="研发中心A栋3F-305机柜",
        updated_at="2024-12-18T09:23:11+08:00",
    ),
    AssetRow(
        code="FS-2024-0902", name="华为MateBook X Pro 笔记本",
        category="ASSET", stock=156, unit_price=8999.0, amount=156*8999.0,
        owner="李欣怡", status="在用", supplier="华为企业购",
        location="销售部1号楼1F-资产库",
        updated_at="2024-12-20T14:05:42+08:00",
    ),
    AssetRow(
        code="FS-2024-1021", name="戴尔PowerEdge R760 机架服务器",
        category="ASSET", stock=8, unit_price=46800.0, amount=8*46800.0,
        owner="王建国（运维）", status="在用", supplier="戴尔企业直销",
        location="IDC机房A区-R07机架",
        updated_at="2024-12-02T11:40:22+08:00",
    ),
    AssetRow(
        code="FS-2023-0344", name="爱普生L6498 多功能一体机",
        category="ASSET", stock=3, unit_price=3599.0, amount=3*3599.0,
        owner="行政部", status="维修中", supplier="京东企业购",
        location="行政部2F-文印区",
        updated_at="2024-11-28T16:10:00+08:00",
    ),
    AssetRow(
        code="HR-FIX-0044", name="Herman Miller Aeron 人体工学椅",
        category="ASSET", stock=128, unit_price=9600.0, amount=128*9600.0,
        owner="HR 行政采购", status="在用", supplier="Herman Miller 总代",
        location="全办公楼工位（按人分配）",
        updated_at="2024-09-15T10:00:00+08:00",
    ),
]

_HR_DB: List[HREmployeeRow] = [
    HREmployeeRow(
        code="HR-EMP-1001", name="陈昊", dept="研发中心-架构组",
        title="高级后端工程师（Agent 方向）", level="P6",
        status="在职", manager="刘志强（架构总监）",
        entry_date="2021-03-15",
    ),
    HREmployeeRow(
        code="HR-EMP-1023", name="林晓雯", dept="人力资源部-招聘组",
        title="资深招聘专员", level="P5",
        status="在职", manager="周敏（HRBP总监）",
        entry_date="2020-07-01",
    ),
    HREmployeeRow(
        code="HR-EMP-0856", name="赵天宇", dept="财务部-报表组",
        title="报表会计", level="P4",
        status="在职", manager="孙丽华（财务总监）",
        entry_date="2022-08-22",
    ),
    HREmployeeRow(
        code="HR-EMP-0720", name="郑瑞", dept="研发中心-算法组",
        title="算法工程师（NLP）", level="P5",
        status="在职", manager="陈昊",
        entry_date="2023-02-14",
    ),
]

_FIN_DB: List[FinanceInvoiceRow] = [
    FinanceInvoiceRow(
        code="FIN-INV-2024-001", type="增值税专票",
        amount=182600.00, payee="联想（北京）有限公司", payer="本公司-主体A",
        period="2024-12", status="已入账",
    ),
    FinanceInvoiceRow(
        code="FIN-INV-2024-002", type="报销单",
        amount=4820.50, payee="陈昊（员工报销）", payer="本公司-主体A",
        period="2024-12", status="待审核",
    ),
    FinanceInvoiceRow(
        code="FIN-INV-2024-003", type="增值税普票",
        amount=374400.00, payee="戴尔（中国）有限公司", payer="本公司-主体A",
        period="2024-11", status="已入账",
    ),
    FinanceInvoiceRow(
        code="FIN-PAY-2024-117", type="付款单",
        amount=140250.00, payee="华为技术有限公司", payer="本公司-主体A",
        period="2024-12", status="已入账",
    ),
]

# 把所有资源拉平成「展示文本 → payload」以便 fuzzy 搜索
def _all_resources() -> List[tuple[str, dict]]:
    out: list[tuple[str, dict]] = []
    for r in _ASSET_DB:
        out.append((f"{r.code} {r.name}", {"module": "ASSET", "type": "asset",
                                           "code": r.code, "name": r.name,
                                           "data": r.model_dump()}))
    for r in _HR_DB:
        out.append((f"{r.code} {r.name} {r.title}",
                    {"module": "HR", "type": "employee",
                     "code": r.code, "name": r.name,
                     "data": r.model_dump()}))
    for r in _FIN_DB:
        out.append((f"{r.code} {r.type_} {r.payee}",
                    {"module": "FIN", "type": "invoice",
                     "code": r.code, "name": f"{r.type_}-{r.payee}",
                     "data": r.model_dump(by_alias=True)}))
    return out


# =====================================================================
# 工具 1：query_resource_by_code（按"编码"精确查库）—— 设计文档第一条
# =====================================================================
class QueryResourceByCodeArgs(BaseModel):
    asset_code: str = Field(
        ..., min_length=4, max_length=64,
        description="要查询的资源编码，例如 FS-2024-0876、HR-EMP-1001、FIN-INV-2024-001。"
                    "支持 ASSET / HR / FIN 三大模块。前缀匹配不区分大小写。",
    )


@tool(args_schema=QueryResourceByCodeArgs)
def query_resource_by_code(asset_code: str) -> dict:
    """
    【规格固定工具名 - 资产/人力/财务编码精确查询】
    给定一个资源编码（资产编码 / 员工工号 / 财务单据编码），
    从「企业资源管理平台」主表中查回唯一一条完整记录。
    适用于：用户明确说出编码、或在上一轮对话里已经确定了编码的场景。
    返回字段：{found: bool, module: ASSET|HR|FIN, type, data: {...}}
    """
    code = (asset_code or "").strip().upper()
    logger.info(f"[Tool.query_resource_by_code] input_code={code}")
    t0 = time.perf_counter()

    hit: Optional[dict] = None
    for r in _ASSET_DB:
        if r.code.upper() == code:
            hit = {"found": True, "module": "ASSET", "type": "asset", "data": r.model_dump()}
            break
    if not hit:
        for r in _HR_DB:
            if r.code.upper() == code:
                hit = {"found": True, "module": "HR", "type": "employee", "data": r.model_dump()}
                break
    if not hit:
        for r in _FIN_DB:
            if r.code.upper() == code:
                hit = {"found": True, "module": "FIN", "type": "invoice",
                       "data": r.model_dump(by_alias=True)}
                break
    if not hit:
        hit = {"found": False, "module": "", "type": "",
               "data": {}, "hint": "未命中，建议检查编码或改用 fuzzy_match_resource 模糊匹配"}
    hit["cost_ms"] = int((time.perf_counter() - t0) * 1000)
    logger.info(f"[Tool.query_resource_by_code] done found={hit['found']} cost={hit['cost_ms']}ms")
    return hit


# =====================================================================
# 工具 2：fuzzy_match_resource（编辑距离模糊匹配）—— 设计文档第二条
# =====================================================================
class FuzzyMatchResourceArgs(BaseModel):
    keyword: str = Field(
        ..., min_length=1, max_length=128,
        description="模糊匹配的关键词，可以是编码片段、资源名称、人名、供应商、"
                    "同义词（例如库存/stock/存货、资产编码/编号）。",
    )
    top_k: int = Field(5, ge=1, le=20, description="返回 TopK 个候选。默认 5。")
    module: Optional[str] = Field(
        None, pattern=r"^(ASSET|HR|FIN)$",
        description="可选：限定在 ASSET/HR/FIN 某一个模块内搜，提升召回率。",
    )


@tool(args_schema=FuzzyMatchResourceArgs)
def fuzzy_match_resource(keyword: str, top_k: int = 5, module: Optional[str] = None) -> dict:
    """
    【规格固定工具名 - 编辑距离模糊匹配】
    当用户说的编码不太确定（比如只记得部分）、或只记得资产/员工/单据的名字、
    或用了同义词（比如"存货"而不是"库存"、"编号"而不是"编码"）时，
    用 Levenshtein 编辑距离 + 同义词加权做 TopK 模糊匹配。
    返回：{keyword, top_k, candidates:[{similarity, module, type, code, name, data}]}
    """
    logger.info(f"[Tool.fuzzy_match_resource] keyword={keyword!r} top_k={top_k} module={module}")
    t0 = time.perf_counter()
    pool = _all_resources()
    if module:
        pool = [(t, p) for (t, p) in pool if p["module"] == module]

    # 多字段打分：姓名 / 编码 / 组合展示串取 max，避免短关键词匹配长串时相似度被稀释
    scored: list[tuple[float, dict]] = []
    seen_codes: set[str] = set()
    for display, payload in pool:
        code = str(payload.get("code") or "")
        if code in seen_codes:
            continue
        name = str(payload.get("name") or "")
        sim = max(
            similarity(keyword, name),
            similarity(keyword, code),
            similarity(keyword, display),
        )
        if sim >= 0.45:
            scored.append((sim, payload))
            seen_codes.add(code)
    scored.sort(key=lambda x: x[0], reverse=True)
    matched = scored[:max(1, top_k)]
    candidates: list[dict] = []
    for sim, payload in matched:
        candidates.append({
            "similarity": round(float(sim), 3),
            "module": payload["module"],
            "type": payload["type"],
            "code": payload["code"],
            "name": payload["name"],
            "data": payload["data"],
        })
    res = {
        "keyword": keyword,
        "module_filter": module,
        "candidates": candidates,
        "cost_ms": int((time.perf_counter() - t0) * 1000),
    }
    logger.info(f"[Tool.fuzzy_match_resource] done candidates={len(candidates)} cost={res['cost_ms']}ms")
    return res


# =====================================================================
# 工具 3：export_to_excel（设计文档第三条，EasyExcel 对应 Python openpyxl）
# =====================================================================
class ExportToExcelArgs(BaseModel):
    rows: List[dict] = Field(
        ..., min_length=1,
        description="要导出的数据行数组，每个元素是一个 JSON 对象（字段名会自动转成列标题）。",
    )
    filename: str = Field(
        "export", min_length=1, max_length=120,
        description="导出文件名（不含 .xlsx 后缀）。系统会自动加时间戳防止覆盖。",
    )


@tool(args_schema=ExportToExcelArgs)
def export_to_excel(rows: List[dict], filename: str = "export") -> dict:
    """
    【规格固定工具名 - 多线程/批量导出 Excel】
    把查询结果（多条 rows）导出为 .xlsx 文件保存在 output/ 目录下。
    返回：{success, filepath, rows_count, columns}，可以直接给用户下载路径。
    """
    logger.info(f"[Tool.export_to_excel] rows={len(rows)} filename={filename!r}")
    t0 = time.perf_counter()

    # 输出目录：项目根下 output/，打开就能看
    out_dir = ROOT_DIR / "output"
    out_dir.mkdir(exist_ok=True)
    safe_name = "".join(c for c in filename if c.isalnum() or c in "-_") or "export"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_path = out_dir / f"{safe_name}_{ts}.csv"  # MVP 用 CSV（Excel 直接打开 + 零依赖）

    # 取所有列（保持字典插入顺序，rows 里第一行的列作为主列，后面行补齐）
    columns: List[str] = []
    for r in rows:
        for k in r.keys():
            if k not in columns:
                columns.append(k)

    def _flatten(obj):
        """嵌套 dict/list → 字符串化，避免 CSV 里出现 {dict}"""
        if isinstance(obj, (dict, list)):
            import json
            return json.dumps(obj, ensure_ascii=False, default=str)
        return "" if obj is None else str(obj)

    with full_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        for r in rows:
            w.writerow({c: _flatten(r.get(c)) for c in columns})

    res = {
        "success": True,
        "filepath": str(full_path.resolve()),
        "filename": full_path.name,
        "rows_count": len(rows),
        "columns": columns,
        "cost_ms": int((time.perf_counter() - t0) * 1000),
        "note": "为零依赖导出使用 CSV（UTF-8-BOM，Excel 双击直接打开不乱码）；"
                "生产环境已切换 EasyExcel/OpenPyXL + 压缩 + 分片下载。",
    }
    logger.info(
        f"[Tool.export_to_excel] ok file={res['filename']} "
        f"rows={res['rows_count']} cols={len(columns)} cost={res['cost_ms']}ms"
    )
    return res


# =====================================================================
# 工具 4：query_approved_projects（已审批立项，读业务真相源）
# =====================================================================
class QueryApprovedProjectsArgs(BaseModel):
    keyword: str = Field(
        "",
        max_length=128,
        description="可选关键词，匹配项目名称/编号/负责人/部门；空则返回最近审批通过的项目。",
    )
    limit: int = Field(5, ge=1, le=20, description="返回条数，默认 5。")


@tool(args_schema=QueryApprovedProjectsArgs)
def query_approved_projects(keyword: str = "", limit: int = 5) -> dict:
    """
    【已审批立项查询】当用户问「最新审批通过的项目」「已立项有哪些」「某负责人/部门的项目」时使用。
    直接读取项目管理库中 status=approved 的记录（按审批/更新时间倒序），不是向量库模糊搜。
    返回：{total, keyword, projects:[{id, project_code, project_name, owner, department, budget, ...}]}
    """
    from project_agent.projects import get_store

    logger.info(f"[Tool.query_approved_projects] keyword={keyword!r} limit={limit}")
    t0 = time.perf_counter()
    items = get_store().list(status="approved")
    kw = (keyword or "").strip().lower()
    if kw:
        def _hit(p) -> bool:
            blob = " ".join([
                p.project_code or "",
                p.project_name or "",
                p.owner or "",
                p.department or "",
                p.sponsor or "",
                p.members or "",
                p.description or "",
            ]).lower()
            return kw in blob
        items = [p for p in items if _hit(p)]
    # list() 已按 updated_at 倒序；再按 reviewed_at 优先
    items = sorted(
        items,
        key=lambda p: p.reviewed_at or p.updated_at or p.created_at,
        reverse=True,
    )[: max(1, limit)]
    projects = []
    for p in items:
        projects.append({
            "id": p.id,
            "project_code": p.project_code,
            "project_name": p.project_name,
            "project_type": p.project_type,
            "owner": p.owner,
            "department": p.department,
            "budget": p.budget,
            "priority": p.priority,
            "risk_level": p.risk_level,
            "start_date": p.start_date,
            "end_date": p.end_date,
            "reviewed_at": p.reviewed_at,
            "reviewer": p.reviewer,
            "description": (p.description or "")[:200],
            "rag_item_pk": p.rag_item_pk or "",
        })
    res = {
        "total": len(projects),
        "keyword": keyword,
        "projects": projects,
        "cost_ms": int((time.perf_counter() - t0) * 1000),
        "note": "数据来自立项审批库（已通过）；细节语义问答可再结合知识库检索。",
    }
    logger.info(f"[Tool.query_approved_projects] done total={res['total']} cost={res['cost_ms']}ms")
    return res


# 导出给上层使用
RAG_TOOLS = [
    query_resource_by_code,
    fuzzy_match_resource,
    export_to_excel,
    query_approved_projects,
]
RAG_TOOLS_BY_NAME = {t.name: t for t in RAG_TOOLS}

__all__ = [
    "RAG_TOOLS",
    "RAG_TOOLS_BY_NAME",
    "query_resource_by_code",
    "fuzzy_match_resource",
    "export_to_excel",
    "query_approved_projects",
    "_ASSET_DB",
    "_HR_DB",
    "_FIN_DB",
]
