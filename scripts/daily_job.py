"""
Simply Just Task - FREE daily 9AM job v3 (CrewAI Studio -> Zoho bridge)
Runs from GitHub Actions (free), not from chat.

Does:
 1. Only runs at 09:00 America/New_York on schedule (DST handled)
 2. Wakes the free Render concierge (sjt-concierge)
 3. Starts CrewAI Simply Just Task Lead Automation-v1 with target_profile
    (requires GitHub Secret CREWAI_BEARER_TOKEN - never put it in code)
 4. WAITS for that Studio run to finish, reads its result, extracts leads
 5. Submits those leads to Render POST /ingest-crewai-leads, which saves
    each lead to Zoho CRM (dedupe by email, then phone,
    Lead_Status=Not Contacted, Source noted in Description)
 6. ONLY THEN triggers Render /run-daily (lead qualify + outreach, max 10/day)
    and /run-social (1 post/day per connected platform + replies + lead capture)
    so new CrewAI leads are in Zoho before the email machine runs.
    HUNT_ONLY=1 mode (crewai-hunt-3x.yml, 11AM/3PM/7PM ET): steps 1-5 only.
    It NEVER triggers /run-daily or /run-social, so no outreach is sent.

Does NOT:
 - Spend any money (free GitHub Actions + free Render + free Zoho tier only)
 - Run Nextdoor (no API - Kernel browser, supervised, see SOPS/NEXTDOOR_KERNEL.md)
 - Buy Findymail credits, Retell numbers, or any paid service

Owner visibility: GitHub repo > Actions tab shows every run + log.
GitHub also emails the repo owner on workflow failure by default.
"""
import os, sys, json, time, datetime, re
from zoneinfo import ZoneInfo
import requests

NY = ZoneInfo("America/New_York")
now_ny = datetime.datetime.now(NY)
force = os.environ.get("FORCE_RUN", "0") == "1"
hunt_only = os.environ.get("HUNT_ONLY", "0") == "1"
force_hunt = os.environ.get("FORCE_HUNT", "0") == "1"
print(f"Now in America/New_York: {now_ny.isoformat()} force={force} hunt_only={hunt_only} force_hunt={force_hunt}")

if hunt_only:
    if not (force or force_hunt) and now_ny.hour not in (11, 15, 19):
        print("HUNT_ONLY: Not 11AM/3PM/7PM New York - skipping (DST guard).")
        sys.exit(0)
elif not force and now_ny.hour != 9:
    print("Not 9AM New York - skipping (DST guard).")
    sys.exit(0)

concierge_url = os.environ.get("CONCIERGE_URL", "https://sjt-concierge.onrender.com/").rstrip("/") + "/"
machine_token = os.environ.get("MACHINE_TOKEN", "").strip()
machine_headers = {"x-machine-token": machine_token} if machine_token else {}

# 1) Wake free Render concierge
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
    sys.exit(1)
if not kickoff_url:
    print("ERROR: CREWAI_KICKOFF_URL is missing.")
    sys.exit(1)

base_url = kickoff_url.rsplit("/kickoff", 1)[0]
auth = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

kickoff_id = None
result_payload = None
webhook_url = concierge_url + "crewai-task-webhook" + (("?t=" + machine_token) if machine_token else "")
try:
    kickoff_payload = {"inputs": {"target_profile": target}}
    if machine_token:
        kickoff_payload["task_webhook_url"] = webhook_url
    r = requests.post(kickoff_url, headers=auth, json=kickoff_payload, timeout=120)
    print(f"CrewAI kickoff: {r.status_code}")
    if r.status_code >= 400 and "task_webhook_url" in kickoff_payload:
        print("CrewAI kickoff with task webhook rejected - retrying without webhook.")
        kickoff_payload.pop("task_webhook_url", None)
        r = requests.post(kickoff_url, headers=auth, json=kickoff_payload, timeout=120)
        print(f"CrewAI kickoff retry: {r.status_code}")
    print(r.text[:1000])
    if r.status_code >= 400:
        sys.exit(1)
    try:
        data = r.json()
        kickoff_id = data.get("kickoff_id") or data.get("id")
        # Some deployments return the finished result inline.
        if isinstance(data, dict) and any(k in data for k in ("result", "output", "leads")):
            result_payload = data
    except Exception:
        pass
    print("Kickoff ID:", kickoff_id)
except SystemExit:
    raise
except Exception as e:
    print(f"CrewAI kickoff failed: {e}")
    sys.exit(1)

# 3) Wait for the Studio run to finish, then read its result
def find_result(obj):
    if isinstance(obj, dict):
        for k in ("result", "output", "raw_output", "final_output", "leads"):
            if obj.get(k):
                return obj[k]
        for v in obj.values():
            got = find_result(v)
            if got:
                return got
    return None

status = "unknown"
completed = result_payload is not None and not kickoff_id
deadline = time.time() + int(os.environ.get("CREWAI_WAIT_SECONDS", "1200"))  # 20 min max
if kickoff_id:
    status_url = base_url + "/status/" + str(kickoff_id)
    while time.time() < deadline:
        try:
            sr = requests.get(status_url, headers=auth, timeout=60)
            print(f"CrewAI status: {sr.status_code} {sr.text[:500]}")
            if sr.status_code < 400:
                sdata = sr.json()
                status = str(sdata.get("status") or sdata.get("state") or "").lower()
                if not result_payload:
                    result_payload = sdata
                if status in ("completed", "complete", "success", "successful", "finished", "done"):
                    result_payload = sdata
                    completed = True
                    break
                if status in ("failed", "failure", "error", "cancelled", "canceled"):
                    print("ERROR: CrewAI run failed - stopping so no empty pipelines run.")
                    sys.exit(1)
            else:
                print("Status endpoint not ready / not supported yet, waiting...")
        except SystemExit:
            raise
        except Exception as e:
            print(f"Status check failed (waiting): {e}")
        time.sleep(30)
    print(f"Final CrewAI status after wait: {status}")
    if not completed:
        print("ERROR: CrewAI run did not confirm completion in time - refusing to run pipelines on unknown results.")
        sys.exit(1)

if result_payload is None:
    print("ERROR: No CrewAI result could be read - refusing to run empty pipelines.")
    sys.exit(1)

result_value = find_result(result_payload)
ingest_body = result_payload if isinstance(result_payload, dict) and "leads" in result_payload else {"result": result_value if isinstance(result_value, str) else json.dumps(result_value or result_payload, default=str)}

# 4) Submit CrewAI leads to Zoho via Render bridge
try:
    ir = requests.post(concierge_url + "ingest-crewai-leads", headers={**machine_headers, "Content-Type": "application/json"}, json=ingest_body, timeout=300)
    print(f"Zoho ingest (/ingest-crewai-leads): {ir.status_code} {ir.text[:1500]}")
    if ir.status_code >= 400:
        print("ERROR: Zoho ingest failed - stopping before outreach pipelines.")
        sys.exit(1)
    try:
        idata = ir.json()
        print(f"Ingest summary: received={idata.get('received')} created={idata.get('created')} exists={idata.get('exists')} errors={idata.get('errors')}")
        if not idata.get("received"):
            print("WARNING: 0 leads extracted from CrewAI result - check the result shape in this log. Pipelines will still run for leads already in Zoho.")
    except Exception:
        pass
except SystemExit:
    raise
except Exception as e:
    print(f"Zoho ingest failed: {e}")
    sys.exit(1)

# 5) Trigger Render pipelines (new leads are now in Zoho first)
# HUNT_ONLY: stop after Zoho ingest - no outreach / no social.
if hunt_only:
    print("HUNT_ONLY: Zoho ingest complete - skipping /run-daily and /run-social (no outreach).")
    print("Hunt-only job finished.")
    sys.exit(0)

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
