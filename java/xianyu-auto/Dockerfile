# =============================================================================
# 闲鱼自动发货系统 - 多阶段构建 Dockerfile
# 目标镜像 < 250MB，单 JAR 启动
# =============================================================================

# ---------- Stage 1: 前端构建 ----------
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend

# 利用缓存：先复制 package.json 与 lock 文件
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm config set registry https://registry.npmmirror.com \
    && npm ci --no-audit --no-fund

# 复制前端源码并构建
COPY frontend/ ./
RUN npm run build


# ---------- Stage 2: 后端构建 ----------
FROM maven:3.9-eclipse-temurin-17 AS backend-build
WORKDIR /app

# 复制 pom 提前下载依赖（利用 Docker 缓存层）
COPY pom.xml ./
RUN mvn dependency:go-offline -B -Dfrontend.phase=none

# 复制后端源码 + 前端 dist
COPY src ./src
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# 构建 fat-jar（跳过前端构建阶段与测试）
RUN mvn clean package -B -DskipTests -Dfrontend.phase=none


# ---------- Stage 3: 运行时 ----------
FROM eclipse-temurin:17-jre-alpine AS runtime

LABEL maintainer="xianyu-auto"
LABEL description="闲鱼自动发货系统 - 单 JAR 部署"

# 安装 tzdata + 时区设置 + 清理缓存
RUN apk add --no-cache tzdata curl \
    && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone \
    && apk del tzdata \
    && rm -rf /var/cache/apk/*

WORKDIR /app

# 复制构建产物
COPY --from=backend-build /app/target/xianyu-auto.jar /app/xianyu-auto.jar

# 创建数据卷目录
RUN mkdir -p /app/data /app/logs

# 暴露端口
EXPOSE 12400

# 健康检查（每 30s 检查一次，超时 5s，重试 3 次）
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -fsS http://localhost:12400/api/public/health || exit 1

# 数据卷
VOLUME ["/app/data", "/app/logs"]

# JVM 参数：容器内限制堆内存 512MB，使用 G1 GC，必要时启用 Headless
ENV JAVA_OPTS="-Xms256m -Xmx512m -XX:+UseG1GC -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/app/logs -Djava.awt.headless=true"
ENV SPRING_PROFILES_ACTIVE=prod

# 启动命令
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar /app/xianyu-auto.jar"]
