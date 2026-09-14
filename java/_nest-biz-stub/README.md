# RuoYi-React · Project Agent 业务后端

上游：[zhouzhishou123/RuoYi-React](https://github.com/zhouzhishou123/RuoYi-React)（React18 + NestJS 若依风格前后端分离）。

因当前环境无法直连 GitHub 完整克隆，本目录提供 **与上游同栈的 NestJS 业务服务根**（`packages/server`），实现 **项目管理 CRUD / 审批**，供 Python AI 通过 `PROJECT_BIZ_BASE_URL` 替换本地 `projects.json`。

网络恢复后可执行：

```bash
git clone https://github.com/zhouzhishou123/RuoYi-React.git ruoyi-react-upstream
# 再把 packages/server/src/project-agent 拷入上游 packages/server
```

## 启动（项目管理 API）

**推荐（零依赖，立即可跑）：**

```bash
cd packages/server
node run.mjs
# 默认 http://127.0.0.1:48080
```

**完整 Nest 开发（需能访问 npm）：**

```bash
cd packages/server
npm install
npm run start:dev
```

Python `conf/.env`：

```env
PROJECT_BIZ_BASE_URL=http://127.0.0.1:48080
```

数据文件：`packages/server/data/projects.json`（由 Nest 进程独立持久化，经 HTTP 暴露；Python 不再读写 `data/projects.json` 业务路径）。

## 接口（与 Python `java_client` / OpenAPI 对齐）

| 方法 | 路径 |
|------|------|
| GET | `/admin-api/project-agent/project/page` |
| GET | `/admin-api/project-agent/project/get` |
| POST | `/admin-api/project-agent/project/create` |
| PUT | `/admin-api/project-agent/project/update` |
| POST | `/admin-api/project-agent/project/submit` |
| POST | `/admin-api/project-agent/project/review` |
| PUT | `/admin-api/project-agent/project/rag-item-pk` |
| GET | `/admin-api/project-agent/project/stats` |

响应包装：`{ code: 0, data, msg }`（兼容芋道 CommonResult）。
