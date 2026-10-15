#!/usr/bin/env python3
"""Apply patch_portal_subsystems.sql to twlmac MySQL (db ry)."""
from __future__ import annotations

import pathlib
import re
import sys

try:
    import pymysql
except ImportError:
    print("need pymysql: pip install pymysql", file=sys.stderr)
    sys.exit(1)

HOST = "192.168.1.57"  # twlmac
PORT = 3306
USER = "root"
PASSWORD = "root123456"
DB = "ry"

SQL_FILE = pathlib.Path(__file__).with_name("patch_portal_subsystems.sql")


def split_statements(sql: str) -> list[str]:
    # drop full-line comments
    lines = []
    for line in sql.splitlines():
        if line.strip().startswith("--"):
            continue
        lines.append(line)
    body = "\n".join(lines)
    parts = [p.strip() for p in body.split(";")]
    return [p for p in parts if p]


def main() -> int:
    sql = SQL_FILE.read_text(encoding="utf-8")
    stmts = split_statements(sql)
    conn = pymysql.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        database=DB,
        charset="utf8mb4",
        autocommit=True,
        connect_timeout=5,
        read_timeout=30,
        write_timeout=30,
    )
    try:
        with conn.cursor() as cur:
            for s in stmts:
                cur.execute(s)
                preview = re.sub(r"\s+", " ", s)[:90]
                print(f"OK: {preview}")
        print("done: portal + xianyu menus applied")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
