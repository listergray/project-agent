# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(
    r"E:\ai-pro\project_agent\java\ruoyi-react\react-ui\src\components\RightContent\AvatarDropdown.tsx"
)
t = p.read_text(encoding="utf-8")
label = "\u5b50\u7cfb\u7edf\u4e2d\u5fc3"
# replace whatever label is currently after portal key
needle_start = "key: 'portal',"
idx = t.find(needle_start)
if idx < 0:
    raise SystemExit("portal key not found")
# find label: '...' after this
li = t.find("label:", idx)
if li < 0 or li > idx + 200:
    raise SystemExit("label not found near portal")
q1 = t.find("'", li)
q2 = t.find("'", q1 + 1)
t2 = t[: q1 + 1] + label + t[q2:]
p.write_text(t2, encoding="utf-8", newline="\n")
print("avatar label set to", label.encode("unicode_escape").decode())
print("ok", label in p.read_text(encoding="utf-8"))
