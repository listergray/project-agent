# 闲鱼自动发货系统

> 一个开箱即用的闲鱼虚拟商品自动发货系统，支持多账号管理、网盘链接库存、关键词 + AI 智能回复、邮件/企业微信通知。单 JAR / 单 Docker 容器部署。

## ✨ 核心特性

- **多账号管理**：一个后台管理多个闲鱼账号，独立 WebSocket 连接，互不影响
- **自动发货**：买家付款后自动识别订单 → 匹配发货规则 → 扣减库存 → 发送内容 → 调用闲鱼确认发货 API
- **网盘链接库存**：支持 REUSABLE 类型（链接 + 提取码，按 max_count 限额，乐观锁并发控制）
- **三种发货内容**：固定文本 / 网盘库存 / 外部 API 调用
- **智能回复**：优先级匹配（精确 > 模糊 > 正则 > 通用关键词 > AI 兜底 > 默认回复）
- **AI 集成**：OpenAI / 阿里通义千问 / DeepSeek，OpenAI 兼容协议统一封装
- **通知告警**：Cookie 失效、发货失败、AI 异常 → 邮件 + 企业微信 + 站内消息
- **可视化后台**：Vue3 + Element Plus（Yudao 风格），数据看板 + 在线聊天
- **单容器部署**：SQLite 嵌入式数据库 + fat-jar，`docker run` 一行启动

## 🚀 快速开始

### 方式一：Docker 一键启动（推荐）

```bash
# 1. 克隆仓库
git clone <repo-url> xianyu-auto && cd xianyu-auto

# 2. 复制配置文件并填写
cp .env.example .env
vim .env   # 至少修改 ENCRYPT_KEY 和 SA_TOKEN_JWT_SECRET

# 3. 构建并启动
docker compose up -d --build

# 4. 浏览器访问
#    http://localhost:12400
#    默认账号: admin / admin123
```

### 方式二：本地开发模式（前后端分离调试）

**前置**：JDK 17、Node 20+、Maven 3.9+

```bash
# 后端
mvn spring-boot:run "-Dfrontend.phase=none"

# 前端（新终端）
cd frontend
npm install
npm run dev   # 自动打开 http://localhost:5173，已配置代理到 12400
```

### 方式三：单 JAR 部署（无 Docker）

```bash
mvn clean package -DskipTests
java -jar target/xianyu-auto.jar
```

## 📋 配置清单

详细配置项见 [.env.example](.env.example)，**必填项**如下：

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `ENCRYPT_KEY` | - | 32 字节 AES 密钥（加密 Cookie / 卡密） |
| `SA_TOKEN_JWT_SECRET` | - | JWT 签名密钥（≥ 32 字符） |
| `DEFAULT_ADMIN_PASSWORD` | `admin123` | admin 首次登录密码 |

**AI 回复**（至少填一个 API Key 才能启用）：
- `DASHSCOPE_API_KEY`（推荐，国内速度快）
- `OPENAI_API_KEY`
- `DEEPSEEK_API_KEY`

**通知**（按需）：
- `MAIL_HOST` + `MAIL_USERNAME` + `MAIL_PASSWORD`（邮件）
- `WECOM_WEBHOOK_URL`（企业微信群机器人）

## 📖 使用教程

### 1. 登录后台
浏览器访问 `http://localhost:12400`，使用 `admin / admin123`（或你配置的密码）登录。

### 2. 修改默认密码
点击右上角头像 → 修改密码。

### 3. 填写系统配置
左侧菜单 → 系统管理 → 系统配置：
- 填写 AI API Key（如已配置环境变量，此处可跳过）
- 配置邮件 / 企业微信通知（如已配置环境变量，此处可跳过）

### 4. 添加闲鱼账号
左侧菜单 → 闲鱼管理 → 闲鱼账号 → 新增账号：
- 填写昵称（仅用于后台识别，如"主账号"）
- 点击保存

### 5. 录入 Cookie
**如何获取 Cookie**：
1. 浏览器登录 [闲鱼网页版](https://www.goofish.com/)
2. 按 F12 打开开发者工具 → Application → Cookies
3. 复制全部 Cookie（或至少包含 `_m_h5_tk`、`_m_h5_tk_enc`、`unb`、`cookie2`、`_tb_token_`）

**录入**：
1. 闲鱼账号列表 → 对应账号 → 操作 → 更新 Cookie
2. 粘贴 Cookie 字符串 → 保存

### 6. 启动连接
点击「启动连接」，状态应变为 🟢 在线。

### 7. 验证消息
- 用另一个闲鱼账号给绑定的账号发消息
- 左侧菜单 → 消息管理 → 在线聊天，应实时显示消息
- 在输入框回复，验证消息能送达

### 8. 配置自动发货
（Phase 3 实现后）左侧菜单 → 自动发货 → 发货规则：
- 选择商品 / SKU
- 配置发货内容类型（固定文本 / 库存 / API）
- 设置延时（可选）

## 🏗️ 项目结构

```
xianyu-auto/
├── pom.xml                              # Maven 构建配置
├── Dockerfile                           # 多阶段镜像构建
├── docker-compose.yml                   # 容器编排
├── .env.example                         # 配置清单模板
├── src/main/
│   ├── java/com/xianyu/auto/
│   │   ├── XianyuAutoApplication.java  # 启动入口
│   │   ├── common/                     # 通用工具（CommonResult/AES/JsonUtils 等）
│   │   │   └── security/               # 协议工具（SignUtils/MessagePackDecoder）
│   │   ├── config/                     # Spring 配置
│   │   ├── system/                     # 系统管理（用户/配置/日志）
│   │   ├── xianyu/                     # ★ 闲鱼集成层
│   │   │   ├── client/                 # WebSocket / HTTP 客户端
│   │   │   ├── auth/                   # Cookie / Token 管理
│   │   │   ├── protocol/               # LWP 协议模型
│   │   │   └── handler/                # 消息处理器
│   │   ├── account/                    # 闲鱼账号管理
│   │   ├── product/                    # 商品管理
│   │   ├── inventory/                  # 网盘链接库存
│   │   ├── delivery/                   # ★ 自动发货
│   │   ├── reply/                      # 关键词 + AI 回复
│   │   ├── notify/                     # 通知服务
│   │   └── message/                    # 聊天消息
│   └── resources/
│       ├── application.yml             # Spring Boot 配置
│       └── schema.sql                  # SQLite 13 张表
└── frontend/                           # Vue3 前端
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── views/                      # 页面
        ├── api/                        # API 封装
        ├── stores/                     # Pinia 状态
        ├── router/                     # 路由守卫
        ├── layout/                     # Yudao 风格布局
        └── components/                # 通用组件
```

## 🧪 开发指南

### 常用 Maven 命令

```bash
# 跳过前端构建的后端调试
mvn spring-boot:run "-Dfrontend.phase=none"

# 仅打包后端 JAR（无前端）
mvn clean package "-Dfrontend.phase=none" -DskipTests

# 完整构建（含前端 npm build）
mvn clean package -DskipTests

# 运行测试
mvn test
```

### 前端调试

```bash
cd frontend
npm install
npm run dev       # 启动 Vite dev server，自动代理 /api → 12400
npm run build     # 生产构建
npm run lint      # ESLint 检查（如配置）
```

### 数据库管理

SQLite 数据文件位于 `./data/xianyu.db`，可用 [DB Browser for SQLite](https://sqlitebrowser.org/) 直接打开查看。

**手动备份**：
```bash
cp data/xianyu.db data/xianyu.db.bak.$(date +%Y%m%d)
```

## 🩺 健康检查

- **API 健康端点**：`GET /api/public/health` 返回 `{ "status": "UP" }`
- **Docker 健康检查**：自动每 30s 调用上述端点
- **日志查看**：`docker logs -f xianyu-auto` 或 `./logs/xianyu-auto.log`

## ❓ 常见问题 FAQ

### Q1：端口 12400 被占用怎么办？
修改 `.env` 中的 `SERVER_PORT=12401`（或其他空闲端口），然后 `docker compose up -d`。

### Q2：SQLite 报 "database is locked"？
并发写入过高时可能出现。本系统已启用 WAL 模式 + HikariCP 连接池（5 连接），正常使用不会触发。如出现请重启容器：`docker compose restart`。

### Q3：Cookie 失效怎么办？
系统会自动检测并通知。如收到失效通知：
1. 重新登录闲鱼网页版
2. 按使用教程 5 重新录入 Cookie
3. 在账号管理页点击「启动连接」

### Q4：AI 回复一直失败？
- 检查 `.env` 中 API Key 是否正确
- 检查网络是否能访问 AI 提供商（OpenAI 需要代理）
- 查看日志：`docker logs xianyu-auto | grep -i ai`
- 系统会自动降级为默认回复

### Q5：如何升级到新版本？
```bash
git pull
docker compose up -d --build
# 数据自动迁移（schema.sql 幂等建表）
```

### Q6：能否不用 Docker 直接跑？
可以，参考「方式三：单 JAR 部署」。需要 JDK 17+。

## 📞 技术栈

| 类别 | 选型 |
|---|---|
| 后端 | Spring Boot 3.5.0 + Java 17 + MyBatis-Plus 3.5.7 + Sa-Token 1.39.0 |
| 数据库 | SQLite 3.46（WAL 模式） |
| 闲鱼协议 | Java-WebSocket 1.5.4 + OkHttp 4.12 + msgpack-core 0.9.8 |
| 前端 | Vue 3.5 + Vite 5 + Element Plus 2.8 + Pinia 2.2 |
| 部署 | Docker + Docker Compose |

## 📝 开源协议

仅供学习交流使用，请遵守闲鱼平台相关协议。商用风险自负。

## 🐛 问题反馈

发现 Bug 或有功能建议，欢迎提 Issue。
