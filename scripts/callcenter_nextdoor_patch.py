import pathlib
p = pathlib.Path('concierge.py')
s = p.read_text()
if 'call-center-v1' in s:
    print('concierge already patched')
else:
    assert 'and phone (888) 566-7570. Sign off as' in s, 'anchor missing and phone (888) 566-7570. Sign'
    s = s.replace('and phone (888) 566-7570. Sign off as', 'and phone (888) 566-7570. Always end with: Reply STOP to opt out. Sign off as', 1)
    assert 'def run_daily_pipeline():\n    report = {' in s, 'anchor missing def run_daily_pipeline():\n    '
    s = s.replace('def run_daily_pipeline():\n    report = {', 'def run_daily_pipeline():\n    # Call Center safety gate (Frankenstein Part 5): no outreach sends outside 8am-9pm ET.\n    try:\n        _et_now = datetime.datetime.now(ZoneInfo("America/New_York")) if ZoneInfo else datetime.datetime.now(datetime.timezone.utc)\n    except Exception:\n        _et_now = datetime.datetime.now(datetime.timezone.utc)\n    _outreach_open = 8 <= _et_now.hour < 21\n    report = {', 1)
    assert '"leads": [], "outreach": [], "errors": [], "cal_sync": {}}' in s, 'anchor missing "leads": [], "outreach": [], "'
    s = s.replace('"leads": [], "outreach": [], "errors": [], "cal_sync": {}}', '"leads": [], "outreach": [], "errors": [], "cal_sync": {}, "outreach_open": _outreach_open, "et_hour": _et_now.hour}', 1)
    assert '                elif new_status == "Pre-Qualified" and ld.get("Email"):' in s, 'anchor missing                 elif new_statu'
    s = s.replace('                elif new_status == "Pre-Qualified" and ld.get("Email"):', '                elif new_status == "Pre-Qualified" and ld.get("Email") and not _outreach_open:\n                    entry["outreach_held"] = "outside 8am-9pm ET - hold for next 9AM run, no send at night"\n                elif new_status == "Pre-Qualified" and ld.get("Email") and _outreach_open:', 1)
    assert '    lines += ["", "=== OUTREACH COPIES ==="]' in s, 'anchor missing     lines += ["", "=== OUTREAC'
    s = s.replace('    lines += ["", "=== OUTREACH COPIES ==="]', '    lines += ["", "=== HUMAN CALL LIST (NO AUTO-CALL - HUMAN ONLY) ==="]\n    lines.append("Call window 8am-9pm ET only. No auto-call exists. Script: Hi [First], Anthony with Simply Just Task in Apopka, calling about your request. Is now ok for 2 minutes? I can text/email the booking link: " + CAL_LINK)\n    _cl = [e for e in report["leads"] if e.get("phone") and e.get("new_status") in ("Pre-Qualified", "Attempted to Contact")]\n    if not _cl:\n        lines.append("- none today")\n    for e in _cl:\n        lines.append("- CALL %s (%s) | status: %s | score: %s | city: %s" % (e.get("name"), e.get("phone"), e.get("new_status"), e.get("ai_score", "-"), e.get("city")))\n    lines.append("Call center window: ET hour %s, outreach_open=%s (email sends held outside 8am-9pm ET)" % (report.get("et_hour"), report.get("outreach_open")))\n    lines += ["", "=== OUTREACH COPIES ==="]', 1)
    assert '"frankenstein_closeout": "whatsapp-drafts+recycle-report-v1",' in s, 'anchor missing "frankenstein_closeout": "what'
    s = s.replace('"frankenstein_closeout": "whatsapp-drafts+recycle-report-v1",', '"frankenstein_closeout": "whatsapp-drafts+recycle-report-v1",\n        "call_center": "call-center-v1,email-live,whatsapp-draft,human-call-list,outreach-window-8-21ET",\n        "nextdoor": "kernel-personal-auth,watcher-cli-v1,draft-only",', 1)
    p.write_text(s)
    print('concierge patched', len(s))
n = pathlib.Path('scripts/nextdoor_watcher.py')
t = n.read_text()
if 'anyone know' not in t:
    t = t.replace('"who do you use"', '"who do you use", "anyone know", "anyone recommend", "looking to find"')
if 'watcher-cli-v1' in t:
    print('nextdoor already patched')
else:
    t += '\n\n# --- watcher-cli-v1 (2026-10-21): runnable report builder, DRAFT ONLY, never posts ---\nimport json as _json, sys as _sys, hashlib as _hashlib, pathlib as _pathlib\ndef build_report(posts):\n    seen, out = set(), []\n    for post in posts or []:\n        text = str(post.get("text") or "")\n        key = _hashlib.sha256(text.strip().lower().encode()).hexdigest()[:16]\n        if key in seen:\n            continue\n        seen.add(key)\n        score = score_post(text, int(post.get("age_min") or 60))\n        job = str(post.get("job") or "home help")\n        first = str(post.get("author_first") or "neighbor")\n        item = {"dedupe": key, "score": score, "real_lead": is_real_lead(score), "job": job,\n                "draft_comment": draft_comment(first, job) if score >= 70 else "",\n                "draft_dm": draft_dm(first, job) if score >= 80 else ""}\n        out.append(item)\n    return sorted(out, key=lambda x: -x["score"])\ndef main(argv=None):\n    argv = list(_sys.argv[1:] if argv is None else argv)\n    raw = _sys.stdin.read() if not argv else _pathlib.Path(argv[0]).read_text()\n    posts = _json.loads(raw) if raw.strip() else []\n    if isinstance(posts, dict):\n        posts = posts.get("posts") or []\n    print(_json.dumps({"watcher": "watcher-cli-v1", "mode": "DRAFT ONLY - no post/comment/DM sent", "count": len(posts), "results": build_report(posts)}, indent=2))\n    return 0\nif __name__ == "__main__":\n    raise SystemExit(main())\n'
    n.write_text(t)
    print('nextdoor patched', len(t))
