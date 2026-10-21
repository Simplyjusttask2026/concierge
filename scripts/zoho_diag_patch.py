import pathlib
p = pathlib.Path('concierge.py')
s = p.read_text()
if 'error-code-v1' in s:
    print('Already patched')
    raise SystemExit(0)
old_token = 'raise Exception("Direct Zoho token failed HTTP %s: %s" % (r.status_code, json.dumps(d)[:250]))'
new_token = 'raise Exception("Direct Zoho token failed HTTP %s: error=%s" % (r.status_code, str(d.get("error") or "unknown")[:80]))'
assert old_token in s, 'token error anchor missing'
s = s.replace(old_token, new_token, 1)
old_exec = 'return {"error": "Composio failed (%s); direct bypass failed (%s)" % (json.dumps(resp, default=str)[:200], str(direct.get("error"))[:200])}'
new_exec = 'return {"error": "Direct bypass failed (%s); Composio failed (%s)" % (str(direct.get("error"))[:220], json.dumps(resp, default=str)[:80])}'
assert old_exec in s, 'zoho_exec error anchor missing'
s = s.replace(old_exec, new_exec, 1)
debug_anchor = '"zoho_path": "composio-first,direct-crm-fallback-v1",'
assert debug_anchor in s, 'debug anchor missing'
s = s.replace(debug_anchor, debug_anchor + '\n        "zoho_direct_diag": "error-code-v1",', 1)
p.write_text(s)
print('patched', len(s))
