import pathlib, ast
p = pathlib.Path("scripts/daily_job.py")
t = p.read_text()
if "HUNT_ONLY" not in t:
    old = 'force = os.environ.get("FORCE_RUN", "0") == "1"\nprint(f"Now in America/New_York: {now_ny.isoformat()} force={force}")\n\nif not force and now_ny.hour != 9:\n    print("Not 9AM New York - skipping (DST guard).")\n    sys.exit(0)'
    new = """force = os.environ.get("FORCE_RUN", "0") == "1"
hunt_only = os.environ.get("HUNT_ONLY", "0") == "1"
force_hunt = os.environ.get("FORCE_HUNT", "0") == "1"
print(f"Now in America/New_York: {now_ny.isoformat()} force={force} hunt_only={hunt_only} force_hunt={force_hunt}")

if hunt_only:
    if not (force or force_hunt) and now_ny.hour not in (11, 15, 19):
        print("HUNT_ONLY: Not 11AM/3PM/7PM New York - skipping (DST guard).")
        sys.exit(0)
elif not force and now_ny.hour != 9:
    print("Not 9AM New York - skipping (DST guard).")
    sys.exit(0)"""
    assert t.count(old) == 1, "guard anchor missing"
    t = t.replace(old, new)
    old2 = "    so new CrewAI leads are in Zoho before the email machine runs."
    assert t.count(old2) == 1, "doc anchor missing"
    t = t.replace(old2, old2 + "\n    HUNT_ONLY=1 mode (crewai-hunt-3x.yml, 11AM/3PM/7PM ET): steps 1-5 only.\n    It NEVER triggers /run-daily or /run-social, so no outreach is sent.")
    old3 = '# 5) Trigger Render pipelines (new leads are now in Zoho first)\nfor path in ("/run-daily", "/run-social"):'
    new3 = """# 5) Trigger Render pipelines (new leads are now in Zoho first)
# HUNT_ONLY: stop after Zoho ingest - no outreach / no social.
if hunt_only:
    print("HUNT_ONLY: Zoho ingest complete - skipping /run-daily and /run-social (no outreach).")
    print("Hunt-only job finished.")
    sys.exit(0)

for path in ("/run-daily", "/run-social"):"""
    assert t.count(old3) == 1, "pipeline anchor missing"
    t = t.replace(old3, new3)
    ast.parse(t)
    p.write_text(t)
    print("daily_job.py HUNT_ONLY inserted, syntax OK")
else:
    print("daily_job.py already has HUNT_ONLY")

f = pathlib.Path("FRANKENSTEIN_STATUS.md")
ft = f.read_text()
marker = "ADDENDUM 2026-10-22"
if marker not in ft:
    ft = ft.rstrip() + "\n\n## ADDENDUM 2026-10-22 (verified live)\n- Studio test run finished, Zoho leads created 2026-10-22 = 0. Manual Studio runs do not use the GitHub bridge (`scripts/daily_job.py`).\n- Fix #3 updated: Render Zoho keys ARE present, but direct token test fails `invalid_code`. Owner must regenerate `ZOHO_REFRESH_TOKEN` in Render only. Composio fallback read verified via `/call-center` on 2026-10-22.\n- Hunt-only 3x/day added: `crewai-hunt-3x.yml` + `HUNT_ONLY` in `daily_job.py` (11AM/3PM/7PM ET, Zoho ingest only, NO outreach).\n- Supervised 9AM proof still pending (daylight 8AM-9PM ET only). WhatsApp Meta still owner-only. `MACHINE_TOKEN` missing on both GitHub and Render - set both together or neither.\n"
    f.write_text(ft)
    print("FRANKENSTEIN_STATUS.md addendum added")
else:
    print("FRANKENSTEIN_STATUS.md addendum already present")
print("HUNT3X APPLY OK")
