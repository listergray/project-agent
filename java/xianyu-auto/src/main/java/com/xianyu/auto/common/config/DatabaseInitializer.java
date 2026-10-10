package com.xianyu.auto.common.config;

import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

/**
 * 数据库增量补丁（MySQL）：缺列时 ALTER ADD。
 * 主表结构见 schema.sql。
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class DatabaseInitializer {

    private final JdbcTemplate jdbcTemplate;

    @PostConstruct
    public void init() {
        addColumnsIfMissing("t_account", new String[][]{
                {"ws_token_expire_at", "BIGINT NULL"},
                {"access_token", "TEXT NULL"},
                {"refresh_token", "TEXT NULL"},
                {"access_token_expire_at", "BIGINT NULL"},
                {"refresh_token_expire_at", "BIGINT NULL"},
                {"auth_type", "VARCHAR(20) DEFAULT 'COOKIE'"}
        });
        addColumnsIfMissing("t_product", new String[][]{
                {"account_id", "BIGINT NULL"},
                {"title", "VARCHAR(500) NULL"},
                {"price", "DECIMAL(12,2) NULL"},
                {"original_price", "DECIMAL(12,2) NULL"},
                {"stock_qty", "INT DEFAULT 0"},
                {"shelf_status", "VARCHAR(20) DEFAULT 'OFF_SHELF'"},
                {"images_json", "TEXT NULL"},
                {"category_id", "VARCHAR(50) NULL"},
                {"province", "VARCHAR(50) NULL"},
                {"city", "VARCHAR(50) NULL"},
                {"sync_status", "VARCHAR(20) DEFAULT 'LOCAL'"},
                {"last_synced_at", "BIGINT NULL"}
        });
        addColumnsIfMissing("t_delivery_rule", new String[][]{
                {"auto_confirm", "INT NOT NULL DEFAULT 1"},
                {"delay_seconds", "INT NOT NULL DEFAULT 0"}
        });
        addColumnsIfMissing("t_delivery_log", new String[][]{
                {"order_id", "VARCHAR(64) NULL"},
                {"inventory_id", "BIGINT NULL"},
                {"consign_status", "VARCHAR(20) NULL"}
        });
        clearStaleLoginErrors();
        log.info("DatabaseInitializer 完成（MySQL）");
    }

    private void clearStaleLoginErrors() {
        try {
            int n = jdbcTemplate.update(
                    "UPDATE t_account SET last_error = NULL WHERE last_error IS NOT NULL "
                            + "AND status IN ('ONLINE','OFFLINE','CONNECTING')");
            if (n > 0) {
                log.info("清除残留 last_error: {} 行", n);
            }
        } catch (Exception e) {
            log.warn("清除残留 last_error 失败: {}", e.getMessage());
        }
    }

    private void addColumnsIfMissing(String table, String[][] columns) {
        for (String[] col : columns) {
            String columnName = col[0];
            String columnType = col[1];
            try {
                if (!columnExists(table, columnName)) {
                    jdbcTemplate.execute(String.format(
                            "ALTER TABLE %s ADD COLUMN %s %s", table, columnName, columnType));
                    log.info("添加列: {}.{}", table, columnName);
                }
            } catch (Exception e) {
                log.warn("添加列 {}.{} 失败: {}", table, columnName, e.getMessage());
            }
        }
    }

    private boolean columnExists(String tableName, String columnName) {
        try {
            Integer cnt = jdbcTemplate.queryForObject(
                    "SELECT COUNT(*) FROM information_schema.COLUMNS "
                            + "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ? AND COLUMN_NAME = ?",
                    Integer.class, tableName, columnName);
            return cnt != null && cnt > 0;
        } catch (Exception e) {
            log.warn("检查列是否存在失败: {}", e.getMessage());
            return false;
        }
    }
}
