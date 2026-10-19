#!/usr/bin/env python3
"""One-time Fix 2a: correct the Cal.com booking link in concierge.py.
Changes ONLY: /15min -> /simplybook. Aborts if already fixed or unexpected."""
from pathlib import Path
import sys

p = Path("concierge.py")
t = p.read_text(encoding="utf-8")
old = 'CAL_LINK = "https://cal.com/simply-justtask/15min"'
new = 'CAL_LINK = "https://cal.com/simply-justtask/simplybook"'
count = t.count(old)
print(f"Found wrong CAL_LINK lines: {count}")
if count != 1:
    print("ERROR: expected exactly 1 wrong CAL_LINK line. Aborting, no changes written.")
    sys.exit(1)
t2 = t.replace(old, new)
assert "simply-justtask/15min" not in t2, "wrong link still present after replace"
assert new in t2, "correct link missing after replace"
import ast
ast.parse(t2)
print("Python syntax check: OK")
p.write_text(t2, encoding="utf-8")
print(f"concierge.py fixed. chars {len(t)} -> {len(t2)}")
