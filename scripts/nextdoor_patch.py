import pathlib
p = pathlib.Path('scripts/nextdoor_watcher.py')
s = p.read_text()
s = s.replace('"can anyone", "does anyone know"]', '"can anyone", "does anyone know", "anyone know", "know of", "anyone recommend"]')
s = s.replace('INTENT = ["looking for",', 'INTENT = ["looking for", "looking to",')
if '"repair"' not in s:
    s = s.replace('"drywall", "door", "fence",', '"drywall", "door", "fence", "repair", "screen",')
if 'nextdoor-watcher-v2' not in s:
    s += chr(10) + 'import json as _json' + chr(10)
    s += '''def zoho_payload(author, text, score, draft):
    author = (author or "Nextdoor Neighbor").strip()
    return {"module_api_name": "Leads", "data": [{"Last_Name": author, "Lead_Source": "Nextdoor", "Lead_Status": "Not Contacted", "Description": ("Nextdoor post (score %s): %s | Draft (NOT SENT): %s" % (score, str(text)[:600], draft))[:1900]}]}
def process_posts(posts):
    out = []
    for post in posts or []:
        author = post.get("author") or "Neighbor"; text = post.get("text") or ""
        score = score_post(text, int(post.get("age_min") or 60))
        first = str(author).split()[0] if str(author).split() else "there"
        item = {"author": author, "neighborhood": post.get("neighborhood"), "age_min": post.get("age_min"), "score": score, "tier": ("real_lead" if score >= 80 else "watch" if score >= 70 else "skip")}
        if score >= 70:
            item["draft_comment"] = draft_comment(first, text[:90]); item["draft_dm"] = draft_dm(first, text[:90])
        if score >= 80:
            item["zoho_payload"] = zoho_payload(author, text, score, item["draft_comment"])
        out.append(item)
    return {"version": "nextdoor-watcher-v2", "sends_made": 0, "posts": sorted(out, key=lambda x: -x["score"]), "counts": {"real_lead": sum(1 for x in out if x["score"] >= 80), "watch": sum(1 for x in out if 70 <= x["score"] < 80), "skip": sum(1 for x in out if x["score"] < 70)}}
def _selftest():
    r = process_posts([{"author": "Fake Neighbor", "text": "Looking for recommendations for a landscaper in Apopka, need mowing help", "age_min": 30}, {"author": "Fake Two", "text": "Lost dog please share", "age_min": 30}])
    assert r["counts"]["real_lead"] == 1 and r["counts"]["skip"] == 1, r
    return r
if __name__ == "__main__":
    import argparse, sys
    ap = argparse.ArgumentParser(); ap.add_argument("--input"); ap.add_argument("--out"); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        print(_json.dumps(_selftest(), indent=2)); sys.exit(0)
    posts = _json.load(open(a.input)) if a.input else []
    result = process_posts(posts); txt = _json.dumps(result, indent=2)
    if a.out: open(a.out, "w").write(txt)
    print(txt)
'''
    p.write_text(s)
    print('watcher patched', len(s))
else:
    print('watcher already patched')

def append_once(path, marker, text):
    pp = pathlib.Path(path); ss = pp.read_text()
    if marker not in ss:
        pp.write_text(ss + text); print('appended', path)
append_once('SOPS/WHATSAPP_TEMPLATE.md', 'UPDATE 2026-10-21', '\n## UPDATE 2026-10-21\nAPI create tried once: 400 WABA not allowed to manage templates. Do not retry via API. Owner Meta Business Suite step remains; templates 0, phone NOT_VERIFIED at last check.\n')
append_once('FRANKENSTEIN_STATUS.md', 'BUILT 2026-10-21 OVERNIGHT', '\n## BUILT 2026-10-21 OVERNIGHT\n- Call Center: /call-center plan v1 draft-only + daily report section. Unit-tested fake leads, compile OK.\n- Nextdoor: watcher v2 CLI, live Kernel scan 3 leads scored 80 saved to Zoho verified by ID, 1 watch, NO post/comment/DM sent (owner go per item).\n- Nextdoor timer workflow every 2h proves watcher logic only; live Kernel hunt needs chat/agent session.\n- WhatsApp template API FAILED WABA not allowed. Owner Meta step unchanged.\n')
