-- douyin-auto episode publish ledger (MySQL / twlmac)
CREATE DATABASE IF NOT EXISTS douyin_auto
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE douyin_auto;

CREATE TABLE IF NOT EXISTS dy_meta (
  meta_key   VARCHAR(64)  NOT NULL,
  meta_value VARCHAR(512) NOT NULL,
  updated_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (meta_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dy_episode (
  ep           INT          NOT NULL COMMENT 'Episode number, e.g. 32 for EP.32',
  status       VARCHAR(32)  NOT NULL COMMENT 'LEGACY|PENDING|RUNNING|SUCCESS|FAILED',
  video_name   VARCHAR(255) NULL,
  video_path   VARCHAR(1024) NULL,
  title        VARCHAR(512) NULL,
  cover_path   VARCHAR(1024) NULL,
  location     VARCHAR(128) NULL,
  job_id       VARCHAR(64)  NULL,
  message      VARCHAR(1024) NULL,
  published_at DATETIME     NULL,
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (ep),
  KEY idx_dy_episode_status (status),
  KEY idx_dy_episode_published (published_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
