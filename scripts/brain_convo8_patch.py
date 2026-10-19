#!/usr/bin/env python3
"""One-time BRAIN convo 8 apply: preserve original BRAIN exactly, append convo 8 section, bump LAST UPDATED. Idempotent + safety checks."""
from pathlib import Path
import sys

brain = Path("BRAIN.md")
updates = Path("BRAIN_UPDATES") / "2026-10-19-convo8-whatsapp-nextdoor-audit.md"

text = brain.read_text(encoding="utf-8")
print(f"BRAIN.md before: chars={len(text)} lines={text.count(chr(10))+1}")

if "CONVO 8" in text:
    print("CONVO 8 already in BRAIN.md - skipping merge (idempotent).")
    sys.exit(0)

if "CREWAI STUDIO -> ZOHO BRIDGE LIVE" not in text:
    print("ERROR: history marker missing. Refusing to write.")
    sys.exit(1)

old = "2026-10-19 convo 7 (CrewAI Studio -> Zoho bridge committed to Render concierge + Daily 9AM v3; Cal.com locked; first real 9AM result-shape test still pending)"
new = "2026-10-19 convo 8 (WhatsApp + Nextdoor corrected by owner via Kernel; full live audit; see convo 8 section below)"
if old not in text:
    print("ERROR: convo 7 LAST UPDATED not found. Refusing to write.")
    sys.exit(1)
text = text.replace(old, new, 1)

if not updates.exists():
    print("ERROR: convo 8 update file missing. Refusing to write.")
    sys.exit(1)
body = updates.read_text(encoding="utf-8").strip()
marker = "## === CONVO 8"
idx = body.find(marker)
if idx < 0:
    print("ERROR: convo 8 marker not in update file. Refusing.")
    sys.exit(1)
section = body[idx:].strip()
if "BRAIN UPDATE" in section[:20]:
    print("ERROR: section starts wrong.")
    sys.exit(1)

merged = text.rstrip("\n") + "\n\n" + section + "\n"
if "CONVO 8" not in merged or new not in merged:
    print("ERROR: merged check failed. Refusing.")
    sys.exit(1)

brain.write_text(merged, encoding="utf-8")
print(f"BRAIN.md after: chars={len(merged)} lines={merged.count(chr(10))+1}")
print("BRAIN PATCH OK")
