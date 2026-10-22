# project_agent 工作指引

## 项目定位和共享上下文

- 用户将 `project_agent` 定位为个人所有项目的整合入口。原有 RAG、代码助手和企业立项演示是其中的模块。
- 三个相关项目：`E:\ai-pro\project_agent`（统一入口）、`E:\ai-pro\sihuo`（接私活团队与业务资料）、`D:\qclaw\animation-pro`（抖音视频制作）。
- 本工作区共享总览为 `E:\ai-pro\project_agent\PROJECT_MAP.md`。首次处理本项目任务、讨论跨项目关系或继续整合工作时，先读取其项目职责、连接状态与当前待办，再按任务读取相关源码。
- “私活”“接单团队”对应 sihuo；“视频制作”“生成视频”对应 animation-pro；“统一入口”“抖音发布”“项目整合”对应 project_agent。含糊的业务要求先结合总览和当前代码判断。
- sihuo 接入方案见 `E:\ai-pro\project_agent\docs\SIHUO_INTEGRATION_PLAN.md`。它是实施建议，状态应与实际完成情况分开记录。

## 按模块读取现有资料

- 统一门户：`java/ruoyi-react/react-ui/src/pages/Portal/Home/index.tsx`、`config/routes.ts`、`src/pages/Subsystem/`。
- 抖音发布：`python/douyin-auto/README.md` 与 `python/douyin-auto/app/`。输入来自 animation-pro 的成片、标题和封面。
- RAG、代码助手、原有项目管理：先读 `agent.md`、`docs/ARCHITECTURE.md`，涉及业务约束时读 `docs/RULES.md`，联调项目管理时读 `docs/PM_LOCAL_DEV.md`。
- `agent.md` 中的“主包只改 python/src/project_agent/”属于原有 Python Agent 模块的工作指引；涉及门户或其他子系统时，以用户任务范围和相应模块为准。保留其中仍适用的技术约束，不把旧的双 Agent 定位当成整个仓库的唯一职责。
- 读取外部项目时，遵守目标目录适用的 `AGENTS.md` 和更具体的子目录规则。不要把 sihuo 的员工配置当成已经接入网页后台的执行服务。

## 实施与交接

- 保留已有用户修改；只处理当前任务涉及的文件。三个项目保持现有目录，业务整合不默认意味着复制或合并全部源码。
- 中文文件使用 UTF-8；源码及配置沿用现有 UTF-8 无 BOM 约定。
- 发生行为变更时，运行对应模块的必要验证；纯上下文文档修改检查路径、内容和规则一致性即可。
- 项目关系、对外接口、成片交接约定或接入进度改变后，在同一次交付中更新共享总览的相关段落、核验日期和变更记录。
- 总览区分“用户说明”“代码/文件核实”“运行验证”“方案/待确认”。没有实际执行的发布、员工调度、部署和验收不得写成已完成。
- 会话需要连续工作的结论、剩余事项和证据路径写入总览或对应方案；不依赖其他会话完整聊天记录自动出现。
- 业务凭据、客户敏感内容和浏览器登录资料不进入共享上下文。读取配置时只取任务需要的非敏感项。
