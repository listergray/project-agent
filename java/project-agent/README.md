# Java 业务侧（芋道风格 · 项目库）

本目录是 **可拷贝进[芋道单体](https://doc.iocoder.cn/)工程** 的业务模块骨架，对应「项目库基础业务逻辑用 Java 实现」；AI 解析 / RAG 同步仍在本仓 Python。

## 使用方式

1. 本地克隆或已有芋道 Boot 工程（推荐 `yudao-boot-mini` 或完整 `ruoyi-vue-pro`）。
2. 将 `yudao-module-projectagent` 拷到芋道的 `yudao-module-xxx` 同级，在父 `pom.xml` 中注册模块。
3. 按芋道惯例补：
   - `application.yaml` 数据源
   - 菜单 SQL / 权限标识 `project:agent:query` 等
   - MyBatis Mapper XML（表 `project_agent_project`）
4. 启动后暴露与 OpenAPI 一致的 REST；Python `.env` 设置：

```env
PROJECT_BIZ_BASE_URL=http://127.0.0.1:48080
```

未配置时，Python 继续用本地 JSON（演示不依赖 Java）。

## 包结构（对齐芋道）

```
cn.iocoder.yudao.module.projectagent
  ├── controller.admin.ProjectController
  ├── service.ProjectService / impl
  ├── dal.dataobject.ProjectDO
  ├── dal.mysql.ProjectMapper
  ├── enums.ProjectStatusEnum
  └── controller.admin.vo.*
```

## 与 Python 的边界

| Java（本模块） | Python（本仓） |
| --- | --- |
| 创建/改/查/提交/审批 CRUD | `POST .../parse` 文档 LLM 解析 |
| MySQL 持久化与权限 | 审批通过后 `rag_sync` → Milvus |
| 列表/统计 | Self-RAG / 对话 / 代码助手 |
