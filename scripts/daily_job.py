"""
Simply Just Task - FREE daily 9AM job
Runs from GitHub Actions (free), not from chat.

Does:
 1. Only runs at 09:00 America/New_York on schedule (DST handled)
 2. Wakes the free Render concierge (sjt-concierge)
 3. Starts CrewAI Simply Just Task Lead Automation-v1 with target_profile
    (requires GitHub Secret CREWAI_BEARER_TOKEN - never put it in code)
 4. Triggers Render /run-daily (lead qualify + outreach, max 10/day) and
    /run-social (1 post/day per connected platform + replies + lead capture)
    ONLY after the CrewAI kickoff succeeds, so a missing/bad token fails
    the run visibly instead of silently posting/emailing nothing.

Does NOT in v2:
 - Spend any money (free GitHub Actions + free Render + free Zoho tier only)
 - Run Nextdoor (no API - Kernel browser, supervised, see SOPS/NEXTDOOR_KERNEL.md)
 - Buy Findymail credits, Retell numbers, or any paid service

Owner visibility: GitHub repo > Actions tab shows every run + log.
GitHub also emails the repo owner on workflow failure by default.
"""
import os, sys, json, datetime
from zoneinfo import ZoneInfo
import requests

NY = ZoneInfo("America/New_York")
now_ny = datetime.datetime.now(NY)
force = os.environ.get("FORCE_RUN", "0") == "1"
print(f"Now in America/New_York: {now_ny.isoformat()} force={force}")

if not force and now_ny.hour != 9:
    print("Not 9AM New York - skipping (DST guard).")
    sys.exit(0)

# 1) Wake free Render concierge
concierge_url = os.environ.get("CONCIERGE_URL", "https://sjt-concierge.onrender.com/").rstrip("/") + "/"
try:
    r = requests.get(concierge_url + "ping", timeout=60)
    print(f"Concierge wake (/ping): {r.status_code} {r.text[:200]}")
except Exception as e:
    print(f"Concierge wake failed (continuing): {e}")

# 2) Start CrewAI lead crew
token = os.environ.get("CREWAI_BEARER_TOKEN", "").strip()
kickoff_url = os.environ.get("CREWAI_KICKOFF_URL", "").strip()
target = os.environ.get("TARGET_PROFILE", "Local residential homeowners in Central Florida for Simply Just Task")

if not token:
    print("ERROR: CREWAI_BEARER_TOKEN secret is missing.")
    print("Add it in GitHub: repo Settings > Secrets and variables > Actions > New repository secret.")
    print("Use the CrewAI AMP/deployment bearer token (same one used to connect CrewAI). Do NOT commit it.")
    sys.exit(1)

try:
    r = requests.post(
        kickoff_url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"inputs": {"target_profile": target}},
        timeout=120,
    )
    print(f"CrewAI kickoff: {r.status_code}")
    print(r.text[:1000])
    if r.status_code >= 400:
        sys.exit(1)
    try:
        data = r.json()
        print("Kickoff ID:", data.get("kickoff_id") or data.get("id") or json.dumps(data)[:300])
    except Exception:
        pass
except Exception as e:
    print(f"CrewAI kickoff failed: {e}")
    sys.exit(1)

# 3) Trigger Render pipelines (lead machine + social crew)
for path in ("/run-daily", "/run-social"):
    try:
        r = requests.get(concierge_url.rstrip("/") + path, timeout=60)
        print(f"Render {path}: {r.status_code} {r.text[:300]}")
        if r.status_code >= 400:
            print(f"WARNING: {path} returned {r.status_code} - check Render logs")
    except Exception as e:
        print(f"Render {path} failed (continuing): {e}")

print("Daily 9AM job finished. Next: check Actions log, CrewAI execution, Zoho for new leads, and Zoho Mail for SJT reports.")
print("Note: Nextdoor is NOT automated here - no API. Kernel browser checks only, supervised, per SOPS/NEXTDOOR_KERNEL.md.")
