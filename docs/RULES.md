# 操作规则（Rules）

> 用途：约束 `project_agent` 两个 Agent 的运行行为与安全边界，是代码实现与演示操作的硬性规则。
> 配套：`docs/说明书.md`（怎么用）、`docs/SKILLS.md`（能力清单）。
> 规则优先级：**安全/合规规则（R0、第二章、第四章）不可绕过**；性能/体验规则为强建议。

---

## 第一章 全局安全规则（R0，强制）

### R0 · 路径穿越防护
- 文件导出（`export_to_excel`）**只能**写入项目根下 `output/` 目录；文件名经 `[a-zA-Z0-9_-]` 白名单清洗 + 时间戳后缀，杜绝 `../../etc/passwd` 类穿越。
- Milvus 表达式 / 查询对特殊字符做 `_escape` 转义，禁止分号拼接注入。

### R0-1 · 数据真实性红线（RAG 知识库 回答 8 条，违反即严重幻觉）
1. **严禁编造**：任何编码对应的库存/金额/人员信息，只能源自 `query_resource_by_code` / `fuzzy_match_resource` 返回或上下文写死的数字。
2. **不知就说不知**：上下文 + 工具均无 → 回答「当前知识库未覆盖」，不得编。
3. **编码须确认**：用户没写完整编码 → 先 `fuzzy_match_resource` 取 Top3 让用户选，不得自行假定。
4. **财务敏感兜底**：集团级数据（全年预算/营收）未在演示中出现 → 明确说明「需连接真实 DW」。
5. **合规原文引用**：命中 FIN 手册合规红线（4.1~4.4）→ 必须显式写「根据《财务模块手册 v1.8 第 4 章 合规红线》第 × 条」。
6. **导出触发条件**：结果 ≥3 条 或 用户明确要导出 → 必须调 `export_to_excel` 并在回答写路径。
7. **工具调用上限 3 轮**：定位 → 取数 → 导出，禁止无限循环（见 R0-2）。
8. **最终回答 Markdown**：开头复述问题，中间分点结论，末尾强制列【来源】= 文档章节 + 工具名。

### R0-2 · 工具调用轮次上限
- RAG 知识库 单次回答内 Function Calling **最多 3 轮**（一轮定位、一轮取数、一轮导出），防止模型无限调工具。

### R0-3 · SQL 注入防护
- Mapper XML 出现 `${` 占位 → 强制替换为 `#{}`（N3 R2 规则自动执行）；字符串拼接改 `@Param` + `#{}`。

### R0-4 · 幂等与去重
- Milvus 写入使用 upsert，同一文件二次导入 `chunk_count` 不增长（幂等）。
- Milvus pk、资源编码在 fuzzy 匹配时按 `code` 去重，避免重复候选。

### R0-5 · LLM 失败兜底
- 任一 LLM 调用异常 → 走节点内置 `_fallback()` 模板，流水线 100% 跑通；日志记 `[xxx] LLM 失败，使用内置 fallback`。

---

## 第二章 意图分类规则（RAG 知识库 N1）

三分类互斥，强制路由：

| 意图 | 定义 | 判定信号 |
| --- | --- | --- |
| `RETRIEVAL` | 纯检索：答案在文档（制度/流程/FAQ） | 「怎么操作」「流程几步」「红线是什么」 |
| `TOOL_FIRST` | 纯查数：答案在业务库，必须调工具 | 出现编码(FS-/HR-EMP-/FIN-*/HR-FIX-) 或具体人名 |
| `MIXED` | 混合：既检索又调工具做对照/计算 | 编码/人名 + 制度比对（如「库存是否合理」） |

补充规则：
- 提到**编码**或**具体人名**（陈昊/林晓雯/赵天宇/郑瑞/王建国/张志远/李欣怡/孙丽华/周敏/刘志强）→ 必归 `TOOL_FIRST`/`MIXED`。
- 提到**导出/下载/表格/Excel/CSV/清单** → 至少含 `export_to_excel` 意图。
- 问**同义词含义**（「存货=库存？」）→ 归 `RETRIEVAL`（制度里有同义词词典章节），**不是** `TOOL_FIRST`。
- Query 改写须把口语/错字/同义词展开为标准术语，利于向量检索（长度 10~50 字最佳）。

---

## 第三章 同义词规则（RAG 知识库 模糊匹配 & 改写）

| 规范词 | 等效变体（命中加权） |
| --- | --- |
| 库存 | 存货 / stock / 库存量 / 现有量 |
| 资产编码 | 编码 / 编号 / code / asset_code |
| 人力资源 | 人力 / hr / 员工 / 人员 |
| 财务 | 财会 / finance / fin |
| 单价 | 价格 / price / 售价 |
| 在职 | 在岗 / 正式 / active |
| 离职 | 离岗 / inactive / 离司 |
| 供应商 | vendor / 供货商 / 供方 |
| 盘点单 | 盘点 / stocktake / inventory |

- 相似度计算：`1 - 编辑距离/maxLen`，同义词命中加权至 ≥0.85。
- fuzzy 入选阈值 `sim ≥ 0.45`；代码助手 模糊匹配阈值默认 `0.6`（Top1 < 0.6 转人工确认，对应 INV-002）。

---

## 第四章 代码助手 代码审查规则（N3，强制）

| 规则 | 级别 | 检查点 | 自动修复 |
| --- | --- | --- | --- |
| R1_NULL | WARN | 空值/参数校验（`@NotNull/@Valid/Objects.requireNonNull`） | 建议补注解 |
| R2_SQLI | ERROR | SQL 注入（`${}` 占位） | 强制改 `#{}` |
| R3_LOCK | WARN | 分布式锁正确释放（tryLock 成功且 unlock 在 finally） | 补 try/finally |
| R4_TX | ERROR | confirm 加 `@Transactional(rollbackFor=Exception.class)` | 自动插入注解 |
| R5_NAME | INFO | 命名：驼峰 + 动宾（importLogic/previewLogic/confirmLogic/fuzzyTopN） | 建议改名 |

- 审查输出 `review_report` 分级（ERROR/WARN/INFO）+ `unfixed_errors` 计数。
- **交付门禁**：`unfixed_errors == 0` 才视为通过（对应交付标准「审查通过才交付」）。

---

## 第五章 权限与异常处理规则（代码助手）

盘点模块统一异常码（6 条），由 `ResultCode.java` 定义，全局 `BizException` + `GlobalExceptionHandler` 组装返回：

| 编码 | 含义 | 级别 | 触发场景 |
| --- | --- | --- | --- |
| INV-001 | Excel 解析失败（空行 >5%） | WARN | 上传文件空行率超 5% |
| INV-002 | 模糊匹配 Top1 < 0.6，需人工选 | INFO | 低相似度行转人工确认 |
| INV-003 | Redisson 锁已持有 | WARN | 同 MD5 5min 内重复导入 |
| INV-004 | 扣减后库存 < 0 | ERROR | `confirm` 任一资产实盘导致负库存 |
| INV-005 | 盘点单状态异常 | ERROR | 状态非 IMPORTED/PREVIEWED 时确认/预览 |
| INV-006 | 权限不足 | WARN | 非 ASSET_MGR/ADMIN 角色调 confirm |

- `confirm` 必须在事务内：`@Transactional(rollbackFor=Exception.class)`，任一 `stock < 0` 全回滚。
- 幂等键：`inv:import:` + 文件 MD5，Redisson 可重入锁，TTL 5min。
- 状态机：`IMPORTED → PREVIEWED → CONFIRMED / REJECTED`（无低相似度行可 IMPORTED 直连 CONFIRMED）。

---

## 第六章 性能与可观测基线（强建议）

- Embedding 首次加载 <60s；同文本二次导入缓存命中 O(1)。
- 检索端到端（含 1 轮工具）<3s；工具 `query_resource_by_code` 响应 <5ms。
- 每行日志带 `trace_id`（loguru + TraceID），便于全链路排错。
- 完整 50 项评估基准见 `README.md`「50 项评估指标」章节。
