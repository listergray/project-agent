# -*- coding: utf-8 -*-
from pathlib import Path
import pymysql

ROOT = Path(r'E:/ai-pro/project_agent/java/ruoyi-react/react-ui/src')

# MySQL
conn = pymysql.connect(host='twlmac', user='root', password='root123456', database='ry', charset='utf8mb4')
with conn.cursor() as cur:
    updates = [
        (2103, '\u9879\u76ee\u53f0\u8d26', '\u7acb\u9879\u8054\u5ba1\u53f0\u8d26'),
        (2104, '\u57fa\u7840\u4fe1\u606f\u5f55\u5165', '\u57fa\u7840\u4fe1\u606f\u5f55\u5165'),
        (2105, '\u6269\u5c55\u4fe1\u606f\u5f55\u5165', '\u6269\u5c55\u4fe1\u606f\u5f55\u5165'),
        (2106, '\u4e00\u6b21\u5ba1\u6838', '\u57fa\u7840\u4fe1\u606f\u4e00\u6b21\u5ba1\u6838'),
        (2107, '\u4e8c\u6b21\u5ba1\u6838', '\u6269\u5c55\u4fe1\u606f\u4e8c\u6b21\u5ba1\u6838'),
        (2108, '\u8d2d\u4e70\u8054\u5ba1', '\u8d2d\u4e70\u8054\u5ba1'),
        (2109, '\u8d22\u52a1\u8054\u5ba1', '\u8d22\u52a1\u8054\u5ba1'),
    ]
    for mid, name, remark in updates:
        cur.execute('UPDATE sys_menu SET menu_name=%s, remark=%s WHERE menu_id=%s', (name, remark, mid))
    role_names = [
        (101, '\u9879\u76ee\u7ecf\u529e'),
        (102, '\u4e00\u6b21\u5ba1\u6838\u5c97'),
        (103, '\u4e8c\u6b21\u5ba1\u6838\u5c97'),
        (104, '\u8d2d\u4e70\u8054\u5ba1\u5c97'),
        (105, '\u8d22\u52a1\u8054\u5ba1\u5c97'),
        (106, '\u5206\u7ba1\u9886\u5bfc'),
    ]
    for rid, name in role_names:
        cur.execute('UPDATE sys_role SET role_name=%s WHERE role_id=%s', (name, rid))
    nicks = [
        (101, '\u4e1a\u52a1\u7ecf\u529e'),
        (102, '\u9879\u76ee\u529e\u5ba1\u6838'),
        (103, '\u5f52\u53e3\u5ba1\u6838'),
        (104, '\u91c7\u8d2d\u8054\u5ba1'),
        (105, '\u8d22\u52a1\u8054\u5ba1'),
        (106, '\u5206\u7ba1\u9886\u5bfc'),
    ]
    for uid, nick in nicks:
        cur.execute('UPDATE sys_user SET nick_name=%s WHERE user_id=%s', (nick, uid))
    conn.commit()
    cur.execute('SELECT menu_id, menu_name FROM sys_menu WHERE menu_id BETWEEN 2103 AND 2109')
    print([ (a,b) for a,b in cur.fetchall()])
conn.close()
print('mysql ok')
