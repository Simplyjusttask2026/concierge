import pathlib
p = pathlib.Path('concierge.py')
s = p.read_text()
if 'whatsapp-drafts+recycle-report-v1' in s:
    print('Already patched')
    raise SystemExit(0)
anchor = '    lines += ["", "=== OUTREACH COPIES ==="]'
assert anchor in s, 'report anchor missing'
block_lines = [
    '    lines += ["", "=== WHATSAPP DRAFTS (DRAFT ONLY - NOT SENT) ==="]',
    '    lines.append("WhatsApp cold text blocked until approved template + VERIFIED. Owner-send drafts only.")',
    '    _wa = [e for e in report["leads"] if e.get("phone") and e.get("new_status") in ("Pre-Qualified", "Attempted to Contact")]',
    '    if not _wa:',
    '        lines.append("- none today")',
    '    for e in _wa:',
    '        _parts = str(e.get("name") or "").split()',
    '        _first = _parts[0] if _parts else "there"',
    '        lines.append("- DRAFT to %s (%s): Hello %s, this is Anthony from Simply Just Task. We received your request and can help. Reply YES to talk or STOP to opt out. Booking: %s" % (e.get("name"), e.get("phone"), _first, CAL_LINK))',
    '    lines += ["", "=== RECYCLE CANDIDATES (DRAFT ONLY - NO SEND) ==="]',
    '    _rc = [e for e in report["leads"] if e.get("new_status") in ("Recycled", "Contact in Future")]',
    '    if not _rc:',
    '        lines.append("- none in newest 50")',
    '    for e in _rc:',
    '        lines.append("- %s | status: %s | follow-up +30 days, never delete" % (e.get("name"), e.get("new_status")))',
]
add = chr(10).join(block_lines) + chr(10) + anchor
s = s.replace(anchor, add, 1)
dbg = chr(34) + 'zoho_path' + chr(34) + ': ' + chr(34) + 'composio-first,direct-crm-fallback-v1' + chr(34) + ','
assert dbg in s, 'debug anchor missing'
s = s.replace(dbg, dbg + chr(10) + '        "frankenstein_closeout": "whatsapp-drafts+recycle-report-v1",', 1)
p.write_text(s)
print('patched', len(s))
