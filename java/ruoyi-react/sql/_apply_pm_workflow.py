# -*- coding: utf-8 -*-
import pymysql
from pathlib import Path

sql_path = Path(r"E:\ai-pro\project_agent\java\ruoyi-react\sql\patch_pm_workflow_menus.sql")
sql = sql_path.read_text(encoding="utf-8")

conn = pymysql.connect(
    host="twlmac",
    user="root",
    password="root123456",
    database="ry",
    charset="utf8mb4",
    autocommit=True,
)
try:
    with conn.cursor() as cur:
        # split on semicolons carefully enough for our patch
        statements = []
        buf = []
        for line in sql.splitlines():
            s = line.strip()
            if not s or s.startswith("--"):
                continue
            buf.append(line)
            if s.endswith(";"):
                statements.append("\n".join(buf))
                buf = []
        if buf:
            statements.append("\n".join(buf))
        for stmt in statements:
            stmt = stmt.strip()
            if not stmt:
                continue
            try:
                cur.execute(stmt)
                if stmt.upper().startswith("SELECT"):
                    rows = cur.fetchall()
                    print("SELECT ->", rows[:10] if rows else rows)
            except Exception as e:
                print("ERR:", e)
                print("STMT:", stmt[:120])
                raise
    print("OK applied", len(statements), "statements")
finally:
    conn.close()
