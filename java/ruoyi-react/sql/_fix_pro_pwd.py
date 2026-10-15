"""Reset pro password to 123456 and verify login-ready state."""
from __future__ import annotations

import bcrypt
import json
import subprocess
import urllib.request

HASH = bcrypt.hashpw(b"123456", bcrypt.gensalt(rounds=10)).decode().replace("$2b$", "$2a$")

sql = f"""
USE ry;
UPDATE sys_user SET password='{HASH}', status='0', del_flag='0', update_time=NOW()
WHERE user_name='pro';
SELECT user_id, user_name, status, del_flag, CHAR_LENGTH(password) plen, LEFT(password, 29) AS pwd
FROM sys_user WHERE user_name='pro';
SELECT COUNT(*) AS role_links FROM sys_user_role WHERE user_id=(SELECT user_id FROM sys_user WHERE user_name='pro');
"""

proc = subprocess.run(
    ["docker", "exec", "-i", "mysql-resume", "mysql", "-uroot", "-proot123456", "--default-character-set=utf8mb4"],
    input=sql.encode("utf-8"),
    capture_output=True,
)
print(proc.stdout.decode("utf-8", errors="replace"))
print(proc.stderr.decode("utf-8", errors="replace"))
print("hash_ok", bcrypt.checkpw(b"123456", HASH.encode()), HASH[:28])
print("exit", proc.returncode)
