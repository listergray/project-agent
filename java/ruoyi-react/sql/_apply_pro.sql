
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
VALUES (100, 103, 'pro', '项目管理员', '00', 'pro@project.local', '13800000001', '0', '', '$2a$10$afBvgKQJT0uOmsVSm2pbguR0YnFb30u0Py8X0RqIoNqaWzIXfaT7e', '0', '0', '', 'admin', NOW(), '项目管理员账号');

INSERT INTO sys_user_role (user_id, role_id) VALUES (100, 100);

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
VALUES
(2100, '项目管理', 0, 5, 'project', NULL, '', '', 1, 0, 'M', '0', '0', '', 'ProjectOutlined', 'admin', NOW(), '项目管理目录'),
(2101, '智能对话', 2100, 1, 'chat', 'project/chat/index', '', '', 1, 0, 'C', '0', '0', 'project:chat:list', 'MessageOutlined', 'admin', NOW(), 'RAG 智能对话'),
(2102, '文件解析录入', 2100, 2, 'parse', 'project/parse/index', '', '', 1, 0, 'C', '0', '0', 'project:parse:list', 'FileAddOutlined', 'admin', NOW(), '立项文档解析录入');

INSERT INTO sys_role_menu (role_id, menu_id) VALUES
(100, 2100), (100, 2101), (100, 2102), (100, 5), (100, 6),
(1, 2100), (1, 2101), (1, 2102);

SELECT 'USER', user_id, user_name, nick_name FROM sys_user WHERE user_name='pro';
SELECT 'ROLE', role_id, role_name FROM sys_role WHERE role_id=100;
SELECT 'MENU', menu_id, menu_name, parent_id, IFNULL(component,'') FROM sys_menu WHERE menu_id BETWEEN 2100 AND 2102;
SELECT 'UR', user_id, role_id FROM sys_user_role WHERE user_id=100;
