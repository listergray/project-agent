# Agent 能力清单（Skills）

> 用途：定义 `project_agent` 两个 Agent 对外暴露的能力（工具 / 节点），
> 供「AI 助理广场」接入方、集成测试、以及后续产品化时做能力注册与权限控制参考。
> 配套：`docs/说明书.md`（怎么用）、`docs/RULES.md`（能力调用约束）。

每个 Skill 字段含义：
- **触发**：什么输入/意图会激活该能力
- **输入 / 输出**：参数与返回
- **实现**：对应代码位置
- **限制**：安全/性能/数据边界（强制遵守，详见 RULES.md）

---

## 一、RAG 知识库 Agent

### S1 · 知识检索（RETRIEVAL）
| 项 | 内容 |
| --- | --- |
| 触发 | 用户问制度、流程、FAQ、条款等「答案在文档里」的问题（意图 `RETRIEVAL`） |
| 流程 | 向量召回 Top30 → RRF 融合 Top20 → Rerank 精排 Top5 → 生成回答 |
| 输入 | 自然语言问题（上限 1000 字） |
| 输出 | Markdown 回答 + 来源文档章节列表 |
| 实现 | `rag_kb/nodes.py` 检索图、`utils/text_splitter.py`、`clients/embed_client.py` |
| 限制 | 不得编造文档外数据；合规条款必须引用原文（红线条目见 RULES R0-1） |

### S2 · 编码精确查库（tool: `query_resource_by_code`）
| 项 | 内容 |
| --- | --- |
| 触发 | 用户给出明确编码（FS-* / HR-EMP-* / FIN-INV-* / FIN-PAY-* / HR-FIX-*） |
| 输入 | `asset_code: str`（4~64 字，前缀大小写不敏感） |
| 输出 | `{found, module: ASSET\|HR\|FIN, type, data}` |
| 实现 | `tools/rag_tools.py::query_resource_by_code` |
| 限制 | 数据仅来自内存 Mock 或真实 MySQL；命中失败须提示改用模糊匹配，不得猜测 |

### S3 · 模糊匹配（tool: `fuzzy_match_resource`）
| 项 | 内容 |
| --- | --- |
| 触发 | 编码不全 / 只记得名字 / 用了同义词（存货≈库存、编号≈编码） |
| 输入 | `keyword: str`、`top_k: int=5`、`module: ASSET\|HR\|FIN=None` |
| 输出 | `{candidates:[{similarity, module, type, code, name, data}]}` |
| 实现 | `tools/rag_tools.py::fuzzy_match_resource` + `utils/fuzzy.py`（Levenshtein DP + 同义词加权） |
| 限制 | 相似度阈值 ≥0.45 才入选；同义词词典见 RULES 第三章 |

### S4 · 批量导出（tool: `export_to_excel`）
| 项 | 内容 |
| --- | --- |
| 触发 | 结果 ≥3 条 或 用户明确说「导出/表格/Excel/清单/下载」 |
| 输入 | `rows: List[dict]`、`filename: str`（自动加时间戳防覆盖） |
| 输出 | `{success, filepath, rows_count, columns}`（CSV / UTF-8-BOM，落 `output/`） |
| 实现 | `tools/rag_tools.py::export_to_excel` |
| 限制 | 路径必须落在项目 `output/` 内，禁止穿越到上级目录（RULES R0） |

### S5 · 意图路由与 Query 改写（N1）
| 项 | 内容 |
| --- | --- |
| 触发 | 每次检索前先执行，决定走 S1 / S2 / S3 或组合（意图 `RETRIEVAL`/`TOOL_FIRST`/`MIXED`） |
| 输入 | 原始中文问题（口语/错字/同义词） |
| 输出 | `{intent, rewritten_query, target_modules}` |
| 实现 | `prompts/rag_search_n1_rewrite.txt` + `rag_kb/nodes.py` |
| 限制 | 含编码或具体人名 → 必归 `TOOL_FIRST`/`MIXED`；同义词「是什么」问题归 `RETRIEVAL`（分类规则见 RULES 第二章） |

---

## 二、代码助手 编程提效 Agent

### S10 · 需求拆解（N1）
| 项 | 内容 |
| --- | --- |
| 触发 | 输入自然语言需求文档（默认：资产盘点单导入模块） |
| 输出 | Markdown 设计文档 + 结构化 JSON（interfaces/tables/enums/status_flow/sequence/checklist） |
| 实现 | `copilot/nodes.py::n1_requirement_analyze` + `prompts/copilot_n1_analyze.txt` |
| 限制 | 默认 3 接口 + 6 异常码(INV-001~006) + 状态机；不合规则走 fallback 设计 |

### S11 · 代码生成（N2）
| 项 | 内容 |
| --- | --- |
| 触发 | 拿到 N1 结构化设计 |
| 输出 | 8~13 个文件：Controller/Service/Mapper(.java+.xml)/DTO/ResultCode/Job |
| 实现 | `copilot/nodes.py::n2_code_gen` + `prompts/copilot_n2_codgen.txt` |
| 限制 | Java 17 + Spring Boot 3（`jakarta.*`）；confirm 必须 `@Transactional(rollbackFor=Exception.class)`；Mapper 批量插入用 `#{}`（防注入） |

### S12 · 代码审查与自动重构（N3）
| 项 | 内容 |
| --- | --- |
| 触发 | 拿到 N2 生成的代码 |
| 输出 | `reviewed_files` + `review_report`（ERROR/WARN/INFO 分级，未修复项清单） |
| 实现 | `copilot/nodes.py::n3_code_review_refactor` + `_review_rules()` |
| 限制 | 内置 5 条规则 R1_NULL/R2_SQLI/R3_LOCK/R4_TX/R5_NAME；SQL 注入 `${}` 一律改 `#{}`；ERROR 必须 100% 修复（详见 RULES 第四章） |

### S13 · 单元测试生成（N4）
| 项 | 内容 |
| --- | --- |
| 触发 | 拿到审查后的代码 |
| 输出 | `InventoryServiceTest.java`（9 条）+ `AssetCodeMatcherTest.java`（5 条），JUnit5 + Mockito |
| 实现 | `copilot/nodes.py::n4_unit_test_gen` + `prompts/copilot_n4_testgen.txt` |
| 限制 | 必须用 JUnit5（禁 JUnit4）；至少覆盖 3 个异常码断言 |

### S14 · 接口文档生成（N5）
| 项 | 内容 |
| --- | --- |
| 触发 | 拿到设计 + 审查报告 |
| 输出 | `README-接口文档.md`：模块概述 + 接口请求/响应示例 + 异常码表 + 状态机 + 时序图(Mermaid) |
| 实现 | `copilot/nodes.py::n5_doc_gen` + `prompts/copilot_n5_docgen.txt` |
| 限制 | Mermaid 至少含时序图 + 状态机两种；须附 N3 审查摘要 |

---

## 三、能力注册建议（产品化）

接入「AI 助理广场」时，建议按以下元数据注册：
- `skill_id`：`rag.retrieval` / `rag.query_by_code` / `rag.fuzzy_match` / `rag.export` / `copilot.*`
- `risk_level`：S2/S3/S4 为「读数据」低风险；`export_to_excel` 为「写文件」需审计；代码助手 为「生成代码」需人工复核
- `requires_tool`：S2/S3/S4 需绑定 Function Calling；代码助手 为一次性批量生成
- `fallback`：所有 Skill 均声明无 LLM Key 时的 fallback 行为，保证可用率 100%
