-- ============================================================
-- 首次启动 MySQL 自动执行：建业务库 + 4 张业务表 + 插 Mock 数据
-- 数据与 `src/project_agent/tools/rag_tools.py` 内存 Mock 完全一致，
-- 这样把 RAG 知识库 工具层从"内存版"切到"真实 MySQL 版"时，上层 Agent 逻辑一行都不用改。
-- ============================================================

CREATE DATABASE IF NOT EXISTS `project_agent_dw` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE `project_agent_meta`;

-- ------------------------------------------------------------
-- 1. 资产表（ASSET 模块）
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `dim_asset`;
CREATE TABLE `dim_asset` (
    `code`        VARCHAR(64)   NOT NULL COMMENT '资产编码（PK）',
    `name`        VARCHAR(256)  NOT NULL COMMENT '资产名称',
    `category`    VARCHAR(32)   NOT NULL DEFAULT 'ASSET' COMMENT '模块分类 ASSET/HR/FIX',
    `stock`       INT           NOT NULL DEFAULT 0 COMMENT '库存数量',
    `unit_price`  DECIMAL(12,2) NOT NULL DEFAULT 0 COMMENT '单价（元）',
    `amount`      DECIMAL(14,2) NOT NULL DEFAULT 0 COMMENT '总价 = stock*unit_price',
    `owner`       VARCHAR(128)  NOT NULL DEFAULT '' COMMENT '责任人',
    `status`      VARCHAR(32)   NOT NULL DEFAULT '在用' COMMENT '在用/闲置/维修中/报废',
    `supplier`    VARCHAR(256)  NOT NULL DEFAULT '' COMMENT '供应商',
    `location`    VARCHAR(512)  NOT NULL DEFAULT '' COMMENT '存放位置',
    `updated_at`  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`code`),
    KEY `idx_status` (`status`),
    KEY `idx_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='资产维表（与工具层 Mock 一致）';

INSERT INTO `dim_asset` VALUES
('FS-2024-0876','联想ThinkStation K-C2 图形工作站','ASSET',37,12800.00,473600.00,'张志远','在用','联想北京代理','研发中心A栋3F-305机柜','2024-12-18 09:23:11'),
('FS-2024-0902','华为MateBook X Pro 笔记本','ASSET',156,8999.00,1403844.00,'李欣怡','在用','华为企业购','销售部1号楼1F-资产库','2024-12-20 14:05:42'),
('FS-2024-1021','戴尔PowerEdge R760 机架服务器','ASSET',8,46800.00,374400.00,'王建国（运维）','在用','戴尔企业直销','IDC机房A区-R07机架','2024-12-02 11:40:22'),
('FS-2023-0344','爱普生L6498 多功能一体机','ASSET',3,3599.00,10797.00,'行政部','维修中','京东企业购','行政部2F-文印区','2024-11-28 16:10:00'),
('HR-FIX-0044','Herman Miller Aeron 人体工学椅','ASSET',128,9600.00,1228800.00,'HR 行政采购','在用','Herman Miller 总代','全办公楼工位（按人分配）','2024-09-15 10:00:00');

-- ------------------------------------------------------------
-- 2. 员工维表（HR 模块）
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `dim_employee`;
CREATE TABLE `dim_employee` (
    `code`        VARCHAR(32)  NOT NULL COMMENT '工号 PK HR-EMP-XXXX',
    `name`        VARCHAR(64)  NOT NULL,
    `dept`        VARCHAR(128) NOT NULL COMMENT '部门',
    `title`       VARCHAR(128) NOT NULL COMMENT '岗位',
    `level`       VARCHAR(16)  NOT NULL COMMENT '职级 P4/P5/P6…',
    `status`      VARCHAR(16)  NOT NULL DEFAULT '在职',
    `manager`     VARCHAR(128) NOT NULL DEFAULT '' COMMENT '直属上级',
    `entry_date`  DATE         NOT NULL,
    `updated_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`code`),
    KEY `idx_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='员工维表';

INSERT INTO `dim_employee` VALUES
('HR-EMP-1001','陈昊','研发中心-架构组','高级后端工程师（Agent 方向）','P6','在职','刘志强（架构总监）','2021-03-15',NOW()),
('HR-EMP-1023','林晓雯','人力资源部-招聘组','资深招聘专员','P5','在职','周敏（HRBP总监）','2020-07-01',NOW()),
('HR-EMP-0856','赵天宇','财务部-报表组','报表会计','P4','在职','孙丽华（财务总监）','2022-08-22',NOW()),
('HR-EMP-0720','郑瑞','研发中心-算法组','算法工程师（NLP）','P5','在职','陈昊','2023-02-14',NOW());

-- ------------------------------------------------------------
-- 3. 发票/付款事实表（FIN 模块）
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `fct_invoice`;
CREATE TABLE `fct_invoice` (
    `code`        VARCHAR(32)    NOT NULL COMMENT '单据编码 PK',
    `type`        VARCHAR(32)    NOT NULL COMMENT '类型：增值税专票/普票/报销单/付款单',
    `amount`      DECIMAL(14,2)  NOT NULL DEFAULT 0 COMMENT '金额（元）',
    `payee`       VARCHAR(256)   NOT NULL DEFAULT '' COMMENT '收款方',
    `payer`       VARCHAR(256)   NOT NULL DEFAULT '' COMMENT '付款方',
    `period`      VARCHAR(16)    NOT NULL DEFAULT '' COMMENT '所属账期 YYYY-MM',
    `status`      VARCHAR(16)    NOT NULL DEFAULT '待审核',
    `created_at`  DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`code`),
    KEY `idx_period` (`period`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='财务单据事实表';

INSERT INTO `fct_invoice` VALUES
('FIN-INV-2024-001','增值税专票',182600.00,'联想（北京）有限公司','本公司-主体A','2024-12','已入账',NOW()),
('FIN-INV-2024-002','报销单',4820.50,'陈昊（员工报销）','本公司-主体A','2024-12','待审核',NOW()),
('FIN-INV-2024-003','增值税普票',374400.00,'戴尔（中国）有限公司','本公司-主体A','2024-11','已入账',NOW()),
('FIN-PAY-2024-117','付款单',140250.00,'华为技术有限公司','本公司-主体A','2024-12','已入账',NOW());

-- ------------------------------------------------------------
-- 4. 盘点模块 4 张业务表（供 代码助手 N2 生成的 Service 真连 MySQL 时使用）
-- ------------------------------------------------------------
USE `project_agent_dw`;

DROP TABLE IF EXISTS `t_inventory_sheet`;
CREATE TABLE `t_inventory_sheet` (
    `id`            BIGINT       NOT NULL AUTO_INCREMENT,
    `file_md5`      VARCHAR(64)  NOT NULL COMMENT 'Excel MD5，分布式锁键 + 幂等键',
    `file_name`     VARCHAR(256) NOT NULL DEFAULT '',
    `status`        VARCHAR(20)  NOT NULL DEFAULT 'IMPORTED' COMMENT 'IMPORTED/PREVIEWED/CONFIRMED/REJECTED',
    `row_count`     INT          NOT NULL DEFAULT 0,
    `bad_row_count` INT          NOT NULL DEFAULT 0,
    `op_user`       VARCHAR(128) NOT NULL DEFAULT '',
    `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_file_md5` (`file_md5`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='盘点单表头（代码助手 生成代码对应的真实表）';

DROP TABLE IF EXISTS `t_inventory_import_row`;
CREATE TABLE `t_inventory_import_row` (
    `id`            BIGINT        NOT NULL AUTO_INCREMENT,
    `sheet_id`      BIGINT        NOT NULL,
    `raw_code`      VARCHAR(128)  NOT NULL DEFAULT '' COMMENT 'Excel 原始近似编码',
    `matched_code`  VARCHAR(64)   NULL COMMENT '模糊匹配 Top1 的资产编码',
    `sim_score`     DECIMAL(5,4)  NOT NULL DEFAULT 0 COMMENT 'Top1 相似度',
    `actual_qty`    INT           NOT NULL DEFAULT 0 COMMENT '实盘数量',
    `sys_qty`       INT           NOT NULL DEFAULT 0 COMMENT '导入时系统库存',
    `diff`          INT           NOT NULL DEFAULT 0 COMMENT 'sys_qty - actual_qty',
    `top5_json`     JSON          NULL COMMENT 'Top5 候选编码快照',
    `status`        VARCHAR(20)   NOT NULL DEFAULT 'OK',
    PRIMARY KEY (`id`),
    KEY `idx_sheet_id` (`sheet_id`),
    KEY `idx_matched_code` (`matched_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='盘点单导入行（代码助手 InventoryImportMapper 对应）';

DROP TABLE IF EXISTS `t_asset`;
CREATE TABLE `t_asset` (
    `code`       VARCHAR(64)   NOT NULL,
    `name`       VARCHAR(256)  NOT NULL,
    `stock`      INT           NOT NULL DEFAULT 0,
    `unit_price` DECIMAL(12,2) NOT NULL DEFAULT 0,
    `owner`      VARCHAR(128)  NOT NULL DEFAULT '',
    `location`   VARCHAR(512)  NOT NULL DEFAULT '',
    `updated_at` DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='资产库存表（扣减的真正表）';

-- t_asset 初始化和 dim_asset 一致，方便 代码助手 生成的代码真实扣库存：
INSERT INTO `t_asset` (code, name, stock, unit_price, owner, location) VALUES
('FS-2024-0876','联想ThinkStation K-C2 图形工作站',37,12800.00,'张志远','研发中心A栋3F-305机柜'),
('FS-2024-0902','华为MateBook X Pro 笔记本',156,8999.00,'李欣怡','销售部1号楼1F-资产库'),
('FS-2024-1021','戴尔PowerEdge R760 机架服务器',8,46800.00,'王建国（运维）','IDC机房A区-R07机架'),
('FS-2023-0344','爱普生L6498 多功能一体机',3,3599.00,'行政部','行政部2F-文印区'),
('HR-FIX-0044','Herman Miller Aeron 人体工学椅',128,9600.00,'HR 行政采购','全办公楼工位（按人分配）');

DROP TABLE IF EXISTS `t_audit_log`;
CREATE TABLE `t_audit_log` (
    `id`         BIGINT       NOT NULL AUTO_INCREMENT,
    `op_type`    VARCHAR(32)  NOT NULL DEFAULT '' COMMENT 'CONFIRM/IMPORT/REJECT…',
    `op_user`    VARCHAR(128) NOT NULL DEFAULT '',
    `biz_id`     VARCHAR(128) NOT NULL DEFAULT '' COMMENT '关联业务主键',
    `before_json` JSON        NULL,
    `after_json`  JSON        NULL,
    `created_at` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_biz_created` (`biz_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作审计日志';
