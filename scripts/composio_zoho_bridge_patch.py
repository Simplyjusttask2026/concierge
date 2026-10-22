import pathlib, sys
p = pathlib.Path("concierge.py")
src = p.read_text()
MARKER = "composio-zoho-bridge-v1"
if MARKER in src:
    print("Already patched (composio-zoho-bridge-v1 present) - no change.")
    sys.exit(0)

# 1) Flask redirect import
old1 = "from flask import Flask, request, jsonify"
new1 = "from flask import Flask, request, jsonify, redirect"
if src.count(old1) != 1:
    print("FAIL: anchor flask import not found exactly once"); sys.exit(1)
src = src.replace(old1, new1)

# 2) Composio bridge helpers, inserted before _composio_failed
old2 = "def _composio_failed(resp):"
new2 = """def _obj_field(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)

def _items_of(resp):
    items = _obj_field(resp, "items", None)
    if items is None and isinstance(resp, dict):
        items = resp.get("items") or resp.get("data") or resp.get("results") or []
    return list(items or [])

def _composio_zoho_connected_status():
    # composio-zoho-bridge-v1: returns (connected_bool, check_ok_bool). Never exposes account ids.
    try:
        resp = composio.connected_accounts.list(user_ids=[COMPOSIO_USER_ID], toolkit_slugs=["zoho"], statuses=["ACTIVE"])
        return (len(_items_of(resp)) > 0, True)
    except Exception:
        return (False, False)

def _zoho_auth_config_id():
    # Reuse an enabled Zoho auth config in this Composio project (prefer Composio-managed), or create one.
    try:
        resp = composio.auth_configs.list(toolkit_slug="zoho")
        items = [x for x in _items_of(resp) if str(_obj_field(x, "status", "ENABLED")) in ("ENABLED", "None", "")]
        items = [x for x in items if str(_obj_field(x, "auth_scheme", "OAUTH2")) in ("OAUTH2", "DCR_OAUTH", "None", "")]
        if items:
            items_sorted = sorted(items, key=lambda x: (1 if _obj_field(x, "is_composio_managed") else 0, 1 if _obj_field(x, "type") == "default" else 0, str(_obj_field(x, "created_at", "") or "")), reverse=True)
            ac_id = _obj_field(items_sorted[0], "id")
            if ac_id:
                return str(ac_id)
    except Exception:
        pass
    try:
        getter = getattr(composio.toolkits, "_get_auth_config_id", None)
        if callable(getter):
            return str(getter("zoho"))
    except Exception:
        pass
    created = composio.auth_configs.create("zoho", {"type": "use_composio_managed_auth", "tool_access_config": {"tools_for_connected_account_creation": []}})
    ac = _obj_field(created, "auth_config", created)
    ac_id = _obj_field(ac, "id")
    if not ac_id:
        raise Exception("Composio Zoho auth config has no id")
    return str(ac_id)

def _composio_failed(resp):"""
if src.count(old2) != 1:
    print("FAIL: anchor _composio_failed not found exactly once"); sys.exit(1)
src = src.replace(old2, new2, 1)

# 3) /debug bridge status
old3 = '@app.route("/debug")\ndef debug():\n    return jsonify({'
new3 = '@app.route("/debug")\ndef debug():\n    _zb_connected, _zb_ok = _composio_zoho_connected_status()\n    return jsonify({\n        "composio_bridge": "composio-zoho-bridge-v1",\n        "composio_zoho_connected": _zb_connected,\n        "composio_zoho_status_check": "ok" if _zb_ok else "error",'
if src.count(old3) != 1:
    print("FAIL: anchor /debug not found exactly once"); sys.exit(1)
src = src.replace(old3, new3, 1)

# 4) Connect routes, inserted before the Zoho token helper route
old4 = '@app.route("/zoho-token-helper", methods=["GET", "POST"])'
new4 = """@app.route("/composio-zoho-connect", methods=["GET"])
def composio_zoho_connect():
    # Owner connects Zoho to Composio (the middleman) for COMPOSIO_USER_ID.
    # Render never receives or stores a Zoho token here; Composio holds it.
    # This route self-disables once an ACTIVE Zoho connection exists.
    headers = {"Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow"}
    page_start = "<!doctype html><html><head><title>Connect Zoho via Composio</title></head><body style=\\"font-family:Arial;max-width:640px;margin:40px auto;padding:0 16px\\">"
    connected, check_ok = _composio_zoho_connected_status()
    if connected:
        return page_start + "<h2>Zoho is already connected via Composio</h2><p>This connect page is now disabled. Test /call-center.</p></body></html>", 200, headers
    try:
        auth_config_id = _zoho_auth_config_id()
        callback_url = request.url_root.rstrip("/") + "/composio-zoho-connected"
        req_obj = composio.connected_accounts.link(user_id=COMPOSIO_USER_ID, auth_config_id=auth_config_id, callback_url=callback_url)
        redirect_url = _obj_field(req_obj, "redirect_url")
        if not redirect_url and isinstance(req_obj, dict):
            redirect_url = req_obj.get("redirectUrl") or req_obj.get("redirect_url")
        if not redirect_url:
            return page_start + "<h2>Could not create Zoho connect link</h2><p>Composio did not return a redirect link. Tell the assistant: bridge link failed (no redirect).</p></body></html>", 502, headers
        return redirect(str(redirect_url))
    except Exception as e:
        msg = str(e).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")[:240]
        return page_start + "<h2>Could not create Zoho connect link</h2><p>Error: " + msg + "</p><p>Tell the assistant: bridge link failed.</p></body></html>", 502, headers

@app.route("/composio-zoho-connected", methods=["GET"])
def composio_zoho_connected():
    headers = {"Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow"}
    page_start = "<!doctype html><html><head><title>Zoho Connect Finished</title></head><body style=\\"font-family:Arial;max-width:640px;margin:40px auto;padding:0 16px\\">"
    connected, check_ok = _composio_zoho_connected_status()
    if connected:
        return page_start + "<h2>Zoho connected via Composio</h2><p>You can close this page. Tell the assistant: zoho bridge connected</p></body></html>", 200, headers
    return page_start + "<h2>Zoho authorization finished</h2><p>The connection may still be processing. You can close this page. Tell the assistant: zoho bridge connected</p></body></html>", 200, headers


@app.route("/zoho-token-helper", methods=["GET", "POST"])"""
if src.count(old4) != 1:
    print("FAIL: anchor zoho-token-helper route not found exactly once"); sys.exit(1)
src = src.replace(old4, new4, 1)

p.write_text(src)
print("Patched concierge.py with composio-zoho-bridge-v1")
