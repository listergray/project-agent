# -*- coding: utf-8 -*-
"""Offline smoke test for ProjectStateMachine transitions (no Spring)."""
import re
from pathlib import Path

sm = Path(
    r"E:\ai-pro\project_agent\java\ruoyi-react\ruoyi-system\src\main\java\com\ruoyi\system\project\workflow\ProjectStateMachine.java"
).read_text(encoding="utf-8")
# parse put(...) lines
puts = re.findall(
    r"put\(PmStatus\.(\w+),\s*ACT_(\w+),\s*PmStatus\.(\w+)\)",
    sm,
)
assert len(puts) >= 11, puts
print("transitions:", len(puts))
for a, b, c in puts:
    print(f"  {a} --{b}--> {c}")

# pages exist
pages = [
    r"E:\ai-pro\project_agent\java\ruoyi-react\react-ui\src\pages\Project\Ledger\index.tsx",
    r"E:\ai-pro\project_agent\java\ruoyi-react\react-ui\src\pages\Project\Basic\index.tsx",
    r"E:\ai-pro\project_agent\java\ruoyi-react\react-ui\src\pages\Project\Extend\index.tsx",
    r"E:\ai-pro\project_agent\java\ruoyi-react\react-ui\src\pages\Project\Audit\Basic.tsx",
    r"E:\ai-pro\project_agent\java\ruoyi-react\react-ui\src\pages\Project\Audit\Extend.tsx",
    r"E:\ai-pro\project_agent\java\ruoyi-react\react-ui\src\pages\Project\Audit\Purchase.tsx",
    r"E:\ai-pro\project_agent\java\ruoyi-react\react-ui\src\pages\Project\Audit\Finance.tsx",
    r"E:\ai-pro\project_agent\java\ruoyi-react\react-ui\src\services\project\workflow.ts",
]
for p in pages:
    assert Path(p).exists(), p
print("frontend pages OK")

# SQL users
import pymysql

conn = pymysql.connect(
    host="twlmac",
    user="root",
    password="root123456",
    database="ry",
    charset="utf8mb4",
)
with conn.cursor() as cur:
    cur.execute(
        "SELECT user_name, nick_name FROM sys_user WHERE user_id BETWEEN 101 AND 106 ORDER BY user_id"
    )
    users = cur.fetchall()
    cur.execute(
        "SELECT role_key FROM sys_role WHERE role_id BETWEEN 101 AND 106 ORDER BY role_id"
    )
    roles = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT COUNT(*) FROM sys_role_menu WHERE menu_id BETWEEN 2103 AND 2109")
    rm = cur.fetchone()[0]
print("users:", users)
print("roles:", roles)
print("role_menu rows for 2103-2109:", rm)
assert set(roles) == {
    "pm_applicant",
    "pm_basic_auditor",
    "pm_extend_auditor",
    "pm_purchase",
    "pm_finance",
    "pm_leader",
}
assert rm >= 20
print("SEED VERIFY PASS")
conn.close()
