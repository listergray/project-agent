package com.xianyu.auto.tools;

import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

/**
 * 将 ./data/xianyu.db 数据导入 MySQL xx_erp（表结构需已由应用 schema.sql 创建）。
 *
 * 用法（项目根目录）:
 *   mvn -q -DskipTests exec:java -Dexec.classpathScope=compile \
 *     "-Dexec.mainClass=com.xianyu.auto.tools.SqliteToMysqlMigrator" \
 *     "-Dexec.args=./data/xianyu.db jdbc:mysql://127.0.0.1:53306/xx_erp?useSSL=false&allowPublicKeyRetrieval=true&characterEncoding=utf8 root YOUR_PASSWORD"
 */
public final class SqliteToMysqlMigrator {

    private static final String[] TABLES = {
            "t_sys_user", "t_sys_config", "t_sys_log", "t_account",
            "t_product", "t_inventory", "t_delivery_rule", "t_delivery_log",
            "t_keyword_rule", "t_chat_message", "t_ai_context",
            "t_notification", "t_webhook_config"
    };

    private SqliteToMysqlMigrator() {}

    public static void main(String[] args) throws Exception {
        String sqlitePath = args.length > 0 ? args[0] : "./data/xianyu.db";
        String mysqlUrl = args.length > 1 ? args[1]
                : "jdbc:mysql://127.0.0.1:53306/xx_erp?useSSL=false&allowPublicKeyRetrieval=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai";
        String user = args.length > 2 ? args[2] : "root";
        String password = args.length > 3 ? args[3] : "";

        if (!Files.exists(Path.of(sqlitePath))) {
            System.err.println("SQLite 文件不存在: " + sqlitePath);
            System.exit(1);
        }

        Class.forName("org.sqlite.JDBC");
        Class.forName("com.mysql.cj.jdbc.Driver");

        try (Connection sqlite = DriverManager.getConnection("jdbc:sqlite:" + sqlitePath);
             Connection mysql = DriverManager.getConnection(mysqlUrl, user, password)) {
            mysql.setAutoCommit(false);
            for (String table : TABLES) {
                if (!sqliteTableExists(sqlite, table)) {
                    System.out.println("跳过（SQLite 无表）: " + table);
                    continue;
                }
                if (!mysqlTableExists(mysql, table)) {
                    System.out.println("跳过（MySQL 无表，请先启动应用建表）: " + table);
                    continue;
                }
                int n = copyTable(sqlite, mysql, table);
                System.out.println("迁移 " + table + ": " + n + " 行");
            }
            mysql.commit();
            System.out.println("迁移完成");
        }
    }

    private static boolean sqliteTableExists(Connection c, String table) throws Exception {
        try (PreparedStatement ps = c.prepareStatement(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?")) {
            ps.setString(1, table);
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next();
            }
        }
    }

    private static boolean mysqlTableExists(Connection c, String table) throws Exception {
        try (PreparedStatement ps = c.prepareStatement(
                "SELECT 1 FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=?")) {
            ps.setString(1, table);
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next();
            }
        }
    }

    private static int copyTable(Connection sqlite, Connection mysql, String table) throws Exception {
        Set<String> mysqlCols = loadMysqlColumns(mysql, table);
        List<String> commonCols = new ArrayList<>();
        try (Statement st = sqlite.createStatement();
             ResultSet rs = st.executeQuery("SELECT * FROM " + table + " LIMIT 0")) {
            ResultSetMetaData meta = rs.getMetaData();
            for (int i = 1; i <= meta.getColumnCount(); i++) {
                String col = meta.getColumnLabel(i);
                if (mysqlCols.contains(col.toLowerCase(Locale.ROOT))) {
                    commonCols.add(col);
                }
            }
        }
        if (commonCols.isEmpty()) {
            return 0;
        }

        String colList = String.join(",", commonCols);
        String placeholders = String.join(",", commonCols.stream().map(c -> "?").toList());
        String insertSql = "REPLACE INTO " + table + " (" + colList + ") VALUES (" + placeholders + ")";

        int count = 0;
        try (Statement st = sqlite.createStatement();
             ResultSet rs = st.executeQuery("SELECT " + colList + " FROM " + table);
             PreparedStatement ps = mysql.prepareStatement(insertSql)) {
            while (rs.next()) {
                for (int i = 0; i < commonCols.size(); i++) {
                    Object v = rs.getObject(i + 1);
                    ps.setObject(i + 1, v);
                }
                ps.addBatch();
                count++;
                if (count % 200 == 0) {
                    ps.executeBatch();
                }
            }
            ps.executeBatch();
        }
        return count;
    }

    private static Set<String> loadMysqlColumns(Connection mysql, String table) throws Exception {
        Set<String> cols = new LinkedHashSet<>();
        try (PreparedStatement ps = mysql.prepareStatement(
                "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                        + "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=?")) {
            ps.setString(1, table);
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    cols.add(rs.getString(1).toLowerCase(Locale.ROOT));
                }
            }
        }
        return cols;
    }
}
