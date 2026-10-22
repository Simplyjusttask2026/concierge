import pathlib, ast
p = pathlib.Path("concierge.py")
t = p.read_text()
anchor = '@app.route("/run-social", methods=["GET", "POST"])'
if "/crewai-task-webhook" not in t:
    assert t.count(anchor) == 1, "anchor missing"
    lines = [
        '@app.route("/crewai-task-webhook", methods=["POST"])',
        'def crewai_task_webhook():',
        '    token = request.args.get("t", "") or request.headers.get("x-machine-token", "")',
        '    if MACHINE_TOKEN and token != MACHINE_TOKEN:',
        '        return jsonify({"error": "unauthorized"}), 401',
        '    payload = request.get_json(silent=True) or {}',
        '    if not payload and request.data:',
        '        try:',
        '            payload = json.loads(request.data.decode("utf-8", "ignore"))',
        '        except Exception:',
        '            payload = {"result": request.data.decode("utf-8", "ignore")}',
        '    task_name = ""',
        '    if isinstance(payload, dict):',
        '        task_name = str(payload.get("task_name") or payload.get("taskName") or payload.get("name") or "")[:80]',
        '    leads = _crewai_extract_leads(payload)',
        '    results = []',
        '    seen = set()',
        '    for lead in leads[:100]:',
        '        key = (lead["email"] or lead["phone"] or lead["full_name"]).lower()',
        '        if key in seen:',
        '            continue',
        '        seen.add(key)',
        '        results.append({"name": lead["full_name"], "email": lead["email"], "result": _crewai_save_one(lead)})',
        '    created = sum(1 for r in results if r["result"].startswith("created:"))',
        '    exists = sum(1 for r in results if r["result"].startswith("exists:"))',
        '    errors = sum(1 for r in results if r["result"].startswith("error:"))',
        '    print(f"CREWAI TASK WEBHOOK task={task_name} received={len(leads)} created={created} exists={exists} errors={errors}")',
        '    return jsonify({"status": "ok", "task": task_name, "received": len(leads), "created": created, "exists": exists, "errors": errors, "results": results}), 200',
        '',
        '',
    ]
    block = chr(10).join(lines)
    t = t.replace(anchor, block + anchor, 1)
    ast.parse(t)
    p.write_text(t)
    print("concierge.py task webhook inserted, syntax OK")
else:
    print("concierge.py task webhook already present")
print("TASK WEBHOOK APPLY OK")
