# 账本 MySQL API

单用户账本持久化：整份 `LedgerDump` JSON 存在 `wodesuoyou.ledger`。

## 配置

编辑 `server/.env`：

```
MYSQL_HOST=192.168.1.46
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=root123456
MYSQL_DATABASE=wodesuoyou
API_PORT=18002
```

## 授权（首次必做）

本机 IP 若被拒绝（`Host 'x' is not allowed`），在 **192.168.1.46**（Docker MySQL）上执行 `grant.sql`。

## 启动

```bash
npm --prefix server install
npm --prefix server start
```

前端 Vite 已把 `/api` 代理到 `18002`。
