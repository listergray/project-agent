"""Idempotent apply: pro user + project menus."""
from __future__ import annotations

import bcrypt
import subprocess
from pathlib import Path

HASH = bcrypt.hashpw(b"123456", bcrypt.gensalt(rounds=10)).decode().replace("$2b$", "$2a$")

sql = f"""
SET FOREIGN_KEY_CHECKS=0;
DELETE FROM sys_role_menu WHERE role_id=100 OR menu_id IN (2100,2101,2102);
DELETE FROM sys_user_role WHERE user_id=100 OR role_id=100;
DELETE FROM sys_user WHERE user_id=100 OR user_name='pro';
DELETE FROM sys_role WHERE role_id=100 OR role_key='project_admin';
DELETE FROM sys_menu WHERE menu_id IN (2100,2101,2102);
SET FOREIGN_KEY_CHECKS=1;

INSERT INTO sys_role (role_id, role_name, role_key, role_sort, data_scope, menu_check_strictly, dept_check_strictly, status, del_flag, create_by, create_time, remark)
VALUES (100, '项目管理员', 'project_admin', 3, '1', 1, 1, '0', '0', 'admin', NOW(), '项目管理：对话 + 文件解析录入');

INSERT INTO sys_user (user_id, dept_id, user_name, nick_name, user_type, email, phonenumber, sex, avatar, password, status, del_flag, login_ip, create_by, create_time, remark)
VALUES (100, 103, 'pro', '项目管理员', '00', 'pro@project.local', '13800000001', '0', '', '{HASH}', '0', '0', '', 'admin', NOW(), '项目管理员账号');

INSERT INTO sys_user_role (user_id, role_id) VALUES (100, 100);

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
VALUES
(2100, '项目管理', 0, 5, 'project', NULL, '', '', 1, 0, 'M', '0', '0', '', 'ProjectOutlined', 'admin', NOW(), '项目管理目录'),
(2101, '智能对话', 2100, 1, 'chat', 'project/chat/index', '', '', 1, 0, 'C', '0', '0', 'project:chat:list', 'MessageOutlined', 'admin', NOW(), 'RAG 智能对话'),
(2102, '文件解析录入', 2100, 2, 'parse', 'project/parse/index', '', '', 1, 0, 'C', '0', '0', 'project:parse:list', 'FileAddOutlined', 'admin', NOW(), '立项文档解析录入');

INSERT INTO sys_role_menu (role_id, menu_id) VALUES
(100, 2100), (100, 2101), (100, 2102), (100, 5), (100, 6);

-- 超管始终拥有全部菜单 + 全部数据权限（避免只挂项目菜单）
UPDATE sys_role SET data_scope='1', status='0', del_flag='0' WHERE role_id=1;
INSERT IGNORE INTO sys_user_role (user_id, role_id) VALUES (1, 1);
DELETE FROM sys_role_menu WHERE role_id=1;
INSERT INTO sys_role_menu (role_id, menu_id) SELECT 1, menu_id FROM sys_menu;

SELECT 'USER', user_id, user_name, nick_name FROM sys_user WHERE user_name='pro';
SELECT 'ROLE', role_id, role_name FROM sys_role WHERE role_id=100;
SELECT 'MENU', menu_id, menu_name, parent_id, IFNULL(component,'') FROM sys_menu WHERE menu_id BETWEEN 2100 AND 2102;
SELECT 'UR', user_id, role_id FROM sys_user_role WHERE user_id=100;
SELECT 'ADMIN_RM', COUNT(*) FROM sys_role_menu WHERE role_id=1;
"""

path = Path(r"E:\ai-pro\project_agent\java\ruoyi-react\sql\_apply_pro.sql")
path.write_text(sql, encoding="utf-8")

proc = subprocess.run(
    [
        "docker",
        "exec",
        "-i",
        "mysql-resume",
        "mysql",
        "-uroot",
        "-proot123456",
        "--default-character-set=utf8mb4",
        "ry",
    ],
    input=path.read_bytes(),
    capture_output=True,
)
print((proc.stdout or b"").decode("utf-8", errors="ignore"))
print((proc.stderr or b"").decode("utf-8", errors="ignore"))
print("exit", proc.returncode)
print("ok_hash", bcrypt.checkpw(b"123456", HASH.encode()), HASH[:28])
