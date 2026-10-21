import pathlib
p = pathlib.Path('concierge.py')
s = p.read_text()
if 'direct-crm-fallback-v1' in s:
    print('Already patched')
    raise SystemExit(0)
anchor = 'ZOHO_MAIL_ACCOUNT_ID = os.environ.get("ZOHO_MAIL_ACCOUNT_ID", "8048488000000008002")  # tasksupport mailbox\n'
assert anchor in s, 'config anchor missing'
config_add = anchor + '''# Direct Zoho CRM bypass (owner-entered in Render only; never in chat/code).
ZOHO_CLIENT_ID = os.environ.get("ZOHO_CLIENT_ID", "")
ZOHO_CLIENT_SECRET = os.environ.get("ZOHO_CLIENT_SECRET", "")
ZOHO_REFRESH_TOKEN = os.environ.get("ZOHO_REFRESH_TOKEN", "")
ZOHO_ACCOUNTS_URL = os.environ.get("ZOHO_ACCOUNTS_URL", "https://accounts.zoho.com").rstrip("/")
ZOHO_CRM_API_URL = os.environ.get("ZOHO_CRM_API_URL", "https://www.zohoapis.com").rstrip("/")
_zoho_direct_token = {"value": "", "expires_at": 0}
'''
s = s.replace(anchor, config_add, 1)
start = s.index('def zoho_exec(slug, args):')
end = s.index('\ndef zoho_ok', start)
new_exec = '''def _zoho_direct_configured():
    return bool(ZOHO_CLIENT_ID and ZOHO_CLIENT_SECRET and ZOHO_REFRESH_TOKEN)

def _zoho_direct_access_token():
    now = time.time()
    if _zoho_direct_token["value"] and _zoho_direct_token["expires_at"] > now + 60:
        return _zoho_direct_token["value"]
    r = requests.post(ZOHO_ACCOUNTS_URL + "/oauth/v2/token", data={"grant_type": "refresh_token", "client_id": ZOHO_CLIENT_ID, "client_secret": ZOHO_CLIENT_SECRET, "refresh_token": ZOHO_REFRESH_TOKEN}, timeout=30)
    d = r.json() if r.content else {}
    token = d.get("access_token")
    if not token:
        raise Exception("Direct Zoho token failed HTTP %s: %s" % (r.status_code, json.dumps(d)[:250]))
    _zoho_direct_token["value"] = token
    _zoho_direct_token["expires_at"] = now + int(d.get("expires_in") or 3600)
    return token

def _zoho_direct_norm_data(rows):
    out = []
    for row in rows or []:
        if not isinstance(row, dict):
            out.append(row)
            continue
        r2 = dict(row)
        for k, v in list(r2.items()):
            if isinstance(v, dict) and v.get("id") and "module" in v:
                r2[k] = {"id": str(v["id"])}
                if k in ("What_Id", "Who_Id", "Parent_Id"):
                    r2["$se_module"] = str(v["module"])
        out.append(r2)
    return out

def _zoho_direct_exec(slug, args):
    if slug == "ZOHO_MAIL_MESSAGES_SEND_EMAIL":
        return {"error": "Direct Zoho bypass v1 is CRM-only; mail still needs Composio"}
    if not _zoho_direct_configured():
        return {"error": "Direct Zoho bypass not configured in Render env"}
    module = str((args or {}).get("module_api_name") or "")
    if not module:
        return {"error": "Direct Zoho bypass: module_api_name missing"}
    try:
        headers = {"Authorization": "Zoho-oauthtoken " + _zoho_direct_access_token()}
        base = ZOHO_CRM_API_URL + "/crm/v8/" + module
        method, url, params, body = "GET", base, {}, None
        if slug == "ZOHO_SEARCH_ZOHO_RECORDS":
            url = base + "/search"
            params = {k: args[k] for k in ("email", "phone", "word", "criteria", "fields", "per_page", "page") if args.get(k) not in (None, "")}
        elif slug == "ZOHO_GET_ZOHO_RECORDS":
            params = {k: args[k] for k in ("fields", "per_page", "page", "sort_by", "sort_order") if args.get(k) not in (None, "")}
            if args.get("ids"):
                params["ids"] = args["ids"]
        elif slug == "ZOHO_CREATE_ZOHO_RECORD":
            method, url, body = "POST", base, {"data": _zoho_direct_norm_data(args.get("data") or [])}
        elif slug == "ZOHO_UPDATE_ZOHO_RECORD":
            method, url, body = "PUT", base, {"data": _zoho_direct_norm_data(args.get("data") or [])}
        else:
            return {"error": "Direct Zoho bypass does not support slug " + str(slug)}
        r = requests.request(method, url, headers=headers, params=params, json=body, timeout=30)
        if r.status_code == 204:
            return {"data": {"data": [], "info": {}}, "successful": True, "via": "direct_zoho"}
        d = r.json() if r.content else {}
        if r.status_code >= 400:
            return {"error": "Direct Zoho HTTP %s: %s" % (r.status_code, json.dumps(d)[:300])}
        return {"data": d, "successful": True, "via": "direct_zoho"}
    except Exception as e:
        return {"error": "Direct Zoho bypass failed: " + str(e)[:300]}

def _composio_failed(resp):
    if not isinstance(resp, dict):
        return True
    if resp.get("error"):
        return True
    txt = json.dumps(resp, default=str)[:2000]
    return "No connected account found" in txt or "ActionExecute_ConnectedAccountNotFound" in txt

def zoho_exec(slug, args):
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
        return {"error": "Composio failed (%s); direct bypass failed (%s)" % (json.dumps(resp, default=str)[:200], str(direct.get("error"))[:200])}
    return resp
'''
s = s[:start] + new_exec + s[end+1:]
debug_anchor = '"cal_booking_sync": "part3-v1-real-confirmed-only",'
assert debug_anchor in s, 'debug anchor missing'
s = s.replace(debug_anchor, debug_anchor + '\n        "composio_user_id": COMPOSIO_USER_ID,\n        "zoho_direct_bypass_configured": _zoho_direct_configured(),\n        "zoho_path": "composio-first,direct-crm-fallback-v1",', 1)
p.write_text(s)
print('patched', len(s))
