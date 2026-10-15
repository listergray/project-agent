# -*- coding: utf-8 -*-
import pymysql

c = pymysql.connect(
    host="192.168.1.57",
    port=3306,
    user="root",
    password="root123456",
    database="ry",
    charset="utf8mb4",
    connect_timeout=5,
    autocommit=True,
)
cur = c.cursor()
# ensure chat menu enabled
cur.execute(
    "UPDATE sys_menu SET visible='0', status='0' WHERE menu_id=%s",
    (2101,),
)
print("2101 rows", cur.rowcount)
cur.execute(
    "SELECT menu_id, path, visible, status FROM sys_menu WHERE menu_id BETWEEN 2100 AND 2109 ORDER BY menu_id"
)
for r in cur.fetchall():
    print(r)
c.close()
