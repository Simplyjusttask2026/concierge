#!/usr/bin/env python3
"""Owner 2026-10-19: Twitter/X locked out, no X API yet. Remove twitter from concierge social platforms until owner has X API. Exact-match only, idempotent, syntax check."""
from pathlib import Path
import ast, sys

p = Path("concierge.py")
text = p.read_text(encoding="utf-8")

old = 'SOCIAL_PLATFORMS = ["facebook", "instagram", "twitter"]'
new = 'SOCIAL_PLATFORMS = ["facebook", "instagram"]  # twitter removed 2026-10-19: owner locked out, no X API yet'

if old in text:
    text = text.replace(old, new, 1)
    print("SOCIAL_PLATFORMS patched.")
elif new in text:
    print("SOCIAL_PLATFORMS already patched - idempotent skip.")
else:
    print("ERROR: SOCIAL_PLATFORMS line not found exactly. Refusing to write.")
    sys.exit(1)

old_prompt = '(Facebook, Instagram, Twitter/X)'
new_prompt = '(Facebook, Instagram)'
if old_prompt in text:
    text = text.replace(old_prompt, new_prompt, 1)
    print("Prompt platform list patched.")
else:
    print("Prompt platform list not found (ok if prompt changed).")

if "twitter" in text.lower().replace('twitter removed 2026-10-19: owner locked out, no x api yet', ''):
    print("WARNING: other twitter mentions remain - leaving them, printing for review")
else:
    print("No other twitter refs.")

ast.parse(text)
print("syntax OK")
p.write_text(text, encoding="utf-8")
print(f"concierge.py chars after: {len(text)}")
print("PATCH OK")
