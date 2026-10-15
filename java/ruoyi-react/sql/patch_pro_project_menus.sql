-- 用户 pro / 123456 · 角色「项目管理员」· 项目管理双菜单
-- 密码 BCrypt（123456），部署时由脚本生成后替换 HASH_PLACEHOLDER

-- 角色
INSERT INTO sys_role (role_id, role_name, role_key, role_sort, data_scope, menu_check_strictly, dept_check_strictly, status, del_flag, create_by, create_time, remark)
SELECT 100, '项目管理员', 'project_admin', 3, '1', 1, 1, '0', '0', 'admin', sysdate(), '项目管理：对话 + 文件解析录入'
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM sys_role WHERE role_id = 100 OR role_key = 'project_admin');

-- 用户
INSERT INTO sys_user (user_id, dept_id, user_name, nick_name, user_type, email, phonenumber, sex, avatar, password, status, del_flag, login_ip, login_date, create_by, create_time, remark)
SELECT 100, 103, 'pro', '项目管理员', '00', 'pro@project.local', '13800000001', '0', '',
       'HASH_PLACEHOLDER',
       '0', '0', '', NULL, 'admin', sysdate(), '项目管理员账号'
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE user_id = 100 OR user_name = 'pro');

-- 用户-角色
INSERT IGNORE INTO sys_user_role (user_id, role_id) VALUES (100, 100);

-- 菜单：项目管理（目录）
INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
SELECT 2100, '项目管理', 0, 5, 'project', NULL, '', '', 1, 0, 'M', '0', '0', '', 'ProjectOutlined', 'admin', sysdate(), '项目管理目录'
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE menu_id = 2100);

-- 菜单：智能对话
INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
SELECT 2101, '智能对话', 2100, 1, 'chat', 'project/chat/index', '', '', 1, 0, 'C', '0', '0', 'project:chat:list', 'MessageOutlined', 'admin', sysdate(), 'RAG 智能对话'
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE menu_id = 2101);

-- 菜单：文件解析录入
INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
SELECT 2102, '文件解析录入', 2100, 2, 'parse', 'project/parse/index', '', '', 1, 0, 'C', '0', '0', 'project:parse:list', 'FileAddOutlined', 'admin', sysdate(), '立项文档解析录入'
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE menu_id = 2102);

-- 角色-菜单（项目管理员）
INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES
(100, 2100), (100, 2101), (100, 2102),
(100, 5), (100, 6);

-- 超管角色也显式挂上（非必须，admin 代码侧通常全量）
INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES
(1, 2100), (1, 2101), (1, 2102);
