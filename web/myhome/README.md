# 我的所有（myhome）

个人资产 / 小居 / 待办与账本。已并入 `project_agent` 子系统，经若依门户 iframe 打开。

- 前端：`http://127.0.0.1:18001`
- API：`http://127.0.0.1:18002`（Vite 代理 `/api`）
- 门户：`/portal/home` → 「我的所有」→ `/subsystem/myhome`

## 启动

```powershell
# API（MySQL：twlmac / 库 wodesuoyou，见 server/.env）
cd web/myhome/server
npm install
npm start

# 前端（另开终端）
cd web/myhome
npm install
npx vite --host 127.0.0.1 --port 18001
```

或一次性：`npm run dev:all`（需先装好 `server` 依赖）。

## 来源

从独立仓库 `E:\ai-pro\myhome` **复制**而来，原项目保留不动。本目录为工程内运行副本。
