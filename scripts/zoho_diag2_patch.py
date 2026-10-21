import pathlib
p = pathlib.Path('concierge.py')
s = p.read_text()
if 'error-code-v2-clean-format' in s:
    print('Already patched')
    raise SystemExit(0)
old_cfg = '''ZOHO_CLIENT_ID = os.environ.get("ZOHO_CLIENT_ID", "")
ZOHO_CLIENT_SECRET = os.environ.get("ZOHO_CLIENT_SECRET", "")
ZOHO_REFRESH_TOKEN = os.environ.get("ZOHO_REFRESH_TOKEN", "")
ZOHO_ACCOUNTS_URL = os.environ.get("ZOHO_ACCOUNTS_URL", "https://accounts.zoho.com").rstrip("/")
ZOHO_CRM_API_URL = os.environ.get("ZOHO_CRM_API_URL", "https://www.zohoapis.com").rstrip("/")'''
new_cfg = '''def _clean_secret_env(name, default=""):
    return os.environ.get(name, default).strip().strip(chr(34)).strip(chr(39)).strip()
ZOHO_CLIENT_ID = _clean_secret_env("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = _clean_secret_env("ZOHO_CLIENT_SECRET")
ZOHO_REFRESH_TOKEN = _clean_secret_env("ZOHO_REFRESH_TOKEN")
ZOHO_ACCOUNTS_URL = _clean_secret_env("ZOHO_ACCOUNTS_URL", "https://accounts.zoho.com").rstrip("/")
ZOHO_CRM_API_URL = _clean_secret_env("ZOHO_CRM_API_URL", "https://www.zohoapis.com").rstrip("/")'''
assert old_cfg in s, 'config anchor missing'
s = s.replace(old_cfg, new_cfg, 1)
old_dbg = '"zoho_direct_diag": "error-code-v1",'
new_dbg = '''"zoho_direct_diag": "error-code-v2-clean-format",
        "zoho_accounts_host": ZOHO_ACCOUNTS_URL.split("://")[-1].split("/")[0],
        "zoho_crm_host": ZOHO_CRM_API_URL.split("://")[-1].split("/")[0],
        "zoho_client_id_prefix_ok": ZOHO_CLIENT_ID.startswith("1000."),
        "zoho_refresh_prefix_ok": ZOHO_REFRESH_TOKEN.startswith("1000."),
        "zoho_client_id_len": len(ZOHO_CLIENT_ID),
        "zoho_client_secret_len": len(ZOHO_CLIENT_SECRET),
        "zoho_refresh_token_len": len(ZOHO_REFRESH_TOKEN),'''
assert old_dbg in s, 'debug anchor missing'
s = s.replace(old_dbg, new_dbg, 1)
p.write_text(s)
print('patched', len(s))
