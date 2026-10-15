-- Run this ON the MySQL host (192.168.1.46 / Docker) as a privileged user.
-- If you see: Host 'x.x.x.x' is not allowed to connect…

CREATE DATABASE IF NOT EXISTS `wodesuoyou`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY 'root123456';
ALTER USER 'root'@'%' IDENTIFIED BY 'root123456';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;

CREATE USER IF NOT EXISTS 'root'@'192.168.1.%' IDENTIFIED BY 'root123456';
ALTER USER 'root'@'192.168.1.%' IDENTIFIED BY 'root123456';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'192.168.1.%' WITH GRANT OPTION;

FLUSH PRIVILEGES;
