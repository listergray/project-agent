"""Restore super-admin (role_id=1) to all menus + all data scope."""
from __future__ import annotations

import subprocess
from pathlib import Path

sql = """
-- 超管：全部数据权限
UPDATE sys_role
SET data_scope = '1', status = '0', del_flag = '0', role_key = 'admin'
WHERE role_id = 1;

-- 确保 admin 用户绑定超管角色
INSERT IGNORE INTO sys_user_role (user_id, role_id) VALUES (1, 1);
UPDATE sys_user SET status = '0', del_flag = '0' WHERE user_id = 1;

-- 超管角色拥有全部菜单（含按钮权限）
DELETE FROM sys_role_menu WHERE role_id = 1;
INSERT INTO sys_role_menu (role_id, menu_id)
SELECT 1, menu_id FROM sys_menu;

SELECT 'ROLE' AS t, role_id, role_name, role_key, data_scope, status FROM sys_role WHERE role_id = 1;
SELECT 'UR' AS t, user_id, role_id FROM sys_user_role WHERE user_id = 1;
SELECT 'RM' AS t, COUNT(*) AS cnt FROM sys_role_menu WHERE role_id = 1;
"""

path = Path(__file__).with_name("_fix_admin_perms.sql")
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
raise SystemExit(proc.returncode)
