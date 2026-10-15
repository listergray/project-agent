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
)
cur = c.cursor()
cur.execute(
    "SELECT menu_id, menu_name, path, component, visible FROM sys_menu WHERE menu_id IN (2090,2091,2200,2201)"
)
for r in cur.fetchall():
    print(r)
cur.execute(
    "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME=%s",
    ("xx_erp",),
)
print("xx_erp:", cur.fetchall())
# ensure xx_erp exists for xianyu-auto
cur.execute(
    "CREATE DATABASE IF NOT EXISTS xx_erp DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
)
print("xx_erp ensured")
c.close()
