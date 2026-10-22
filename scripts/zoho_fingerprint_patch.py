import pathlib, sys
p = pathlib.Path("concierge.py")
src = p.read_text()
MARKER = "zoho-fingerprint-v1"
if MARKER in src:
    print("Already patched (zoho-fingerprint-v1 present) - no change.")
    sys.exit(0)

# 1) Fingerprint helper, inserted before _zoho_direct_configured
old1 = '''def _zoho_direct_configured():
    return bool(ZOHO_CLIENT_ID and ZOHO_CLIENT_SECRET and ZOHO_REFRESH_TOKEN)'''
new1 = '''def _zoho_token_fingerprint(token):
    # zoho-fingerprint-v1: safe diagnostic only - sha256 first 8 hex chars + dot-part lengths. Never returns the token itself.
    t = (token or "").strip()
    if not t:
        return {"fp": "", "parts": []}
    import hashlib
    return {"fp": hashlib.sha256(t.encode("utf-8")).hexdigest()[:8], "parts": [len(x) for x in t.split(".")]}

def _zoho_direct_configured():
    return bool(ZOHO_CLIENT_ID and ZOHO_CLIENT_SECRET and ZOHO_REFRESH_TOKEN)'''
if src.count(old1) != 1:
    print("FAIL: anchor _zoho_direct_configured not found exactly once"); sys.exit(1)
src = src.replace(old1, new1)

# 2) /debug fields
old2 = '        "zoho_refresh_token_len": len(ZOHO_REFRESH_TOKEN),'
new2 = '''        "zoho_refresh_token_len": len(ZOHO_REFRESH_TOKEN),
        "zoho_fingerprint": "zoho-fingerprint-v1",
        "zoho_refresh_fp": _zoho_token_fingerprint(ZOHO_REFRESH_TOKEN),
        "zoho_client_fp": _zoho_token_fingerprint(ZOHO_CLIENT_ID),'''
if src.count(old2) != 1:
    print("FAIL: anchor zoho_refresh_token_len not found exactly once"); sys.exit(1)
src = src.replace(old2, new2)

# 3) Helper success page: show fingerprint right under the textarea
old3 = '''<textarea readonly style="width:100%;height:90px">""" + safe + """</textarea>
<p><b>Do not paste this in chat, GitHub, or email. Close this page after saving.</b></p></body></html>"""'''
new3 = '''<textarea readonly style="width:100%;height:90px">""" + safe + """</textarea>
<p>Token fingerprint (safe to share, it is NOT the token): <b>""" + _zoho_token_fingerprint(token)["fp"] + """</b> parts=""" + str(_zoho_token_fingerprint(token)["parts"]) + """<br>After you Save in Render and it redeploys, /debug zoho_refresh_fp must match this fingerprint.</p>
<p><b>Do not paste this in chat, GitHub, or email. Close this page after saving.</b></p></body></html>"""'''
if src.count(old3) != 1:
    print("FAIL: anchor helper textarea not found exactly once"); sys.exit(1)
src = src.replace(old3, new3)

p.write_text(src)
print("Patched concierge.py with zoho-fingerprint-v1")
