# -*- coding: utf-8 -*-
from pathlib import Path


def u(*codes):
    return "".join(chr(int(c, 16)) for c in codes)


PWD = "$2a$10$afBvgKQJT0uOmsVSm2pbguR0YnFb30u0Py8X0RqIoNqaWzIXfaT7e"

roles = [
    (101, u("9879", "76ee", "7ecf", "529e"), "pm_applicant", 10),
    (102, u("4e00", "6b21", "5ba1", "6838", "5c97"), "pm_basic_auditor", 11),
    (103, u("4e8c", "6b21", "5ba1", "6838", "5c97"), "pm_extend_auditor", 12),
    (104, u("8d2d", "4e70", "8054", "5ba1", "5c97"), "pm_purchase", 13),
    (105, u("8d22", "52a1", "8054", "5ba1", "5c97"), "pm_finance", 14),
    (106, u("5206", "7ba1", "9886", "5bfc"), "pm_leader", 15),
]
users = [
    (101, "pm_biz", u("4e1a", "52a1", "7ecf", "529e")),
    (102, "pm_office", u("9879", "76ee", "529e", "5ba1", "6838")),
    (103, "pm_tech", u("5f52", "53e3", "5ba1", "6838")),
    (104, "pm_buy", u("91c7", "8d2d", "8054", "5ba1")),
    (105, "pm_fin", u("8d22", "52a1", "8054", "5ba1")),
    (106, "pm_lead", u("5206", "7ba1", "9886", "5bfc")),
]
menus = [
    (2103, u("9879", "76ee", "53f0", "8d26"), 3, "ledger", "project/ledger/index", "project:pm:list", "ProfileOutlined"),
    (2104, u("57fa", "7840", "4fe1", "606f", "5f55", "5165"), 4, "basic", "project/basic/index", "project:pm:basic:edit", "FormOutlined"),
    (2105, u("6269", "5c55", "4fe1", "606f", "5f55", "5165"), 5, "extend", "project/extend/index", "project:pm:extend:edit", "FileTextOutlined"),
    (2106, u("4e00", "6b21", "5ba1", "6838"), 6, "audit-basic", "project/audit/basic", "project:pm:audit:basic", "AuditOutlined"),
    (2107, u("4e8c", "6b21", "5ba1", "6838"), 7, "audit-extend", "project/audit/extend", "project:pm:audit:extend", "SolutionOutlined"),
    (2108, u("8d2d", "4e70", "8054", "5ba1"), 8, "audit-purchase", "project/audit/purchase", "project:pm:audit:purchase", "ShoppingOutlined"),
    (2109, u("8d22", "52a1", "8054", "5ba1"), 9, "audit-finance", "project/audit/finance", "project:pm:audit:finance", "AccountBookOutlined"),
]

lines = [
    "-- PM workflow MVP menus 2103-2109 + role demo users (password 123456)",
    "SET FOREIGN_KEY_CHECKS=0;",
    "DELETE FROM sys_role_menu WHERE role_id BETWEEN 101 AND 106 OR menu_id BETWEEN 2103 AND 2109;",
    "DELETE FROM sys_user_role WHERE user_id BETWEEN 101 AND 106 OR role_id BETWEEN 101 AND 106;",
    "DELETE FROM sys_user WHERE user_id BETWEEN 101 AND 106;",
    "DELETE FROM sys_role WHERE role_id BETWEEN 101 AND 106;",
    "DELETE FROM sys_menu WHERE menu_id BETWEEN 2103 AND 2109;",
    "SET FOREIGN_KEY_CHECKS=1;",
    "",
    "INSERT INTO sys_role (role_id, role_name, role_key, role_sort, data_scope, menu_check_strictly, dept_check_strictly, status, del_flag, create_by, create_time, remark) VALUES",
]
role_vals = []
for rid, name, key, sort in roles:
    role_vals.append(
        f"({rid}, '{name}', '{key}', {sort}, '1', 1, 1, '0', '0', 'admin', NOW(), 'pm')"
    )
lines.append(",\n".join(role_vals) + ";")
lines.append("")
lines.append(
    "INSERT INTO sys_user (user_id, dept_id, user_name, nick_name, user_type, email, phonenumber, sex, avatar, password, status, del_flag, login_ip, create_by, create_time, remark) VALUES"
)
user_vals = []
for uid, uname, nick in users:
    user_vals.append(
        f"({uid}, 103, '{uname}', '{nick}', '00', '{uname}@project.local', '13800000{uid}', '0', '', '{PWD}', '0', '0', '', 'admin', NOW(), 'pm')"
    )
lines.append(",\n".join(user_vals) + ";")
lines.append("")
lines.append("INSERT INTO sys_user_role (user_id, role_id) VALUES")
lines.append("(101, 101), (102, 102), (103, 103), (104, 104), (105, 105), (106, 106);")
lines.append("")
lines.append(
    "INSERT INTO sys_menu (menu_id, menu_name, parent_id, order_num, path, component, query, route_name, is_frame, is_cache, menu_type, visible, status, perms, icon, create_by, create_time, remark) VALUES"
)
menu_vals = []
for mid, name, order, path, component, perms, icon in menus:
    menu_vals.append(
        f"({mid}, '{name}', 2100, {order}, '{path}', '{component}', '', '', 1, 0, 'C', '0', '0', '{perms}', '{icon}', 'admin', NOW(), 'pm')"
    )
lines.append(",\n".join(menu_vals) + ";")
lines.append("")
lines.append("INSERT INTO sys_role_menu (role_id, menu_id) VALUES")
lines.append("(101, 2100), (101, 2103), (101, 2104), (101, 2105),")
lines.append("(102, 2100), (102, 2103), (102, 2106),")
lines.append("(103, 2100), (103, 2103), (103, 2107),")
lines.append("(104, 2100), (104, 2103), (104, 2108),")
lines.append("(105, 2100), (105, 2103), (105, 2109),")
lines.append("(106, 2100), (106, 2103);")
lines.append("INSERT IGNORE INTO sys_role_menu (role_id, menu_id) VALUES")
lines.append("(1, 2103), (1, 2104), (1, 2105), (1, 2106), (1, 2107), (1, 2108), (1, 2109),")
lines.append("(100, 2103), (100, 2104), (100, 2105), (100, 2106), (100, 2107), (100, 2108), (100, 2109);")
lines.append("")

text = "\n".join(lines) + "\n"
path = Path(r"E:/ai-pro/project_agent/java/ruoyi-react/sql/patch_pm_workflow_menus.sql")
path.write_text(text, encoding="utf-8")
assert u("9879", "76ee", "53f0", "8d26") in text
assert "pm_biz" in text
print("rewrote SQL ok", path.stat().st_size)
