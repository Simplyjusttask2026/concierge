#!/usr/bin/env python3
"""Owner 2026-10-19: Twitter/X @simplyjusttask connected + verified in Composio (twitter_grece-toom, ACTIVE, id 2019701374850637824). Re-add twitter to concierge social platforms. Exact-match only, idempotent, syntax check."""
from pathlib import Path
import ast, sys

p = Path("concierge.py")
text = p.read_text(encoding="utf-8")

old = 'SOCIAL_PLATFORMS = ["facebook", "instagram"]  # twitter removed 2026-10-19: owner locked out, no X API yet'
new = 'SOCIAL_PLATFORMS = ["facebook", "instagram", "twitter"]  # twitter re-added 2026-10-19: @simplyjusttask connected in Composio'

if old in text:
    text = text.replace(old, new, 1)
    print("SOCIAL_PLATFORMS patched.")
elif new in text:
    print("SOCIAL_PLATFORMS already patched - idempotent skip.")
else:
    print("ERROR: SOCIAL_PLATFORMS line not found exactly. Refusing to write.")
    sys.exit(1)

old_prompt = '(Facebook, Instagram)'
new_prompt = '(Facebook, Instagram, Twitter/X)'
if old_prompt in text:
    text = text.replace(old_prompt, new_prompt, 1)
    print("Prompt platform list patched.")
elif new_prompt in text:
    print("Prompt platform list already patched - idempotent skip.")
else:
    print("Prompt platform list not found (ok if prompt changed).")

ast.parse(text)
print("syntax OK")
p.write_text(text, encoding="utf-8")
print(f"concierge.py chars after: {len(text)}")
print("PATCH OK")
