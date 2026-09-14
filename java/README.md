# Java 业务侧

| 目录 | 说明 |
| --- | --- |
| `ruoyi-react/` | [whiteshader/ruoyi-react](https://gitee.com/whiteshader/ruoyi-react)：Spring Boot 3 + React(Ant Design Pro) |
| `project-agent/` | 项目库模块骨架（OpenAPI / SQL / Controller） |
| `_nest-biz-stub/` | 零依赖演示用项目库 HTTP（`:48080`，可选） |

## ruoyi-react 本机启动

依赖：本机 Docker MySQL(`3306`/`root123456`/`ry`) + Redis(`6379`)。

```bash
# 后端（端口 8088，避开 AI API :8080）
cd java/ruoyi-react
mvn -pl ruoyi-admin -am package -DskipTests
java -jar ruoyi-admin/target/ruoyi-admin.jar

# 前端（默认 http://localhost:8000，代理到 :8088）
cd java/ruoyi-react/react-ui
npm install
npm run dev
```

登录：`admin` / `admin123`
