"""
代码助手 状态 + 默认需求文档（需求文档里写的「资产盘点单导入 + 模糊匹配 + 库存扣减」模块）
设计说明：我给 代码助手 一个 2~3 页的自然语言需求文档，经过 5 节点流水线后，
能在 output/ 目录产出 8~12 个真实可用的 Java/XML/MD 文件，打开 output 目录直接讲。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, TypedDict

DEFAULT_REQUIREMENT = """
【项目名称】企业资源管理平台 - 资产盘点单导入模块（STAR 案例）

【场景 S】
集团资产年度盘点（2024-12-25 起）。资产管理员从仓库拿 PDA 扫码盘点，
数据以 Excel 形式回流到运营端。旧系统每年盘点靠人工核对 Excel → 编码查库 →
手工扣库存，一个部门要 2 周，编码对不上时要反复发邮件，经常出错。

【任务 T】工期 2 周，要交付：
1. 后端 3 个 REST 接口（Spring Boot 3 + Java 17 + MyBatis-Plus + MySQL 8）
   (a) POST /asset/inventory/importExcel  — EasyExcel 批量导入（支持 1 万行级）
   (b) POST /asset/inventory/preview      — 预览差异，前端展示"模糊匹配 Top5 弹窗"
   (c) POST /asset/inventory/confirm      — 确认扣减库存（避免重复扣）
2. 1 个 Spring Scheduled 定时任务：每天 03:00 生成《昨日盘点差异汇总》CSV
3. 2 个前端页面（Vue 3 + Element Plus）：盘点单导入页、差异确认页
4. 代码必须可编译 + 关键类有 JUnit5 单元测试（正常/异常/边界各 3 条）

【技术栈约束 A】
- 后端：Spring Boot 3.2.x / Java 17 / MyBatis-Plus 3.5.5 / Swagger OpenAPI 3 / HikariCP / Redisson
- 编码模糊匹配：Levenshtein 编辑距离 + 同义词热加载（"库存/存货/stock"、"资产编码/编号/code"等）
- 模糊匹配阈值 0.6；低于阈值的编码前端弹窗让用户手动选择 Top5 候选
- 防止重复导入：每一张 Excel 用 Excel 文件 MD5 做分布式锁键（Redisson RLock），
  TTL 5 分钟，"持有锁的线程才允许写库"（避免用户连点两次按钮）
- 扣减库存必须在同一个 DB 事务里；盘点单状态机：IMPORTED(已导入) → PREVIEWED(待确认) → CONFIRMED(已扣减) / REJECTED(差异驳回)
- 异常码（ResultCode）统一枚举：
    INV-001 Excel 解析失败（空行超 5%）
    INV-002 资产编码模糊匹配 Top1 相似度 < 0.6（需要用户选）
    INV-003 Redisson 锁已持有，请 5 分钟后再试（防重复导入）
    INV-004 扣减后库存 < 0，拒绝扣减
    INV-005 盘点单状态异常，无法确认
    INV-006 权限不足，请联系资产管理员

【核心业务流程】
1. 用户上传 Excel（列：资产编码<或近似编码>、实盘数量、库位、盘点人、备注）
2. importExcel：
   (a) 计算文件 MD5 → Redisson tryLock；失败返回 INV-003
   (b) EasyExcel 解析 → 空行占比 >5% → INV-001
   (c) 对每行"近似编码"跑 Levenshtein 与同义词词典，记录 Top1 相似度 + Top5 候选
   (d) 行级结果写 t_inventory_import；表头写 t_inventory_sheet；状态 IMPORTED
   (e) 返回 sheet_id + 总行数 + Top1 相似度 < 0.6 的行数（需人工确认）
3. preview(sheet_id)：读 sheet + 所有 import 行 → 返回
   "应盘/实盘/差异数 + 每一行的 Top5 候选编码 + 名称 + 相似度"
4. confirm(sheet_id, Map<行ID, 资产编码> 人工修正结果)：
   (a) 状态校验：必须 IMPORTED / PREVIEWED，否则 INV-005
   (b) 应用人工修正后的编码，组装"编码 → 库存变化 = 系统当前数 - 实盘数"
   (c) 事务内：①写 t_inventory_sheet=CONFIRMED ②逐行 UPDATE t_asset stock = stock - diff
   (d) 任何一行 diff 导致 stock<0 → 全事务回滚 → 返回 INV-004
   (e) 记录一条操作日志 t_audit_log
5. 每日 03:00 job：扫描昨天 CONFIRMED 的 sheet，汇总"部门/编码/差异数" → export CSV 到文件系统
   （生产推到 MinIO + 发邮件给资产管理员）

【交付检查清单 R】
8 个工作日内交付（压缩 40% 工期，原计划 14 天）。关键交付物：
□ InventoryController.java（3 接口 + Swagger 注解 + 参数校验 @Valid）
□ InventoryService.java（含 importLogic、previewLogic、confirmLogic 三个核心方法 + @Transactional）
□ AssetCodeMatcher.java（Levenshtein 编辑距离 + 同义词词典类）
□ InventoryImportRowMapper.java + InventoryImportMapper.xml（批量导入 SQL）
□ InventoryDiffJob.java（Scheduled 定时任务）
□ ResultCode.java（异常码枚举 6 条）
□ InventoryServiceTest.java（JUnit5：正常/异常/边界 3 条 × 3 方法 = 9 条）
□ AssetCodeMatcherTest.java（JUnit5：编辑距离 + 同义词 + 阈值 3 条 + 2 边界 = 5 条）
□ README-接口文档.md（3 接口请求/响应示例 + 时序图 Mermaid + 状态机说明）
合计：至少 9 个文件。单测覆盖率（Cobertura/Jacoco）目标 65%。
"""


class CopilotState(TypedDict, total=False):
    # N1 需求拆解输出
    requirement_doc: str
    design_doc: str                       # Markdown 设计文档（N1 输出，约 800~1500 字）
    design_structured: Dict[str, Any]     # 结构化设计（接口、表、枚举、时序，便于后续代码生成精准取字段）

    # N2 代码生成输出
    generated_files: Dict[str, str]       # {相对路径: 文件内容}

    # N3 审查重构输出
    reviewed_files: Dict[str, str]        # 审查并修复后的文件
    review_report: List[Dict[str, Any]]   # 审查问题清单：[{file,level,issue,fix,line_range}]

    # N4 单测输出
    test_files: Dict[str, str]            # {相对路径: 测试类内容}

    # N5 文档输出
    api_doc_md: str                       # 最终 README-接口文档.md 内容（含 Mermaid 图）

    # 全局
    output_dir: str                       # 本次运行的落盘目录（绝对路径）
    steps_done: List[str]                 # 完成步骤 ['N1','N2',...]
    errors: List[str]
    trace_id: str
