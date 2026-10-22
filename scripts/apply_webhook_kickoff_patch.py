import pathlib, ast
p = pathlib.Path("scripts/daily_job.py")
t = p.read_text()
if "crewai-task-webhook" not in t:
    old = "try:" + chr(10) + '    r = requests.post(kickoff_url, headers=auth, json={"inputs": {"target_profile": target}}, timeout=120)' + chr(10) + '    print(f"CrewAI kickoff: {r.status_code}")' + chr(10) + "    print(r.text[:1000])"
    lines = [
        'webhook_url = concierge_url + "crewai-task-webhook" + (("?t=" + machine_token) if machine_token else "")',
        'try:',
        '    kickoff_payload = {"inputs": {"target_profile": target}}',
        '    if machine_token:',
        '        kickoff_payload["task_webhook_url"] = webhook_url',
        '    r = requests.post(kickoff_url, headers=auth, json=kickoff_payload, timeout=120)',
        '    print(f"CrewAI kickoff: {r.status_code}")',
        '    if r.status_code >= 400 and "task_webhook_url" in kickoff_payload:',
        '        print("CrewAI kickoff with task webhook rejected - retrying without webhook.")',
        '        kickoff_payload.pop("task_webhook_url", None)',
        '        r = requests.post(kickoff_url, headers=auth, json=kickoff_payload, timeout=120)',
        '        print(f"CrewAI kickoff retry: {r.status_code}")',
        '    print(r.text[:1000])',
    ]
    assert t.count(old) == 1, "kickoff anchor missing"
    t = t.replace(old, chr(10).join(lines), 1)
    ast.parse(t)
    p.write_text(t)
    print("daily_job.py task webhook kickoff inserted, syntax OK")
else:
    print("daily_job.py task webhook already present")
print("WEBHOOK KICKOFF APPLY OK")
