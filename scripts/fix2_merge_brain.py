#!/usr/bin/env python3
"""One-time Fix 2b: merge BRAIN_UPDATES/*.md into BRAIN.md.
Owner already merged parts manually (convo 4/5/6 sections exist in BRAIN.md),
so this merges ONLY files not already present, verbatim, in filename order.
Idempotent: safe to re-run; already-merged files are skipped."""
from pathlib import Path
import sys

brain_path = Path("BRAIN.md")
updates_dir = Path("BRAIN_UPDATES")

text = brain_path.read_text(encoding="utf-8")
original_chars = len(text)
print(f"BRAIN.md before: chars={original_chars} lines={text.count(chr(10))+1}")

old_line = "2026-10-18 night convo 3 (Kernel Nextdoor verified-live, live feed scan, account decision pending, SOP plan documented \u2014 see convo 3 section)"
new_line = "2026-10-19 (BRAIN merged BRAIN_UPDATES verbatim, main protected + backup branch, fixes started \u2014 see merged 2026-10-19 sections)"
if old_line in text:
    text = text.replace(old_line, new_line, 1)
    print("LAST UPDATED bumped.")
else:
    print("LAST UPDATED already bumped or changed; leaving as-is.")

files = sorted(updates_dir.glob("*.md"))
if not files:
    print("ERROR: no BRAIN_UPDATES files found. Aborting.")
    sys.exit(1)

appended = []
skipped = []
for f in files:
    marker = f"BRAIN_UPDATES/{f.name}"
    if marker in text:
        skipped.append(f.name)
        continue
    body = f.read_text(encoding="utf-8").strip()
    text = text.rstrip("\n") + f"\n\n## === MERGED FROM {marker} ===\n{body}\n"
    appended.append(f.name)

print(f"Appended ({len(appended)}): {appended}")
print(f"Skipped already-merged ({len(skipped)}): {skipped}")

brain_path.write_text(text, encoding="utf-8")
print(f"BRAIN.md after: chars={len(text)} lines={text.count(chr(10))+1}")
if not appended:
    print("Nothing new to merge (all BRAIN_UPDATES already in BRAIN.md).")
