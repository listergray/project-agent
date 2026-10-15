
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
