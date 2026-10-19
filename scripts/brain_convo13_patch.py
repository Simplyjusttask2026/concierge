#!/usr/bin/env python3
"""Convo 13 BRAIN apply: merge the 8 unmerged BRAIN_UPDATES + convo 13 into BRAIN.md.

Preserves every existing BRAIN word. Idempotent markers skip anything already merged.
Aborts (exit 1, no write) if safety checks fail."""
from pathlib import Path
import sys

brain_path = Path("BRAIN.md")
updates_dir = Path("BRAIN_UPDATES")

text = brain_path.read_text(encoding="utf-8")
print(f"BRAIN.md before: chars={len(text)} lines={text.count(chr(10))+1}")
if "CONVO 13" in text:
    print("CONVO 13 already in BRAIN.md - skipping (idempotent).")
    sys.exit(0)
for marker_text in ["CREWAI STUDIO -> ZOHO BRIDGE LIVE", "CONVO 8", "CONVO 10 ADDENDUM", "FREE ONLY"]:
    if marker_text not in text:
        print(f"ERROR: history marker missing: {marker_text}. Refusing to write.")
        sys.exit(1)

old_updated = "2026-10-19 convo 8 (WhatsApp + Nextdoor corrected by owner via Kernel; full live audit; see convo 8 section below)"
new_updated = "2026-10-19 convo 13 (full BRAIN + every note read, 8 unmerged notes + pasted convo merged, read again verified; see convo 13 section below)"
if old_updated not in text:
    print("ERROR: convo 8 LAST UPDATED line not found. Refusing to write.")
    sys.exit(1)
text = text.replace(old_updated, new_updated, 1)

unmerged = [
    "2026-10-19-convo10-twitter-readded.md",
    "2026-10-19-convo11-ads-phones.md",
    "2026-10-19-convo11-ads-team-free.md",
    "2026-10-19-convo12-ads-contact-email.md",
    "2026-10-19-convo12-ads-contacts-final.md",
    "2026-10-19-convo12-whatsapp-correction.md",
    "2026-10-19-convo12-whatsapp-fixed.md",
    "2026-10-19-convo12-zoho-voice.md",
]
appended = []
for name in unmerged:
    f = updates_dir / name
    if not f.exists():
        print(f"ERROR: update file missing: {name}. Refusing to write.")
        sys.exit(1)
    body = f.read_text(encoding="utf-8").strip()
    idx = body.find("## ")
    if idx < 0:
        print(f"ERROR: no heading in {name}. Refusing to write.")
        sys.exit(1)
    section = body[idx:].strip()
    heading = section.splitlines()[0].strip()
    if heading in text:
        print(f"Skip already-merged: {name}")
        continue
    text = text.rstrip("\n") + f"\n\n## === MERGED FROM BRAIN_UPDATES/{name} ===\n{section}\n"
    appended.append(name)
print(f"Appended notes ({len(appended)}): {appended}")

trail = updates_dir / "2026-10-19-convo13-brain-read-add-reread.md"
if not trail.exists():
    print("ERROR: convo13 trail file missing. Refusing to write.")
    sys.exit(1)
body13 = trail.read_text(encoding="utf-8").strip()
idx13 = body13.find("## === CONVO 13")
if idx13 < 0:
    print("ERROR: convo 13 marker not in trail. Refusing to write.")
    sys.exit(1)
section13 = body13[idx13:].strip()
text = text.rstrip("\n") + "\n\n" + section13 + "\n"

if "CONVO 13" not in text or new_updated not in text:
    print("ERROR: merged check failed. Refusing to write.")
    sys.exit(1)
for name in appended:
    if f"BRAIN_UPDATES/{name}" not in text:
        print(f"ERROR: merged marker missing after append: {name}. Refusing to write.")
        sys.exit(1)

brain_path.write_text(text, encoding="utf-8")
print(f"BRAIN.md after: chars={len(text)} lines={text.count(chr(10))+1}")
print("BRAIN PATCH OK")
