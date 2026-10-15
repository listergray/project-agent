# -*- coding: utf-8 -*-
import pymysql

HASH_123456 = "$2a$10$afBvgKQJT0uOmsVSm2pbguR0YnFb30u0Py8X0RqIoNqaWzIXfaT7e"

conn = pymysql.connect(
    host="twlmac",
    user="root",
    password="root123456",
    database="ry",
    charset="utf8mb4",
)
try:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT user_name, password FROM sys_user WHERE user_name IN (%s, %s) ORDER BY user_name",
            ("admin", "pro"),
        )
        print("before:", cur.fetchall())
        cur.execute(
            "UPDATE sys_user SET password=%s WHERE user_name=%s",
            (HASH_123456, "admin"),
        )
        conn.commit()
        cur.execute(
            "SELECT user_name, password FROM sys_user WHERE user_name IN (%s, %s) ORDER BY user_name",
            ("admin", "pro"),
        )
        rows = cur.fetchall()
        print("after:", rows)
        by_name = {r[0]: r[1] for r in rows}
        print("admin==pro:", by_name.get("admin") == by_name.get("pro"))
finally:
    conn.close()
