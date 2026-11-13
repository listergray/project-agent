# 个人项目总览

维护位置：`E:\ai-pro\project_agent\PROJECT_MAP.md`  
核验日期：2026-11-10（Asia/Shanghai；twlmac 局域网地址改为 `192.168.1.177`。此前运行事实保留各自原核验日期）
用途：供 project_agent、sihuo、animation-pro 的新会话快速了解项目职责、已存在的连接和下一步工作。详细业务材料留在所属项目。

## 1. 项目职责

| 项目 | 本地目录 | 用户定位 | 当前核验情况 |
| --- | --- | --- | --- |
| project_agent | `E:\ai-pro\project_agent` | 个人所有项目的整合入口 | 有统一门户、项目管理、RAG/代码助手、抖音发布等多个模块；旧 README 和 agent.md 主要描述原有双 Agent 演示 |
| animation-pro | `D:\qclaw\animation-pro` | 为抖音账号制作视频 | 有技术栈 EP 系列目录、制作脚本、成片与标题/封面交付约定，也有独立视频支线 |
| sihuo | `E:\ai-pro\sihuo` | 接软件、网站和小程序开发私活 | 有员工配置、项目资料、工作室网站与获客素材；接入统一门户尚待实施 |

“视频生成”对应 animation-pro；“抖音发布”“统一管理”对应 project_agent；“私活”“接单团队”对应 sihuo。当前总览聚焦这三个项目，不代表 project_agent 只包含这些模块。

## 2. 关系和证据等级

```text
animation-pro ── 成片 + 同目录标题/封面 ──> project_agent/python/douyin-auto ──> 抖音
                                       └──────> project_agent/python/xhs-auto ──> 小红书
                                                   ↑
                                  统一门户 /subsystem/douyin 、 /subsystem/xhs

sihuo ── 待实施：私活入口、资料索引、需求与交付管理 ──> project_agent
```

- **用户说明**：project_agent 目前能够把 animation-pro 生成的视频发布到抖音；下一步要接入 sihuo。
- **本次文件/代码核实**：存在视频扫描、发布接口和门户入口；发布服务配置的 `VIDEO_DIR` 指向 `D:\qclaw\animation-pro`。仅提取了这一项配置，不在总览保存凭据。
- **共享上下文建立时的运行验证**：当时未启动服务、未操作登录、未发布视频、未查询线上发布结果，不据此推断某集已发布。后续发布修复的服务核验另记于下方。
- **方案状态**：sihuo 接入建议见第 5 节和 `docs/SIHUO_INTEGRATION_PLAN.md`，尚未实施业务接入。
- **2026-10-18 封面与排队修复**：EP36 的多次尝试被本地封面检查拦截；09:36、09:46 的失败截图已有双封面且抖音提示检测通过。已改为限定横竖区域、等待已加载预览连续稳定，并保存检测证据；发布改为 FIFO 等待浏览器、优先于保活，同一集复用活跃任务。初版 17 项离线回归通过；用户后续发起的 EP36/37/38 任务均运行通过封面检测。详见 `docs/DOUYIN_FAILURE_ANALYSIS.md`。
- **2026-10-18 发布结束识别与只读核验**：EP36 提交后原流程没有确认结束，浏览器关闭时清理异常又覆盖业务结果。已增加作品 ID/成功提示/对应作品状态确认、返回空上传页后的只读核对、90 秒普通等待及持续刷新；未确认提交以 `NEEDS_REVIEW` 结束并阻止重复发布，页面可“核对结果”。29 项离线回归及追加匹配检查通过；10:23 已加载最终修复，健康接口 `publishConfirmation=submission-evidence`、数据库正常。10:21 已只读查到 EP36 对应作品“已发布”并修正本地成功记录，10:24 的匹配行截图再次核实其平台发布时间为 10:07；两次管理页截图亦显示 EP37/38 已发布。本会话没有重新上传或发布；简介与定位读回验收仍待后续。

- 2026-11-08 13:46（启动与网络复核）：frpc、nginx、`:3000` 原型、`:8000` 若依前端、`:8080` 旧 Agent、`:8088` 若依后端、`:48080` Nest、`:12400` 闲鱼、`:12500` 抖音、`:12600` 小红书、`:18001` 人生指南前端、`:18002` 人生指南 API、`:9080` 网关均已监听。若依根路径、闲鱼公开健康接口、抖音/小红书健康接口、人生指南健康接口和网关均返回 200；抖音、小红书及人生指南健康结果确认 MySQL 正常。此前本机连接 `twlmac:3306` 时，系统一度将目标选到 OneXrayTun，TCP 表面建立但未收到 MySQL 握手；随后同一目标自动恢复为 WLAN 路由，指定/未指定网卡均收到 MySQL 8.4 握手，说明故障发生在本机当时的网络路径状态，未发现 MySQL 配置错误。未修改 OneXray 配置，也未启动本机 Docker。日志位于 `data/debug/services-20261108/`。

## 3. 各项目的工作入口

下列相对路径以该行所属项目根目录为起点。

### project_agent

| 范围 | 入口 | 说明 |
| --- | --- | --- |
| 工作规则 | `AGENTS.md` | 新会话读取共享上下文的入口，保留原模块约束 |
| 统一门户 | `java/ruoyi-react/react-ui/src/pages/Portal/Home/index.tsx` | `/portal/home` 的模块入口清单；已见项目管理、闲鱼、抖音、小红书、人生指南、任务待办等入口 |
| 任务待办 | `java/ruoyi-react/react-ui/src/pages/Portal/Todo/`、`/agent/todo` | 网页维护 Agent 扫描队列，读写 `docs/TODO_AGENT_QUEUE.yaml` |
| 门户路由 | `java/ruoyi-react/react-ui/config/routes.ts` | 已有 `/subsystem/douyin`、`/subsystem/xhs`、`/subsystem/xianyu`、`/subsystem/myhome`、`/portal/todo` |
| 抖音嵌入页 | `java/ruoyi-react/react-ui/src/pages/Subsystem/Douyin/index.tsx` | 通过共用子系统框架打开发布服务，默认本地端口 12500 |
| 小红书嵌入页 | `java/ruoyi-react/react-ui/src/pages/Subsystem/Xhs/index.tsx` | 同上结构，默认本地端口 12600；slug=`xhs` |
| 子系统地址解析 | `java/ruoyi-react/react-ui/src/utils/subsystemOrigin.ts` | 本地主机走端口；其他主机使用 `/gw/<slug>`；新子系统需配套检查网关 |
| 发布服务 | `python/douyin-auto/README.md`、`app/main.py`、`app/scanner.py`、`app/daily.py`、`app/db.py` | 独立 FastAPI + Playwright 服务，包含扫描、任务与按集数记录的发布状态 |
| 抖音互动记录 | `python/douyin-auto/app/interaction_store.py`、`app/mobile_comment_collector.py`、`web/interaction.html`、`web/comment-replies.html` | 互动流水落在 `dy_interaction_record`；「评论回复记录」菜单只读筛选 `kind=comment`。评论来源包括创作者中心和安卓「消息→互动消息」；手机扫描每小时执行，忽略已读标记，只处理当天本人视频评论，要求核实作者标识及评论人/内容、无作者回复后先记 `PENDING`，自动模式下用 DeepSeek 判断并回复，无法判断时中性兜底，发送后需读回确认；不确定则 `NEEDS_REVIEW` 且不重发。2026-11-08 真机只读扫描已成功：6 条“周五”通知换算到 2026-11-06，当天符合“评论了你”的通知 0 条。正式手动任务第一次因私信采集占用手机而重试，空闲后再执行则 MySQL 超时，未打开或发送评论回复。 |
| 抖音来信与私信好友 | `python/douyin-auto/app/dm_inbox_collector.py`、`app/dm_batch_store.py`、`web/dm-inbox.html`、`web/dm-batch.html`、`web/dm-failures.html` | 来信依赖小米 8 收件箱，启动后立即运行、随后每小时采集；相对时间换算为实际消息日期，日期与时间分列。互关私信日报及连续三日发送失败清单位于「私信好友」一级菜单下。今天主动来信且当天没有确认回复的对象可在会话内回复；只有同一批次连续 3 个自然日明确 `FAILED` 才写入独立失败表，跳过及待核对不计失败。应用空间入口与其它子系统共用 `SubsystemChrome` iframe 外框，并提供返回应用空间入口 |
| 小红书发布服务 | `python/xhs-auto/README.md`、`app/main.py`、`app/publisher.py` | 同构于 douyin-auto；Playwright 发创作服务平台；库 `xhs_auto` |
| 项目管理台账 / 审批 | `java/ruoyi-react`：`/project/pm/**` + MySQL `pm_project` | 多级审批状态机；表 SQL `java/ruoyi-react/sql/pm_project.sql` |
| 项目管理 AI | `java/ruoyi-react/ruoyi-ai`：`/ai/chat`、`/ai/chat/stream`、`/ai/projects/parse` | Spring AI + LangChain4j Tools；前端原生 `Project/Chat`、`Project/Parse`（不再 iframe `:8080`） |
| 旧 Python PM/RAG API | `python/src/project_agent/api/server.py` | Self-RAG / 旧 parse 演示备用；**PM 主路径一期不再依赖** |
| 原有架构与联调 | `agent.md`、`docs/ARCHITECTURE.md`、`docs/PM_LOCAL_DEV.md` | 以 ARCHITECTURE 一期叙述为准；agent.md 仍约束 Python 包路径 |

### animation-pro

- `README_EP_INDEX.md`：技术栈系列目录索引；文档列至 EP36。目录列表和“已交付”文字是文件证据，不等于本次重新验收视频或验证抖音发布。
- `TOPIC_PRIORITY.md`：后续选题优先 **ES → Grafana → XXL-JOB → Nacos**（2026-11-10 用户确认；长视频员工默认按此队列）。
- `EPxx_<topic>/video_html/`：系列成片通常放置位置；例如 `EP36_agent_permissions/video_html/`。
- `SHORT_VIDEO_GUIDELINES.md`、`SUBTITLE_SYNC.md`、`COVER_UPLOAD_GUIDELINES.md`：系列时长、字幕同步和上传封面要求。
- `derivative_douyin/AGENTS.md`：该支线独立的声音与生产工作流，不用系列规范强行覆盖。
- `templates/`、`template_gallery_100/`、`follow1000_vertical/` 等分别承担模板和支线用途，不默认全部进入系列发布队列。
- `template_gallery_100/` 已于2026-10-19补齐100款静态模板、300张1920×1080横版原图、100张1440×2880竖向展示图及可编辑画面；含10个分类、每类10款，首批10款原图和画面源文件保持不变。入口为 `template_gallery_100/index.html`，整包为 `百款视频模板_完整包.zip`；未包含配音或成片，不进入技术栈EP发布队列。2026-10-18 按用户要求制作闲鱼选款/售卖资料包；商品草稿、试运营价格与制作边界见 `docs/VIDEO_SALES_OFFER.md`，包位于 `outputs/video_sales_20261018/`。销售主体为按约定制作的视频服务，选款包与商家源包分开。

### sihuo

- `AGENTS.md`：私活团队职责、项目资料与授权规则；文档目前注明没有已确认的客户项目，后续接单状态须按真实证据更新。
- `.codex/agents/`：项目经理、设计、开发、测试、部署等员工配置；配置文件不能替代实际执行服务。
- `.agents/skills/freelance-team/`：私活团队工作流程和需求资料模板。
- `integrations/agency-agents/manifest.json`、`vendor/agency-agents/`：专项员工库来源和原版资料。
- `projects/developer-studio/`：自身工作室的 brief、设计、检查与交付资料，不应计为真实客户订单。
- `sites/xuzao-studio/`：工作室展示站点资产；公开展示与内部客户管理是不同入口。
- `marketing/launch/`：服务说明、获客渠道、客户需求收集与宣传素材；不能据此推断获客、成交或收款已经发生。
- 2026-11-06服务理念：用户提出“共同目标提升效率、私人定制、不满意不要钱”；记录与介绍草案见 `E:\ai-pro\sihuo\marketing\launch\positioning.md`。原官网服务保留，承诺适用范围与合作机制待明确；本轮未改站或发布，接入实施状态不变。
- 2026-11-07：用户要求介绍加入“全力支持”，并讨论开发费、月费和服务器费用；试行建议与官方云价示例见 `E:\ai-pro\sihuo\marketing\launch\pricing-and-support.md`。价格与服务条款待用户确认，未采购资源、改站或对外发布，业务接入状态不变。

## 4. 已有视频交接约定

1. animation-pro 产出视频及同目录的标题、封面等素材。
2. douyin-auto 从配置的视频目录递归扫描 `.mp4`，识别文件名中的 `EP.<数字>`（例如 `技术栈EP.36教程.mp4`）。无 EP 编号、低于起始集数或已发布的项目会被过滤。
3. 标题候选包括 `标题.txt`、`标题.md`、`title.txt`；封面按扫描器规则读取竖版、横版及备用封面。
4. 发布服务有 `/api/scan`、`/api/publish`、`/api/episodes`、`/api/jobs` 等接口，以及定时发布逻辑；生产默认值、实际启用状态和当日记录须在任务需要时核实。
5. 集数阈值与已发布状态涉及数据库和当前配置。README 示例中的起始集数与源码默认值已有差异，不把旧文档数字复制成当前运行事实。
6. sihuo 的获客短片未必属于技术栈 EP 系列。后续若复用发布服务，需要单独设计素材 ID/分类和去重规则，避免 EP 编号冲突或误发布。

## 5. sihuo 接入目标与实施顺序

详细方案：`E:\ai-pro\project_agent\docs\SIHUO_INTEGRATION_PLAN.md`。

| 阶段 | 交付内容 | 当前状态 |
| --- | --- | --- |
| 共享上下文 | 三项目 AGENTS 入口、此总览、接入方案 | 已完成；三项目读取入口、关键路径及 UTF-8 编码已核验 |
| 第一期：统一入口与资料 | 现有门户增加私活工作台，展示工作室、资料和团队目录，支持进入需求整理 | 待实施 |
| 第二期：接单业务 | 客户线索、需求范围、报价草稿、项目交付进度与资料关联 | 待明确业务范围后实施 |
| 第三期：员工与宣传协作 | 可追踪的任务调度；必要时串接宣传视频制作与发布 | 待一期、二期形成稳定的数据与执行接口后实施 |

先沿用已有门户与项目管理能力。企业立项的 `draft/pending/approved/rejected` 是审批状态，不能直接当成私活的开发、验收、交付和收款状态。新会话先看方案，不默认重建整套系统或搬迁三个目录。

## 6. 新会话的用法与维护

- 在三个项目各自根目录发起会话时，适用的 `AGENTS.md` 提供彼此的路径、职责和总览入口。涉及历史决策或跨项目工作时按指引读取总览。
- 对已经打开的旧会话，可明确要求“读取 `E:\ai-pro\project_agent\PROJECT_MAP.md` 后继续”；不要假定文件更新已自动进入旧上下文。
- 当前总协调会话已关联到 `E:\ai-pro\project_agent`，直接使用本项目根目录的 `AGENTS.md`。
- 总览是可维护的项目文档，不是完整聊天记录同步，也不授予额外的目录访问权限。
- 修改连接、状态或工作分工后更新对应段落、核验日期和下面的简短变更记录。仅增加影响后续决策的事实，详细日志保留在所属项目。
- 总览不可读时说明具体路径和缺失内容，继续完成不依赖它的工作；不要编造进度。

## 7. 变更记录

- 2026-11-13：Agent 待办 `/agent/todo/**` 改为匿名可访问；定时 tick 改为 HTTP 拉/写（`geime.fun/gw/ruoyi` 或本机 `:8088`），与门户 `/portal/todo` 实时同源，不再依赖云端读 Git YAML 快照。存储仍为本地 `docs/TODO_AGENT_QUEUE.yaml`。

- 2026-11-10：总监两条 approved 待办（功能集成、整体方向/盈利）此前未跑，因为扫描 Automation 未建、本会话也未 tick。本会话手动 tick 后均 `done`。结论（方案级，未改业务代码）：集成=门户编排不并仓，缺口是 sihuo 一期入口；现阶段优先闲鱼跟单与授权后的序造获客，成片按 ES→Grafana→XXL-JOB→Nacos；无账面成交。队列 `todo-20261109-fcb3f` / `todo-20261109-6ba91`。仍未代建云端 Automation。

- 2026-11-13：视频优先改为软考软件设计师章节（参考李阿妹课程目录结构）；旁白云扬 **+0%**、吐字清晰带顿挫。首集 EP55「数据的表示」已交付约 178.57s。中间件队列（ES 等）暂缓。见 `SOFT_EXAM_SERIES.md`、`TOPIC_PRIORITY.md`。

- 2026-11-10：animation-pro 后续选题曾优先 **ES → Grafana → XXL-JOB → Nacos**；2026-11-13 起让位于软设系列。

- 2026-11-09：任务待办员工台扩充总监、总技术工程师、项目经理、财务、UI设计师，并配电子头像与 Cursor 岗位 Agent；扫描路由同步。未做真实工时/月费核算。

- 2026-11-09：门户新增独立模块「任务待办」`/portal/todo`，后端 `/agent/todo` 读写 `docs/TODO_AGENT_QUEUE.yaml`（与 Cursor 扫描同一文件）。需重启若依 `:8088` 后接口才可用；未代用户创建云端 Automation。

- 2026-11-09：新增 Agent 待办队列（SuperAgent 轻量）：`docs/TODO_AGENT_QUEUE.yaml`、`docs/AGENT_TODO_RUNBOOK.md`、`.cursor/prompts/agent-todo-tick.md`、Automation 草稿 `.cursor/automations/agent-todo-scan.prompt.md`。定时 tick 扫描 `approved` 项并由主 Agent 派 Task 子 Agent；首条试跑为外网 `/gw/*` 冒烟（`qa-tester`，已 approved）。未代用户创建云端 Cursor Automation，需在 Automations UI 粘贴草稿并 Run once。

- 2026-11-07：抖音来信流程调整为先保存未读名单，再直接打开收件箱会话标记已读；优先点可见会话行，搜索无精确结果时滚动查找，扫描上限 40 屏；当天确认未发送才在当前会话回固定话术，不做作品互动。处理期间暂停其他私信，每轮最多 15 位，未完成按小时重试。页面统计改为 CONFIRMED 才计为已发送，SENDING/NEEDS_REVIEW 单列待核对，失败记录不算已发送。运行核验：`python -m compileall -q app` 通过；`:12500/dm-inbox` 与状态/日报 API 返回 200；真机一轮扫描 212 个会话，6 位未读全部打开，确认回复 5 位，待发 0，另有 2 条历史发送状态待核对；完成后私信调度恢复，随后一次调度发送被“今日已发送”去重跳过。详见 `python/douyin-auto/README.md`。

- 2026-11-07：抖音来信日报修正为按消息实际日期分组，解析“昨天 22:15”等相对时间并独立存储/展示日期与时间；迁移旧记录时从摘要解析时间并移除重复尾缀。今天来信才进入自动回复队列，同日 `CONFIRMED` 发送计为双方都发，待核对状态单列。核验：`2026-11-06 22:15` 示例归到昨天，摘要只留 `[赞]`；今日/昨日日报分别返回 35/7 位来信，页面日期与时间列存在且 `/dm-inbox` 返回 200。真机扫描 209 个会话，7 位未读均打开，今天符合条件者回复 1 位，待处理 0；调度恢复，采集间隔 60 分钟。`python -m compileall -q app` 通过。旧日期 2 位未回复者保留在昨日统计，不自动补发。详见 `python/douyin-auto/README.md`。

- 2026-11-11：待办 `todo-20261111-3c4ef`、`todo-20261111-9671e` 由总监拍板。盈利只推序造企业展示型官网（草案 1500–3000 元/单，价格须用户确认后再上架）；考试题模块暂不做，真题和教材原文不进仓库或门户。本轮未派工、未改业务代码、未代发布。

- 2026-11-10：用户确认 twlmac 局域网地址由 `192.168.1.172` 变为 `192.168.1.177`。本机 hosts 的 `twlmac` 改为新地址；`192.168.1.177` 的 `6379`、`3306` 已探测可连通。应用仍用主机名 `twlmac`，不改各 `.env`。Kafka 对外地址在 `deploy/middleware/docker-compose.yml` 改为 `192.168.1.177:9092`，需在 twlmac 上重新加载该 compose 后才生效。历史备份脚本里的旧地址未改。

- 2026-11-07：抖音侧栏增加「私信好友」一级菜单，将互关日报与连续失败查询作为二级菜单；连续 3 天发送状态均明确为 `FAILED` 才写入 `dy_dm_send_failure` 独立清单，跳过/待核对不算失败；日报发送结果同步记录到批次成员，历史发送状态可回填。新增 `/dm-failures` 和 `/api/dm-batch/failures`，并修正日报日期列表接口的参数调用。核验：`python -m compileall -q app` 通过；失败查询 API 与两个页面返回 200，侧栏及日报/失败页内容已在浏览器确认；历史回填检查 80 条，未发现连续三天明确失败对象。核验时当前批次为 2026-11-07 至 2026-11-09，只有第 1 天有发送记录，其中 9 条明确失败，尚不能进入三日失败清单；后续两天扫描完成后再按规则判定。门户 `:8000` 本次浏览器跳转到登录页，未登录验证该嵌入路由。详见 `python/douyin-auto/README.md`。

- 2026-11-07：根据用户反馈，应用空间进入抖音运营台与新窗口打开时菜单显示不一致；将 `/subsystem/douyin` 与 `/subsystem/douyin/interaction` 改为在当前标签页直达 `:12500` 服务，去除这两个入口的 iframe。抖音页面 HTML 对菜单脚本和样式加了版本参数，菜单内页面链接也带版本号以绕过旧缓存。核验：React `npm run build` 成功；`:12500/`、带版本参数的 `/shell.js` 与 `/dm-batch` 均返回 200。因当前门户浏览器无法通过安全校验取得已登录标签页，未做应用空间里的真实跳转验收；登录后当前标签会进入独立服务，浏览器后退可返回门户。

- 2026-11-07：用户指出整页直达导致抖音入口无法像其它子系统一样返回应用空间；已将两个抖音入口恢复为共用 `SubsystemChrome`，并为 iframe 目标地址增加每次挂载独有的查询标记，配合菜单脚本/样式版本参数绕开旧 iframe 资源缓存。保留外层“返回应用空间”与“新窗口打开”操作。最终 `npm run build` 成功；`:12500/` 及带版本参数的私信页面/菜单资源返回 200。全量 `tsc` 被项目旧目录 `node_modules_old_211137` 内声明文件语法错误阻断，错误不在本次入口文件。

- 2026-11-07：抖音互动评论回复改为仅采集当前登录创作者中心 `/creator-micro/interactive/comment` 下的本人视频评论；路径校验失败时拒绝采集和回复。对新评论使用 DeepSeek 结合评论与作品信息生成回复，模型不可用、无法判断或生成不合规时发送 `INTERACTION_COMMENT_FALLBACK` 中性话术；评论按单条消息键去重，不再同一评论者/视频每日限一次。私信模型及日去重保持独立。核验：`python -m compileall -q app` 与页面内联 JavaScript 语法解析通过；重启 `:12500` 后 DeepSeek `deepseek-chat` 已配置。启动后收件箱扫描 205 个会话、未读 0 位，门控释放，互动模式恢复 `auto`。后续 2026-11-07 通过真机页面读回确认两条手动评论回复；手机定时扫描另记于 2026-11-08。
- 2026-11-08：新增安卓「消息→互动消息」本人视频评论扫描器，每小时运行、手机忙时 5 分钟后重试；忽略已读标记，只识别当天“评论了你”，逐条打开并确认本人视频、同一评论人/内容及是否已有作者回复。没有作者回复时先写 `PENDING`，仅在自动发送已启用时用 DeepSeek 回复；模型无法判断时用中性话术，需读回作者回复确认，发送不确定时为 `NEEDS_REVIEW` 且不自动重发。新增 `GET /api/interaction/mobile-comments/status`、`POST /api/interaction/mobile-comments/run` 和粉丝互动页手动扫描按钮；评论扫描器与私信收件箱共用手机锁，与创作者中心评论回复共用评论锁。`py_compile` 通过；`:12500/api/interaction/mobile-comments/status` 返回启用且间隔 60 分钟，健康接口可响应并报告 MySQL ping 超时。修正星期日期换算与手机互动消息入口描述定位，并补充唤醒时的小米听筒提示/锁屏画报处理。真机只读扫描已成功，6 条“周五”通知归到 2026-11-06，2026-11-08 符合“评论了你”的通知为 0 条；正式手动扫描先因私信采集占用手机而重试，手机空闲后执行仍因 MySQL 读超时未进入采集、未落库、未发送。另修复每日视频发布在数据库不能预留发布名额时仍继续排队的问题；本次重启的 09:04 补跑被该保护阻止，没有发布任务入队。11-07 此前两条手动评论回复已由真机页面读回确认；评论扫描自动落库和发送验收仍待数据库恢复及真实当天通知。详见 `python/douyin-auto/README.md` 与 `python/douyin-auto/data/debug/mobile-comment-safe-restart-20261108.err.log`。
- 2026-11-07：抖音运营台新增「评论回复记录」左侧菜单与 `/comment-replies` 只读页面，复用 `/api/interaction/records?kind=comment`，按状态、评论用户筛选并分页展示作品、原评论、回复内容和记录状态。所有已有页面升级 `shell.js` 缓存版本，确保从应用空间入口进入也能看到新菜单。核验：`python -m compileall -q app`、`node --check web/shell.js` 和新页内联 JavaScript 语法检查通过；重启后 `:12500/comment-replies`、新版本 `/shell.js` 与评论记录 API 返回有效数据，接口当前有 1 条历史评论记录。启动时手机收件箱扫描 209 个会话、打开并回复 1 位未读来信；扫描结束后互动自动模式恢复，下一轮定时扫描为 20:56。未手动触发评论回复。

- 2026-11-07：sihuo新增收费与支持方案草案，区分一次开发、可选人工月费、实际云资源费用；服务定位介绍补上用户要求的“全力支持”。项目经理核对估算与边界，具体金额和承诺口径未视为已生效。入口为 `marketing/launch/pricing-and-support.md`；本轮未采购或发布，未变更项目接口或接入进度。

- 2026-11-06：sihuo补充用户提出的服务理念与对外介绍草案，入口为 `marketing/launch/positioning.md`；保留原企业展示型官网服务和历史素材，尚未细化“不满意不要钱”的收费与交付机制，未据此改站或对外发布。未变更项目职责、接口或业务接入进度。

- 2026-11-06：INFRA 从本机 WSL Docker（`127.0.0.1`）切回 `twlmac`（`192.168.1.172`）。六处 `.env`（`conf`、若依、闲鱼、抖音、小红书、myhome）的 `INFRA_HOST`/`MYSQL_HOST`/`REDIS_HOST` 已改回 `twlmac`；本机 `mysql-agent`/`redis-agent` 已停止（容器未删）。切配置前将本机库 `douyin_auto` 整库覆盖迁入 twlmac（`dy_episode` 48、`dy_interaction_record` 660、`dy_relation_contact` 1666 等），远端旧库备份在 `dumps/douyin_auto_twlmac_backup.json`。冒烟：若依 `:8088`、闲鱼健康、抖音 `/api/health` 显示 `db.host=twlmac`、myhome `/api/health` mysql ok。其余库未迁，仍用 twlmac 原有数据。

- 2026-11-06：修复项目页顶栏“应用空间”被 ProLayout 品牌字号覆盖的问题；项目页与子系统外框共用 `BackToAppSpace`，统一返回入口字号、间距、悬停与焦点样式。原路由隔离示例账号浏览器核对确认链接及文字均为 12px、无下划线；截图 `outputs/system-refresh-20261105/header-unified.png`。未变更业务接口。

- 2026-11-06：项目管理 Java AI 一期：新增 `ruoyi-ai`（Spring AI + LangChain4j）、`pm_project` MySQL 持久化、`/ai/chat|/stream|/projects/parse`；前端 Chat/Parse 去 Python iframe。代码已编译通过；完整联调验收（登录→流式→解析→审批）依赖重启 `:8088` 后验证。详见 `docs/ARCHITECTURE.md`。

- 2026-11-05：完成登录、门户、项目页和子系统框架的展示优化，增加统一主题、状态筛选反馈、详情抽屉、载入提示及手机适配；原系统前端编译完成，20 项浏览器检查通过（浏览器内示例账号、接口及 iframe，占位数据未写入数据库）。本地 HTML 入口 9080/8000 返回 200；完整 TypeScript 检查未完成，未部署或验收真实业务。证据 `outputs/system-refresh-20261105/`，说明 `docs/SYSTEM_PRESENTATION_20261105.md`。

- 2026-11-05：统一门户 `/portal/home` 优化工作空间布局、分类滑块、应用搜索和卡片说明展开，保留既有 6 个入口、角色判断与退出逻辑；修复小红书 SVG 非法标签字符。实际首页源码的隔离示例账号预览通过 20 项浏览器检查及 TSX 语法检查，证据在 `outputs/portal-refresh-20261105/`，详见 `docs/PORTAL_PRESENTATION_20261105.md`。完整项目类型检查和开发服务启动因本机资源限制未完成；未部署、未验证真实登录或子系统服务状态。

- 2026-11-01：抖音真机私信改为主路径 `我 → 互关/关注列表 → 搜索栏`（`mobile_dm.py`），全局「用户」搜索仅作 `fallback`；私信后 `mobile_engage.py` 按前 4 条作品 **4→1→3→2** 选 1 条点赞评论，无作品跳过。小米 8 已探通互关列表搜到 Lister 主页（其页显示「暂无作品」）。别人评论我的视频仍走创作者中心「启用自动」。`:12500` 已重启。

- 2026-11-01：用户选定抖音私信长期方案为**安卓真机**（非模拟器）。接入说明 `python/douyin-auto/docs/ANDROID_DEVICE.md`；本机 `adb`/`scrcpy` 可用，小米 8 已接入。

- 2026-10-24：闲鱼货源管理改为每日凌晨 3:00（Asia/Shanghai）扫描 dayu 货源；可售自动上架、不可售自动下架关联闲鱼商品（`SupplyMonitorJob` / `POST /api/supply/monitor/check`）。配置项 `xianyu.supply.monitor-cron`、`auto-upshelf`、`auto-downshelf`。

- 2026-10-31：`python/douyin-auto` 互关/关注关系入库 MySQL 表 `dy_relation_contact`、`dy_relation_sync_log`；API `/api/relation/*`；已自 debug JSON 导入约 812 互关、854 单方面关注（1666 关注联系人）。

- 2026-10-31：`python/douyin-auto` 评论/私信回复按「预览 → 启用自动发送」重构：`interaction_collect` / `interaction_send` / `interaction_service` + MySQL `dy_interaction_record`（基线、去重、状态机）；默认预览、自动发送关；`POST /api/interaction/records/{id}/verify` 只读核对。代码与单测已更新；**未**代用户完成真实账号 1 评论 + 1 私信发送验收。

- 2026-10-29：`python/douyin-auto` 新增评论/私信 Playwright 自动回复（默认每 30 分钟最多 15 条，服务内调度）；见 `README.md` 与 `GET /api/interaction/status`。

- 2026-10-24：闲鱼子系统新增「货源管理」`/supply/list`（表 `t_supply_source`、API `/api/supply`）。已录入万屿数卡电费 6 元货源 `https://shop.iwany.top/goods?id=24523`（平台商品号 24523，进货价约 5.55）。仅为上游采购台账，未代为在闲鱼上架电费代缴。

- 2026-10-24：小红书默认改为 `template_gallery_100` 图文模式（海报+三帧），与抖音 EP 视频分离；文案/首波方案见 `python/xhs-auto/docs/NOTE_PUBLISH_PLAN.md`。未代用户真实发布。

- 2026-10-24：按抖音发布同构新增 `python/xhs-auto`（:12600）与门户 `/subsystem/xhs`、nginx `/gw/xhs/`、frpc `12600`；MySQL 库 `xhs_auto`。未代用户扫码登录或真实发布。

- 2026-10-19：animation-pro 根据用户要求补齐百款静态模板库，验收100张竖向展示图、300张横版画面及原首批10款保留；提供分类/风格筛选和完整下载包。本次没有制作或发布视频，也未修改已有闲鱼商品及售卖资料包。

- 2026-10-19：用户更新登录后，闲鱼实际登录校验通过；已发布5元视频制作主商品（本地21、平台1091134951396），并通过平台详情读回核验标题、5元价格及在售状态。三张指定图片上传成功，自动发货关闭，人工交付；未发布其他3个独立草稿。链接 `https://www.goofish.com/item?id=1091134951396`，证据见 `outputs/video_sales_20261018/闲鱼上架记录.json`。

- 2026-10-18：用户确认基础订单最低5元并授权闲鱼上架。已保存主商品到闲鱼管理后台（本地商品21、账号1、5元、自动发货关闭），并修复视频商品被强制生成PDF封面/回退资料类目的问题，4项回归通过并加载。实际平台登录校验失效，图片上传HTTP 302，自动刷新未恢复；商品尚未上架，等待更新登录凭据后继续发布既有草稿。详见 `docs/VIDEO_SALES_OFFER.md`。

- 2026-10-18：读取用户引用的“百款模板，视频定制”会话，核实10款静态预览并打包闲鱼售卖资料；保留50–60秒0.5元/条、超60秒至180秒1元/条，提出最低5元/单及分档定制/改稿规则。商品仅为本地草稿，未发布、未导入数据库，动态样片和实际订单成本验证待完成。详见 `docs/VIDEO_SALES_OFFER.md`。

- 2026-10-18：按用户说明确定三项目职责；核实门户和文件扫描式视频发布连接；建立共享上下文及 sihuo 接入方案。此次为文档与配置指引工作，未实现私活工作台、员工执行接口或业务数据同步。
- 2026-10-18：核验三个项目的 AGENTS 入口均指向此总览；关键资料路径存在；五份交付文档通过 UTF-8 检查；sihuo 原有 AGENTS 内容按字节完整保留。
- 2026-10-18：补充抖音失败诊断及证据路径，区分封面验收与页面状态不一致、保活资源竞争和非阻塞警告；修复与真实发布验收均未实施。
- 2026-10-18：按用户要求实施稳定封面预览检查、浏览器排队及同集任务去重；17 项离线回归、语法与编码检查通过；空闲时重启服务并验证新健康状态。真实抖音发布、简介及定位的线上验收未执行。
- 2026-10-18：跟进用户实际运行后的结束识别故障，修复提交确认、重复点击、清理异常覆盖及前端轮询；29 项回归通过，空闲重启服务。只读核对 EP36 已发布并修正任务，记录用户 EP37/38 成功运行；未代用户重新发布，简介与定位读回校验尚待处理。
