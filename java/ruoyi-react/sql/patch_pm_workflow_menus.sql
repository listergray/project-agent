-- PM workflow MVP menus 2103-2109 + role demo users (password 123456)
SET FOREIGN_KEY_CHECKS=0;
DELETE FROM sys_role_menu WHERE role_id BETWEEN 101 AND 106 OR menu_id BETWEEN 2103 AND 2109;
DELETE FROM sys_user_role WHERE user_id BETWEEN 101 AND 106 OR role_id BETWEEN 101 AND 106;
DELETE FROM sys_user WHERE user_id BETWEEN 101 AND 106;
DELETE FROM sys_role WHERE role_id BETWEEN 101 AND 106;
DELETE FROM sys_menu WHERE menu_id BETWEEN 2103 AND 2109;
SET FOREIGN_KEY_CHECKS=1;

INSERT INTO sys_role (role_id, role_name, role_key, role_sort, data_scope, menu_check_strictly, dept_check_strictly, status, del_flag, create_by, create_time, remark) VALUES
(101, '项目经办', 'pm_applicant', 10, '1', 1, 1, '0', '0', 'admin', NOW(), 'pm'),
(102, '一次审核岗', 'pm_basic_auditor', 11, '1', 1, 1, '0', '0', 'admin', NOW(), 'pm'),
(103, '二次审核岗', 'pm_extend_auditor', 12, '1', 1, 1, '0', '0', 'admin', NOW(), 'pm'),
(104, '购买联审岗', 'pm_purchase', 13, '1', 1, 1, '0', '0', 'admin', NOW(), 'pm'),
(105, '财务联审岗', 'pm_finance', 14, '1', 1, 1, '0', '0', 'admin', NOW(), 'pm'),
(106, '分管领导', 'pm_leader', 15, '1', 1, 1, '0', '0', 'admin', NOW(), 'pm');

INSERT INTO sys_user (user_id, dept_id, user_name, nick_name, user_type, email, phonenumber, sex, avatar, password, status, del_flag, login_ip, create_by, create_time, remark) VALUES
(101, 103, 'pm_biz', '业务经办', '00', 'pm_biz@project.local', '13800000101', '0', '', '$2a$10$afBvgKQJT0uOmsVSm2pbguR0YnFb30u0Py8X0RqIoNqaWzIXfaT7e', '0', '0', '', 'admin', NOW(), 'pm'),
(102, 103, 'pm_office', '项目办审核', '00', 'pm_office@project.local', '13800000102', '0', '', '$2a$10$afBvgKQJT0uOmsVSm2pbguR0YnFb30u0Py8X0RqIoNqaWzIXfaT7e', '0', '0', '', 'admin', NOW(), 'pm'),
(103, 103, 'pm_tech', '归口审核', '00', 'pm_tech@project.local', '13800000103', '0', '', '$2a$10$afBvgKQJT0uOmsVSm2pbguR0YnFb30u0Py8X0RqIoNqaWzIXfaT7e', '0', '0', '', 'admin', NOW(), 'pm'),
(104, 103, 'pm_buy', '采购联审', '00', 'pm_buy@project.local', '13800000104', '0', '', '$2a$10$afBvgKQJT0uOmsVSm2pbguR0YnFb30u0Py8X0RqIoNqaWzIXfaT7e', '0', '0', '', 'admin', NOW(), 'pm'),
(105, 103, 'pm_fin', '财务联审', '00', 'pm_fin@project.local', '13800000105', '0', '', '$2a$10$afBvgKQJT0uOmsVSm2pbguR0YnFb30u0Py8X0RqIoNqaWzIXfaT7e', '0', '0', '', 'admin', NOW(), 'pm'),
(106, 103, 'pm_lead', '分管领导', '00', 'pm_lead@project.local', '13800000106', '0', '', '$2a$10$afBvgKQJT0uOmsVSm2pbguR0YnFb30u0Py8X0RqIoNqaWzIXfaT7e', '0', '0', '', 'admin', NOW(), 'pm');

INSERT INTO sys_user_role (user_id, role_id) VALUES
(101, 101), (102, 102), (103, 103), (104, 104), (105, 105), (106, 106);

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark) VALUES
(2103, '项目台账', 2100, 3, 'ledger', 'project/ledger/index', '', '', 1, 0, 'C', '0', '0', 'project:pm:list', 'ProfileOutlined', 'admin', NOW(), 'pm'),
(2104, '基础信息录入', 2100, 4, 'basic', 'project/basic/index', '', '', 1, 0, 'C', '0', '0', 'project:pm:basic:edit', 'FormOutlined', 'admin', NOW(), 'pm'),
(2105, '扩展信息录入', 2100, 5, 'extend', 'project/extend/index', '', '', 1, 0, 'C', '0', '0', 'project:pm:extend:edit', 'FileTextOutlined', 'admin', NOW(), 'pm'),
(2106, '一次审核', 2100, 6, 'audit-basic', 'project/audit/basic', '', '', 1, 0, 'C', '0', '0', 'project:pm:audit:basic', 'AuditOutlined', 'admin', NOW(), 'pm'),
(2107, '二次审核', 2100, 7, 'audit-extend', 'project/audit/extend', '', '', 1, 0, 'C', '0', '0', 'project:pm:audit:extend', 'SolutionOutlined', 'admin', NOW(), 'pm'),
(2108, '购买联审', 2100, 8, 'audit-purchase', 'project/audit/purchase', '', '', 1, 0, 'C', '0', '0', 'project:pm:audit:purchase', 'ShoppingOutlined', 'admin', NOW(), 'pm'),
(2109, '财务联审', 2100, 9, 'audit-finance', 'project/audit/finance', '', '', 1, 0, 'C', '0', '0', 'project:pm:audit:finance', 'AccountBookOutlined', 'admin', NOW(), 'pm');

INSERT INTO sys_role_menu (role_id, menu_id) VALUES
(101, 2100), (101, 2103), (101, 2104), (101, 2105),
(102, 2100), (102, 2103), (102, 2106),
(103, 2100), (103, 2103), (103, 2107),
(104, 2100), (104, 2103), (104, 2108),
(105, 2100), (105, 2103), (105, 2109),
(106, 2100), (106, 2103);
INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES
(1, 2103), (1, 2104), (1, 2105), (1, 2106), (1, 2107), (1, 2108), (1, 2109),
(100, 2103), (100, 2104), (100, 2105), (100, 2106), (100, 2107), (100, 2108), (100, 2109);

