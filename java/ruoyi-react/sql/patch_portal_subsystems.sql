-- Portal + xianyu-auto subsystem menus (idempotent by menu_id)
-- Portal UI uses static route /portal/home (layout:false); menus are hidden from sidebar.

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
SELECT 2090, '子系统中心', 0, 0, 'portal', NULL, '', '', 1, 0, 'M', '1', '0', '', 'AppstoreOutlined', 'admin', sysdate(), 'subsystem portal (hidden)'
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE menu_id = 2090);

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
SELECT 2091, '子系统列表', 2090, 1, 'home', 'portal/home/index', '', '', 1, 0, 'C', '1', '0', 'portal:home:view', 'AppstoreOutlined', 'admin', sysdate(), 'static /portal/home'
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE menu_id = 2091);

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
SELECT 2200, '闲鱼发货', 0, 6, 'subsystem', NULL, '', '', 1, 0, 'M', '1', '0', '', 'ShopOutlined', 'admin', sysdate(), 'external subsystems'
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE menu_id = 2200);

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
SELECT 2201, '闲鱼自动发货', 2200, 1, 'xianyu', 'subsystem/xianyu/index', '', '', 1, 0, 'C', '1', '0', 'subsystem:xianyu:view', 'ShopOutlined', 'admin', sysdate(), 'iframe xianyu-auto :12400'
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE menu_id = 2201);

INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES
(1, 2090), (1, 2091),
(1, 2200), (1, 2201);
