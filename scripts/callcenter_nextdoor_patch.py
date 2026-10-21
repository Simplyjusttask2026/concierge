import pathlib
p = pathlib.Path('concierge.py')
s = p.read_text()
if 'call-center-v2' in s:
    print('concierge already patched v2')
else:
    assert 'and phone (888) 566-7570. Sign off as' in s, 'anchor missing and phone (888) 566-7570. Sign off as'
    s = s.replace('and phone (888) 566-7570. Sign off as', 'and phone (888) 566-7570. Always end with: Reply STOP to opt out. Sign off as', 1)
    assert 'def run_daily_pipeline():\n    report = {' in s, 'anchor missing def run_daily_pipeline():\n    report = {'
    s = s.replace('def run_daily_pipeline():\n    report = {', 'def run_daily_pipeline():\n    _outreach_open = _call_center_window_open()\n    report = {', 1)
    assert '"leads": [], "outreach": [], "errors": [], "cal_sync": {}}' in s, 'anchor missing "leads": [], "outreach": [], "errors": ['
    s = s.replace('"leads": [], "outreach": [], "errors": [], "cal_sync": {}}', '"leads": [], "outreach": [], "errors": [], "cal_sync": {}, "outreach_open": _outreach_open}', 1)
    assert '                elif new_status == "Pre-Qualified" and ld.get("Email"):' in s, 'anchor missing                 elif new_status == "Pre-'
    s = s.replace('                elif new_status == "Pre-Qualified" and ld.get("Email"):', '                elif new_status == "Pre-Qualified" and ld.get("Email") and _lead_is_stopped(ld):\n                    entry["outreach_suppressed"] = "STOP/opt-out in lead notes - do not contact"\n                elif new_status == "Pre-Qualified" and ld.get("Email") and not _outreach_open:\n                    entry["outreach_held"] = "outside 8am-9pm ET - hold for next 9AM run, no send at night"\n                elif new_status == "Pre-Qualified" and ld.get("Email") and _outreach_open:', 1)
    assert '    lines += ["", "=== CALL CENTER PLAN v1 (DRAFT ONLY - SENDS NOTHING) ===", "counts=%s window=%s wa_autosend=%s" % (_ccp["counts"],_ccp["window_open_8am_9pm_et"],_ccp["whatsapp_autosend_enabled"])]' in s, 'anchor missing     lines += ["", "=== CALL CENTER PLAN '
    s = s.replace('    lines += ["", "=== CALL CENTER PLAN v1 (DRAFT ONLY - SENDS NOTHING) ===", "counts=%s window=%s wa_autosend=%s" % (_ccp["counts"],_ccp["window_open_8am_9pm_et"],_ccp["whatsapp_autosend_enabled"])]', '    lines += ["", "=== CALL CENTER PLAN v1 (DRAFT ONLY - SENDS NOTHING) ===", "counts=%s window=%s wa_autosend=%s" % (_ccp["counts"],_ccp["window_open_8am_9pm_et"],_ccp["whatsapp_autosend_enabled"])]\n    for _c in _ccp.get("human_call_list") or []:\n        lines.append("- HUMAN CALL %s (%s) | %s" % (_c.get("name"), _c.get("phone"), _c.get("script")))', 1)
    assert '"call_center": "call-center-plan-v1",' in s, 'anchor missing "call_center": "call-center-plan-v1",'
    s = s.replace('"call_center": "call-center-plan-v1",', '"call_center": "call-center-v2,email-gate-8-21ET,stop-line,human-call-list,whatsapp-draft",\n        "nextdoor": "kernel-personal-auth,watcher-v2,draft-only",', 1)
    p.write_text(s)
    print('concierge patched v2', len(s))
n = pathlib.Path('scripts/nextdoor_watcher.py')
t = n.read_text()
assert 'nextdoor-watcher-v2' in t, 'nextdoor watcher v2 expected'
if 'anyone know' not in t:
    t = t.replace('"who do you use"', '"who do you use", "anyone know", "anyone recommend", "looking to find"')
    n.write_text(t)
    print('nextdoor intent patched')
else:
    print('nextdoor already intent patched')
