#!/usr/bin/env python3
"""Append convo 8 twitter addendum to BRAIN.md if absent. Safety checks, idempotent."""
from pathlib import Path
import sys
brain=Path("BRAIN.md")
updates=Path("BRAIN_UPDATES/2026-10-19-convo8-twitter-removed.md")
text=brain.read_text(encoding="utf-8")
print(f"BRAIN.md before: chars={len(text)}")
if "TWITTER/X REMOVED" in text:
    print("Twitter addendum already in BRAIN.md - skipping.")
    sys.exit(0)
if "CONVO 8" not in text or "CREWAI STUDIO -> ZOHO BRIDGE LIVE" not in text:
    print("ERROR: history markers missing. Refusing.")
    sys.exit(1)
body=updates.read_text(encoding="utf-8").strip()
idx=body.find("## === CONVO 8 ADDENDUM")
if idx<0:
    print("ERROR: addendum marker missing. Refusing.")
    sys.exit(1)
section=body[idx:].strip()
merged=text.rstrip("\n")+"\n\n"+section+"\n"
brain.write_text(merged,encoding="utf-8")
print(f"BRAIN.md after: chars={len(merged)}")
print("PATCH OK")
