# SQLite → MySQL（xx_erp）迁移

## 步骤

1. 确认 Docker MySQL 可连：`127.0.0.1:53306`
2. `.env` 中配置 `MYSQL_*`（库名 `xx_erp`）
3. **先启动一次应用**（或至少跑通到 sql.init），让 `schema.sql` 建好表
4. 停止应用
5. 备份：`copy data\xianyu.db data\xianyu.db.bak`
6. 执行迁移：

```powershell
cd D:\java\xianyu-auto
mvn -q -DskipTests "-Dfrontend.phase=none" compile exec:java `
  "-Dexec.classpathScope=compile" `
  "-Dexec.mainClass=com.xianyu.auto.tools.SqliteToMysqlMigrator" `
  "-Dexec.args=./data/xianyu.db jdbc:mysql://127.0.0.1:53306/xx_erp?useSSL=false&allowPublicKeyRetrieval=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai root YOUR_PASSWORD"
```

7. 再启动应用，确认账号/商品/规则数据在线

**注意**：`ENCRYPT_KEY` 必须与迁移前一致，否则 Cookie 密文无法解密。
