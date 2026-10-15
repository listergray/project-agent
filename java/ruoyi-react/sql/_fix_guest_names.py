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
name = "\u6e38\u5ba2"
cur.execute(
    "UPDATE sys_user SET nick_name=%s WHERE user_name=%s",
    (name, "guest"),
)
cur.execute(
    "UPDATE sys_role SET role_name=%s WHERE role_key=%s",
    (name, "guest"),
)
cur.execute("SELECT HEX(nick_name), nick_name FROM sys_user WHERE user_name='guest'")
print(cur.fetchone())
c.close()
