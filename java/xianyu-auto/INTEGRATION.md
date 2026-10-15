# Integration into project_agent

Migrated from `E:\\java\\xianyu-auto` as an independent subsystem under RuoYi.

## Infra (twlmac)

| Item | Value |
|---|---|
| MySQL | `twlmac:3306` / db `xx_erp` / root / root123456 |
| Port | `12400` |
| Config | `.env` (do not commit secrets) |

Do not start local Docker DB; use twlmac like the rest of project_agent.

## Start

> 已纳入仓库启动清单：`.cursor/rules/local-services.mdc`（「启动服务」时与 core stack 一并检查 `:12400`）。

```powershell
cd E:\\ai-pro\\project_agent\\java\\xianyu-auto
# 需已有 frontend/dist，并在 target/classes/static（package 会自动拷贝）
mvn spring-boot:run "-Dfrontend.phase=none"
```

Or package with frontend static assets:

```powershell
mvn clean package -DskipTests
java -jar target/xianyu-auto-1.0.0-SNAPSHOT.jar
```

First boot creates `xx_erp` and runs `schema.sql`.
健康检查：`http://127.0.0.1:12400/api/public/health`；若依菜单：`http://localhost:8000/subsystem/xianyu`。

## RuoYi entry

1. admin login -> `/portal/home`
2. click xianyu card -> `/subsystem/xianyu` (iframe -> `http://127.0.0.1:12400`)
3. xianyu own login: `admin` / `admin123`

Override iframe origin with `XIANYU_PORTAL_ORIGIN` at react-ui build time.
