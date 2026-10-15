# -*- coding: utf-8 -*-
from pathlib import Path
import re
import pymysql

HOST = "192.168.1.57"
SQL_FILE = Path(__file__).with_name("patch_guest_user.sql")


def split_statements(sql: str) -> list[str]:
    lines = []
    for line in sql.splitlines():
        if line.strip().startswith("--"):
            continue
        lines.append(line)
    body = "\n".join(lines)
    return [p.strip() for p in body.split(";") if p.strip()]


def main() -> None:
    sql = SQL_FILE.read_text(encoding="utf-8")
    conn = pymysql.connect(
        host=HOST,
        port=3306,
        user="root",
        password="root123456",
        database="ry",
        charset="utf8mb4",
        connect_timeout=5,
        autocommit=True,
    )
    try:
        with conn.cursor() as cur:
            # sync password hash from pro if present
            cur.execute("SELECT password FROM sys_user WHERE user_name=%s", ("pro",))
            row = cur.fetchone()
            hash_pwd = row[0] if row and row[0] else None
            for s in split_statements(sql):
                cur.execute(s)
                print("OK", re.sub(r"\s+", " ", s)[:80])
            if hash_pwd:
                cur.execute(
                    "UPDATE sys_user SET password=%s WHERE user_name=%s",
                    (hash_pwd, "guest"),
                )
                print("synced guest password hash from pro")
            # ensure chat menu enabled
            cur.execute(
                "UPDATE sys_menu SET visible='0', status='0' WHERE menu_id IN (2101,2102)"
            )
            cur.execute(
                "SELECT user_id,user_name,nick_name FROM sys_user WHERE user_name='guest'"
            )
            print("user", cur.fetchone())
            cur.execute(
                "SELECT role_id,role_key FROM sys_role WHERE role_key='guest'"
            )
            print("role", cur.fetchone())
    finally:
        conn.close()


if __name__ == "__main__":
    main()
