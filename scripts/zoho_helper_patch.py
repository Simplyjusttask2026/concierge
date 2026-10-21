import pathlib, sys
p = pathlib.Path("concierge.py")
src = p.read_text()
MARKER = "zoho-token-helper-v1"
if MARKER in src:
    print("Already patched, no change")
    sys.exit(0)
debug_anchor = '"zoho_direct_diag": "error-code-v2-clean-format",'
if debug_anchor not in src:
    print("ERROR debug anchor not found"); sys.exit(1)
src = src.replace(debug_anchor, debug_anchor + '\n        "zoho_token_helper": "zoho-token-helper-v1",', 1)
route = '''
@app.route("/zoho-token-helper", methods=["GET", "POST"])
def zoho_token_helper():
    # zoho-token-helper-v1: owner-only one-time exchange. A grant code can only be
    # created while logged into the owner Zoho API Console, so possession of a fresh
    # code is the gate. This route never logs or stores the code or the token.
    headers = {"Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow"}
    form = """<!doctype html><html><head><title>Zoho Token Helper</title></head>
<body style="font-family:Arial;max-width:640px;margin:40px auto;padding:0 16px">
<h2>Zoho Token Helper</h2>
<p>1. In the Zoho API Console, open the SAME Self Client as the Client ID/Secret in Render.</p>
<p>2. Generate Code with CRM scope, 10 minutes. That code is NOT the refresh token.</p>
<p>3. Paste that fresh code below within 10 minutes and click Exchange. Codes work once only.</p>
<form method="POST"><input name="code" style="width:100%;padding:10px" autocomplete="off" placeholder="Paste fresh Zoho grant code here">
<button style="margin-top:12px;padding:10px 18px">Exchange</button></form>
<p>Never paste the code or the result in chat, GitHub, or email.</p></body></html>"""
    if request.method == "GET":
        return form, 200, headers
    code = (request.form.get("code") or "").strip().strip(chr(34)).strip(chr(39)).strip()
    if not code:
        return form.replace("</body>", "<p><b>Error: no code entered.</b></p></body>"), 400, headers
    if not (ZOHO_CLIENT_ID and ZOHO_CLIENT_SECRET):
        return form.replace("</body>", "<p><b>Error: ZOHO_CLIENT_ID / ZOHO_CLIENT_SECRET not set in Render.</b></p></body>"), 500, headers
    try:
        r = requests.post(ZOHO_ACCOUNTS_URL + "/oauth/v2/token", data={"grant_type": "authorization_code", "client_id": ZOHO_CLIENT_ID, "client_secret": ZOHO_CLIENT_SECRET, "code": code}, timeout=30)
        d = r.json() if r.content else {}
    except Exception:
        return form.replace("</body>", "<p><b>Exchange request failed: network error. Generate a new code and retry.</b></p></body>"), 502, headers
    token = d.get("refresh_token")
    if not token:
        err = str(d.get("error") or "unknown")[:80]
        return form.replace("</body>", "<p><b>Zoho exchange failed: error=" + err + "</b>. Codes expire fast and work once only - generate a NEW code in the same Self Client and retry.</p></body>"), 400, headers
    crm_test = "not tested"
    at = d.get("access_token")
    if at:
        try:
            cr = requests.get(ZOHO_CRM_API_URL + "/crm/v8/Leads", params={"per_page": 1, "fields": "id"}, headers={"Authorization": "Zoho-oauthtoken " + at}, timeout=30)
            crm_test = "OK - Zoho CRM read worked" if cr.status_code in (200, 204) else ("failed HTTP " + str(cr.status_code))
        except Exception:
            crm_test = "network error during CRM test"
    safe = str(token).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    out = """<!doctype html><html><head><title>Zoho Refresh Token</title></head>
<body style="font-family:Arial;max-width:640px;margin:40px auto;padding:0 16px">
<h2>Copy this refresh token into Render</h2>
<p>CRM test: <b>""" + crm_test + """</b></p>
<p>Render - sjt-concierge - Environment - ZOHO_REFRESH_TOKEN - paste this - Save. Then tell the assistant: render zoho saved.</p>
<textarea readonly style="width:100%;height:90px">""" + safe + """</textarea>
<p><b>Do not paste this in chat, GitHub, or email. Close this page after saving.</b></p></body></html>"""
    return out, 200, headers

'''
anchor = '@app.route("/ping")'
if src.count(anchor) != 1:
    print("ERROR ping anchor count", src.count(anchor)); sys.exit(1)
src = src.replace(anchor, route + "\n" + anchor, 1)
p.write_text(src)
print("Patched concierge.py with zoho-token-helper-v1")
