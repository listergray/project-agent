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

```powershell
cd E:\\ai-pro\\project_agent\\java\\xianyu-auto
mvn spring-boot:run "-Dfrontend.phase=none"
```

Or package with frontend static assets:

```powershell
mvn clean package -DskipTests
java -jar target/xianyu-auto-1.0.0-SNAPSHOT.jar
```

First boot creates `xx_erp` and runs `schema.sql`.

## RuoYi entry

1. admin login -> `/portal/home`
2. click xianyu card -> `/subsystem/xianyu` (iframe -> `http://127.0.0.1:12400`)
3. xianyu own login: `admin` / `admin123`

Override iframe origin with `XIANYU_PORTAL_ORIGIN` at react-ui build time.
