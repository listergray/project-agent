# 项目管理本地联调说明

## 1. 必须启动 Nest 业务 Stub

项目管理基础 CRUD/审批走 Java/Nest 协议；本地用零依赖 stub：

```bash
node java/_nest-biz-stub/packages/server/run.mjs
```

默认监听 `127.0.0.1:48080`。

**改完 Nest stub（如 `run.mjs`）后必须重启该进程**，否则 `q` 等改动不会生效（仍跑旧内存里的脚本）。

Python 侧需指向该地址（示例）：

```bash
export PROJECT_BIZ_BASE_URL=http://127.0.0.1:48080
```

未设置时会回退本地 JSON，列表搜索/`q` 与正式 Java 路径行为可能不一致。

## 2. Python API（`/api/v1/projects*`）

启动项目 Agent 的 FastAPI（`python/.../api/server.py`），对外提供：

- `GET /api/v1/projects`（支持 `status`、`q`）
- `GET /api/v1/projects/stats`
- `POST /api/v1/projects/parse`（AI 解析，单文件 ≤ 20MB）
- 以及 create / update / submit / review 等

前端 `python-frontend` 通过同源或代理访问上述接口。

## 3. 改完前端务必 rebuild / dev

对 `python-frontend` 有任何改动后，在访问门户前执行：

```bash
cd python-frontend
npm run build
# 或开发态
npm run dev
```

若依/门户若加载的是已构建的 `dist`，**不重新 build 会出现「改了 TSX 但页面仍旧」的假失败**。

## 4. 若依菜单 iframe vs 门户直开

| 入口 | 说明 |
| --- | --- |
| 若依 `8000` 菜单「项目管理」 | iframe 嵌门户页，通常带 `embed=1`，页内 NavBar/营销 Hero 收敛 |
| 门户 `8080/projects?embed=1` | 直接打开同一页面，用于独立联调；`embed=1` 或处于 iframe 时均为嵌套态 |

联调时确认菜单 URL 指向当前门户端口，避免打到旧静态资源。

## 5. 解析耗时说明

`POST /api/v1/projects/parse` 走 AI，**经常超过 60 秒**。前端已：

- 开始时 toast：`正在解析，可能需要约 1–3 分钟…`
- 客户端 **180s** Abort 超时，超时文案：`解析超时（>180s），请缩小文档或稍后重试`

反向代理 / 网关超时需 ≥ 180s，否则会被中间层先断开。
