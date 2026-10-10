-- ============================================================
-- xx_erp MySQL Schema（闲鱼渠道 + ERP 底座）
-- 启动时 spring.sql.init 执行；CREATE IF NOT EXISTS 保证幂等
-- ============================================================

CREATE TABLE IF NOT EXISTS t_sys_user (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    username        VARCHAR(50)  NOT NULL,
    password_hash   VARCHAR(100) NOT NULL,
    nickname        VARCHAR(50),
    email           VARCHAR(100),
    phone           VARCHAR(20),
    role            VARCHAR(20)  NOT NULL DEFAULT 'USER',
    status          INT          NOT NULL DEFAULT 1,
    last_login_at   BIGINT,
    last_login_ip   VARCHAR(50),
    created_at      BIGINT       NOT NULL,
    updated_at      BIGINT       NOT NULL,
    deleted         INT          NOT NULL DEFAULT 0,
    UNIQUE KEY uk_sys_user_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS t_sys_config (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    config_key      VARCHAR(100) NOT NULL,
    config_value    TEXT,
    config_group    VARCHAR(50)  NOT NULL DEFAULT 'default',
    description     VARCHAR(255),
    created_at      BIGINT       NOT NULL,
    updated_at      BIGINT       NOT NULL,
    deleted         INT          NOT NULL DEFAULT 0,
    UNIQUE KEY uk_sys_config_key (config_key),
    KEY idx_sys_config_group (config_group)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS t_sys_log (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    operator        VARCHAR(50),
    action          VARCHAR(100) NOT NULL,
    method          VARCHAR(255),
    params          TEXT,
    result          TEXT,
    ip              VARCHAR(50),
    duration_ms     BIGINT,
    error_msg       TEXT,
    created_at      BIGINT       NOT NULL,
    deleted         INT          NOT NULL DEFAULT 0,
    KEY idx_sys_log_operator (operator),
    KEY idx_sys_log_action (action),
    KEY idx_sys_log_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS t_account (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    nickname        VARCHAR(100),
    user_id         VARCHAR(50),
    user_nick       VARCHAR(100),
    avatar          VARCHAR(500),
    cookie_text     TEXT,
    device_id       VARCHAR(128),
    ws_token        TEXT,
    ws_token_expire_at BIGINT,
    access_token    TEXT,
    refresh_token   TEXT,
    access_token_expire_at BIGINT,
    refresh_token_expire_at BIGINT,
    auth_type       VARCHAR(20) DEFAULT 'COOKIE',
    status          VARCHAR(20)  NOT NULL DEFAULT 'OFFLINE',
    last_error      TEXT,
    last_login_at   BIGINT,
    last_keepalive_at BIGINT,
    auto_start      INT          NOT NULL DEFAULT 0,
    created_at      BIGINT       NOT NULL,
    updated_at      BIGINT       NOT NULL,
    deleted         INT          NOT NULL DEFAULT 0,
    KEY idx_account_user_id (user_id),
    KEY idx_account_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS t_product (
    id                  BIGINT PRIMARY KEY AUTO_INCREMENT,
    account_id          BIGINT,
    name                VARCHAR(200) NOT NULL,
    title               VARCHAR(500),
    xianyu_item_id      VARCHAR(100),
    description         TEXT,
    price               DECIMAL(12,2),
    original_price      DECIMAL(12,2),
    stock_qty           INT DEFAULT 0,
    shelf_status        VARCHAR(20) DEFAULT 'OFF_SHELF',
    images_json         TEXT,
    category_id         VARCHAR(50),
    province            VARCHAR(50),
    city                VARCHAR(50),
    delivery_content    TEXT,
    default_inventory_id BIGINT,
    auto_delivery       INT          NOT NULL DEFAULT 0,
    status              VARCHAR(20)  NOT NULL DEFAULT 'ENABLED',
    sync_status         VARCHAR(20) DEFAULT 'LOCAL',
    last_synced_at      BIGINT,
    created_at          BIGINT       NOT NULL,
    updated_at          BIGINT       NOT NULL,
    deleted             INT          NOT NULL DEFAULT 0,
    KEY idx_product_xianyu_item_id (xianyu_item_id),
    KEY idx_product_account (account_id),
    KEY idx_product_shelf (shelf_status),
    KEY idx_product_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS t_inventory (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    product_id      BIGINT,
    code            VARCHAR(100),
    type            VARCHAR(20)  NOT NULL,
    content         TEXT         NOT NULL,
    stock           INT          NOT NULL DEFAULT 0,
    used_count      INT          NOT NULL DEFAULT 0,
    status          VARCHAR(20)  NOT NULL DEFAULT 'AVAILABLE',
    created_at      BIGINT       NOT NULL,
    updated_at      BIGINT       NOT NULL,
    deleted         INT          NOT NULL DEFAULT 0,
    KEY idx_inventory_product (product_id),
    KEY idx_inventory_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS t_delivery_rule (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    name            VARCHAR(200) NOT NULL,
    account_id      BIGINT,
    product_id      BIGINT,
    trigger_type    VARCHAR(20)  NOT NULL,
    trigger_keywords TEXT,
    delivery_content TEXT,
    inventory_id    BIGINT,
    auto_confirm    INT          NOT NULL DEFAULT 1,
    delay_seconds   INT          NOT NULL DEFAULT 0,
    priority        INT          NOT NULL DEFAULT 0,
    enabled         INT          NOT NULL DEFAULT 1,
    created_at      BIGINT       NOT NULL,
    updated_at      BIGINT       NOT NULL,
    deleted         INT          NOT NULL DEFAULT 0,
    KEY idx_delivery_rule_account (account_id),
    KEY idx_delivery_rule_product (product_id),
    KEY idx_delivery_rule_trigger (trigger_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS t_delivery_log (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    account_id      BIGINT,
    account_nickname VARCHAR(200),
    rule_id         BIGINT,
    rule_name       VARCHAR(200),
    conversation_id VARCHAR(100),
    buyer_id        VARCHAR(50),
    buyer_nick      VARCHAR(100),
    item_id         VARCHAR(50),
    item_name       VARCHAR(200),
    order_id        VARCHAR(64),
    delivery_content TEXT,
    inventory_code  VARCHAR(100),
    inventory_id    BIGINT,
    consign_status  VARCHAR(20),
    status          VARCHAR(20)  NOT NULL,
    error_msg       TEXT,
    created_at      BIGINT       NOT NULL,
    updated_at      BIGINT       NOT NULL,
    deleted         INT          NOT NULL DEFAULT 0,
    KEY idx_delivery_log_account (account_id),
    KEY idx_delivery_log_status (status),
    KEY idx_delivery_log_created (created_at),
    KEY idx_delivery_log_order (account_id, order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS t_order (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    account_id      BIGINT       NOT NULL,
    order_id        VARCHAR(64)  NOT NULL,
    item_id         VARCHAR(50),
    item_title      VARCHAR(500),
    buyer_id        VARCHAR(50),
    buyer_nick      VARCHAR(100),
    conversation_id VARCHAR(100),
    status          VARCHAR(30)  NOT NULL DEFAULT 'WAIT_PAY',
    pay_amount      DECIMAL(12,2),
    paid_at         BIGINT,
    shipped_at      BIGINT,
    consign_status  VARCHAR(20),
    raw_json        MEDIUMTEXT,
    created_at      BIGINT       NOT NULL,
    updated_at      BIGINT       NOT NULL,
    deleted         INT          NOT NULL DEFAULT 0,
    UNIQUE KEY uk_order_account_oid (account_id, order_id),
    KEY idx_order_status (status),
    KEY idx_order_buyer (buyer_id),
    KEY idx_order_item (item_id),
    KEY idx_order_updated (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS t_keyword_rule (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    account_id      BIGINT       NOT NULL,
    item_id         VARCHAR(50),
    keyword         VARCHAR(255) NOT NULL,
    match_type      VARCHAR(20)  NOT NULL,
    reply_content   TEXT         NOT NULL,
    priority        INT          NOT NULL DEFAULT 0,
    status          VARCHAR(20)  NOT NULL DEFAULT 'ENABLED',
    created_at      BIGINT       NOT NULL,
    updated_at      BIGINT       NOT NULL,
    deleted         INT          NOT NULL DEFAULT 0,
    KEY idx_keyword_account (account_id),
    KEY idx_keyword_item (item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS t_chat_message (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    account_id      BIGINT,
    conversation_id VARCHAR(100) NOT NULL,
    sender          VARCHAR(20)  NOT NULL,
    sender_id       VARCHAR(50),
    sender_nick     VARCHAR(100),
    item_id         VARCHAR(50),
    msg_type        VARCHAR(20)  NOT NULL DEFAULT 'TEXT',
    content         TEXT,
    raw_data        MEDIUMTEXT,
    read_status     INT          NOT NULL DEFAULT 0,
    created_at      BIGINT       NOT NULL,
    deleted         INT          NOT NULL DEFAULT 0,
    KEY idx_msg_account (account_id),
    KEY idx_msg_conv (conversation_id),
    KEY idx_msg_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS t_ai_context (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    conversation_id VARCHAR(100) NOT NULL,
    history_json    TEXT,
    token_count     INT          NOT NULL DEFAULT 0,
    updated_at      BIGINT       NOT NULL,
    UNIQUE KEY uk_ai_context_conv (conversation_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS t_notification (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    account_id      BIGINT,
    type            VARCHAR(50)  NOT NULL,
    title           VARCHAR(200) NOT NULL,
    content         TEXT,
    read_status     INT          NOT NULL DEFAULT 0,
    created_at      BIGINT       NOT NULL,
    KEY idx_notify_account (account_id),
    KEY idx_notify_read (read_status),
    KEY idx_notify_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS t_webhook_config (
    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
    name            VARCHAR(100) NOT NULL,
    type            VARCHAR(20)  NOT NULL,
    url             VARCHAR(500) NOT NULL,
    enabled         INT          NOT NULL DEFAULT 1,
    event_filter    TEXT,
    created_at      BIGINT       NOT NULL,
    updated_at      BIGINT       NOT NULL,
    deleted         INT          NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT IGNORE INTO t_sys_config (config_key, config_value, config_group, description, created_at, updated_at, deleted)
VALUES ('system.init.admin.password', 'admin123', 'system', '首次启动初始化的 admin 密码（首次启动后会清除）', 0, 0, 0);
