# -*- coding: utf-8 -*-
from __future__ import annotations
import pathlib
import pymysql

HOST = "192.168.1.57"
NAMES = {
    2090: "\u5b50\u7cfb\u7edf\u4e2d\u5fc3",
    2091: "\u5b50\u7cfb\u7edf\u5217\u8868",
    2200: "\u95f2\u9c7c\u53d1\u8d27",
    2201: "\u95f2\u9c7c\u81ea\u52a8\u53d1\u8d27",
}
SQL_PATH = pathlib.Path(r"E:\ai-pro\project_agent\java\ruoyi-react\sql\patch_portal_subsystems.sql")
tpl = """-- Portal + xianyu-auto subsystem menus (idempotent by menu_id)
-- Portal UI uses static route /portal/home (layout:false); menus are hidden from sidebar.

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
SELECT 2090, '{n2090}', 0, 0, 'portal', NULL, '', '', 1, 0, 'M', '1', '0', '', 'AppstoreOutlined', 'admin', sysdate(), 'subsystem portal (hidden)'
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE menu_id = 2090);

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
SELECT 2091, '{n2091}', 2090, 1, 'home', 'portal/home/index', '', '', 1, 0, 'C', '1', '0', 'portal:home:view', 'AppstoreOutlined', 'admin', sysdate(), 'static /portal/home'
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE menu_id = 2091);

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
SELECT 2200, '{n2200}', 0, 6, 'subsystem', NULL, '', '', 1, 0, 'M', '0', '0', '', 'ShopOutlined', 'admin', sysdate(), 'external subsystems'
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE menu_id = 2200);

INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark)
SELECT 2201, '{n2201}', 2200, 1, 'xianyu', 'subsystem/xianyu/index', '', '', 1, 0, 'C', '0', '0', 'subsystem:xianyu:view', 'ShopOutlined', 'admin', sysdate(), 'iframe xianyu-auto :12400'
FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM sys_menu WHERE menu_id = 2201);

INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES
(1, 2090), (1, 2091),
(1, 2200), (1, 2201);
"""
SQL_PATH.write_text(tpl.format(n2090=NAMES[2090], n2091=NAMES[2091], n2200=NAMES[2200], n2201=NAMES[2201]), encoding="utf-8")
print("rewrote sql")
conn = pymysql.connect(host=HOST, port=3306, user="root", password="root123456", database="ry", charset="utf8mb4", connect_timeout=5, read_timeout=15, write_timeout=15, autocommit=True)
with conn.cursor() as cur:
    for mid, name in NAMES.items():
        cur.execute("UPDATE sys_menu SET menu_name=%s WHERE menu_id=%s", (name, mid))
        print("updated", mid, name.encode("unicode_escape").decode(), "rows", cur.rowcount)
    cur.execute("SELECT menu_id, HEX(menu_name) FROM sys_menu WHERE menu_id IN (2090,2091,2200,2201)")
    for r in cur.fetchall():
        print(r)
conn.close()
print("done")
