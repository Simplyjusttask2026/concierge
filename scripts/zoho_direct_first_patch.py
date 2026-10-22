import pathlib, sys
p = pathlib.Path("concierge.py")
src = p.read_text()
MARKER = "zoho-direct-first-v1"
if MARKER in src:
    print("Already patched (zoho-direct-first-v1 present) - no change.")
    sys.exit(0)

# 1) zoho_exec: direct Render->Zoho FIRST for CRM (no Composio needed), Composio bridge as backup
old1 = """def zoho_exec(slug, args):
    try:
        resp = composio.tools.execute(slug=slug, arguments=args, user_id=COMPOSIO_USER_ID, dangerously_skip_version_check=True)
    except TypeError:
        try:
            resp = composio.tools.execute(slug, args, COMPOSIO_USER_ID)
        except Exception as e:
            resp = {"error": str(e)}
    except Exception as e:
        resp = {"error": str(e)}
    if _composio_failed(resp) and slug.startswith("ZOHO_") and "MAIL" not in slug:
        direct = _zoho_direct_exec(slug, args)
        if not (isinstance(direct, dict) and direct.get("error")):
            print("ZOHO VIA DIRECT BYPASS:", slug)
            return direct
        return {"error": "Direct bypass failed (%s); Composio failed (%s)" % (str(direct.get("error"))[:220], json.dumps(resp, default=str)[:80])}
    return resp"""
new1 = """def zoho_exec(slug, args):
    # zoho-direct-first-v1: CRM tries direct Render->Zoho FIRST, so Zoho works
    # with no Composio at all (no Composio quota/chat dependency). The Composio
    # bridge is only a backup for CRM. Zoho Mail slugs still use Composio first.
    is_crm = slug.startswith("ZOHO_") and "MAIL" not in slug
    direct_error = None
    if is_crm and _zoho_direct_configured():
        direct = _zoho_direct_exec(slug, args)
        if not (isinstance(direct, dict) and direct.get("error")):
            print("ZOHO VIA DIRECT (primary, no Composio):", slug)
            return direct
        direct_error = str(direct.get("error"))[:220]
    try:
        resp = composio.tools.execute(slug=slug, arguments=args, user_id=COMPOSIO_USER_ID, dangerously_skip_version_check=True)
    except TypeError:
        try:
            resp = composio.tools.execute(slug, args, COMPOSIO_USER_ID)
        except Exception as e:
            resp = {"error": str(e)}
    except Exception as e:
        resp = {"error": str(e)}
    if _composio_failed(resp) and is_crm:
        if direct_error:
            return {"error": "Direct Zoho failed (%s); Composio backup failed (%s)" % (direct_error, json.dumps(resp, default=str)[:80])}
        direct = _zoho_direct_exec(slug, args)
        if not (isinstance(direct, dict) and direct.get("error")):
            print("ZOHO VIA DIRECT BYPASS:", slug)
            return direct
        return {"error": "Direct bypass failed (%s); Composio failed (%s)" % (str(direct.get("error"))[:220], json.dumps(resp, default=str)[:80])}
    if direct_error and is_crm:
        print("ZOHO VIA COMPOSIO BRIDGE (direct failed, backup worked):", slug)
    return resp"""
if src.count(old1) != 1:
    print("FAIL: anchor zoho_exec not found exactly once"); sys.exit(1)
src = src.replace(old1, new1, 1)

# 2) /debug path label
old2 = '        "zoho_path": "composio-first,direct-crm-fallback-v1",'
new2 = '        "zoho_path": "direct-first,composio-bridge-fallback-v1",\n        "zoho_direct_first": "zoho-direct-first-v1",'
if src.count(old2) != 1:
    print("FAIL: anchor zoho_path not found exactly once"); sys.exit(1)
src = src.replace(old2, new2, 1)

# 3) /zoho-direct-test route (direct only, no Composio, no lead data - count only)
old3 = '@app.route("/composio-zoho-connect", methods=["GET"])'
new3 = """@app.route("/zoho-direct-test", methods=["GET"])
def zoho_direct_test():
    # Tests ONLY the direct Render->Zoho path. Composio is not called here.
    if not _zoho_direct_configured():
        return jsonify({"version": "zoho-direct-first-v1", "direct_configured": False, "direct_ok": False, "error": "Direct Zoho not configured in Render env"}), 207
    resp = _zoho_direct_exec("ZOHO_GET_ZOHO_RECORDS", {"module_api_name": "Leads", "fields": "id", "per_page": 1})
    if isinstance(resp, dict) and not resp.get("error"):
        rows = (resp.get("data") or {}).get("data") or []
        return jsonify({"version": "zoho-direct-first-v1", "direct_configured": True, "direct_ok": True, "via": resp.get("via", "direct_zoho"), "sample_count": len(rows)}), 200
    err = str((resp or {}).get("error") or "unknown")[:300] if isinstance(resp, dict) else "unknown"
    return jsonify({"version": "zoho-direct-first-v1", "direct_configured": True, "direct_ok": False, "error": err}), 207


@app.route("/composio-zoho-connect", methods=["GET"])"""
if src.count(old3) != 1:
    print("FAIL: anchor composio-zoho-connect route not found exactly once"); sys.exit(1)
src = src.replace(old3, new3, 1)

# 4) Token helper: also test the REFRESH token itself (not just the one-time code exchange)
old4 = """    crm_test = "not tested"
    at = d.get("access_token")
    if at:
        try:
            cr = requests.get(ZOHO_CRM_API_URL + "/crm/v8/Leads", params={"per_page": 1, "fields": "id"}, headers={"Authorization": "Zoho-oauthtoken " + at}, timeout=30)
            crm_test = "OK - Zoho CRM read worked" if cr.status_code in (200, 204) else ("failed HTTP " + str(cr.status_code))
        except Exception:
            crm_test = "network error during CRM test" """
new4 = """    crm_test = "not tested"
    at = d.get("access_token")
    if at:
        try:
            cr = requests.get(ZOHO_CRM_API_URL + "/crm/v8/Leads", params={"per_page": 1, "fields": "id"}, headers={"Authorization": "Zoho-oauthtoken " + at}, timeout=30)
            crm_test = "OK - Zoho CRM read worked" if cr.status_code in (200, 204) else ("failed HTTP " + str(cr.status_code))
        except Exception:
            crm_test = "network error during CRM test"
    refresh_test = "not tested"
    try:
        rr = requests.post(ZOHO_ACCOUNTS_URL + "/oauth/v2/token", data={"grant_type": "refresh_token", "client_id": ZOHO_CLIENT_ID, "client_secret": ZOHO_CLIENT_SECRET, "refresh_token": token}, timeout=30)
        rd = rr.json() if rr.content else {}
        rat = rd.get("access_token")
        if not rat:
            refresh_test = "failed error=" + str(rd.get("error") or "unknown")[:80]
        else:
            rc = requests.get(ZOHO_CRM_API_URL + "/crm/v8/Leads", params={"per_page": 1, "fields": "id"}, headers={"Authorization": "Zoho-oauthtoken " + rat}, timeout=30)
            refresh_test = "OK - refresh token works for CRM read" if rc.status_code in (200, 204) else ("failed HTTP " + str(rc.status_code))
    except Exception:
        refresh_test = "network error during refresh test" """
if src.count(old4) != 1:
    print("FAIL: anchor helper crm_test not found exactly once"); sys.exit(1)
src = src.replace(old4, new4, 1)

# 5) Token helper success page: show the refresh test result
q3 = chr(34) * 3
old5 = "<p>CRM test: <b>" + q3 + " + crm_test + " + q3 + "</b></p>"
new5 = "<p>CRM test: <b>" + q3 + " + crm_test + " + q3 + "</b><br>Refresh test: <b>" + q3 + " + refresh_test + " + q3 + "</b></p><p>Only save this token in Render if Refresh test says OK.</p>"
if src.count(old5) != 1:
    print("FAIL: anchor helper CRM test page line not found exactly once"); sys.exit(1)
src = src.replace(old5, new5, 1)

p.write_text(src)
print("Patched concierge.py with zoho-direct-first-v1")
