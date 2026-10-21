"""
NEXTDOOR-AGENT-01 watcher — TEAM scoring + dedupe + draft logic
Status: BUILT 2026-10-19, UPDATED 2026-10-19 convo 4 (personal team, website services).
Owner: YES he has a team (Scout/Qualifier/Writer/Image Maker/Poster/Reporter) — see SOPS/NEXTDOOR_KERNEL.md
Schedule: OWNER-SET every 2 hours, 7am-10pm ET — MORE FREQUENT than other AIs (other AIs = 1x/day Daily 9AM).
  Reason: "looking for" job posts go fast. Caps: max 1 own post/day + max 3 replies per 2-hour check.
  Main hunt: neighbors' "looking for" posts for jobs we do -> comment short, direct, neighborly with our info on THEIR post.
  Truth: no auto timer live yet (Daily 9AM workflow 0 runs / secret blocker) — manual supervised runs until a real Nextdoor timer exists.
Nextdoor has no API/webhook. Live browser steps run via Kernel MCP with profile nextdoor-anthony-personal.
Posting is intentionally NOT implemented here. No send function in this file.
Human `go comment <name>` / `go post` required, then Poster posts via Kernel manually and verifies.
"""
# SERVICES from simplyjusttask.com/services + homepage (2026-10-19). Residential only per BRAIN.
SERVICES = {
    "handyman": ["handyman", "furniture assembly", "tv mounting", "mount", "install", "toilet", "window ac", "drywall", "door", "fence", "repair", "screen", "painting", "paint", "touch-up", "touch up", "odd job", "home repair", "maintenance"],
    "cleaning": ["cleaning", "cleaner", "house cleaning", "deep clean", "move out clean", "move-in", "move out"],
    "lawn": ["lawn", "landscap", "yard", "mow", "mowing", "trim", "palm", "tree", "garden", "bush", "bougainvillea"],
    "pressure": ["pressure wash", "power wash", "driveway clean"],
    "errands_concierge": ["errand", "pickup", "pick up", "delivery", "concierge", "personal assistance", "property check", "home watch", "house sitting", "pet sitting", "dog walking", "senior", "help moving"],
    "small_engine": ["mower", "lawnmower", "lawn mower", "small engine", "toro"],
}
INTENT = ["looking for", "looking to", "recommend", "need someone", "need", "help", "any recommendations", "who do you use", "estimate", "quote", "can anyone", "does anyone know", "anyone know", "know of", "anyone recommend"]
SKIP = ["lost dog", "lost cat", "found dog", "found cat", "politics", "election", "for sale", "moving sale", "lost pet", "found pet", "sponsored"]
BOOKING = "https://cal.com/simply-just-task/simplybook"
PHONE = "(352) 849-2344"

def score_post(text: str, age_min: int = 60) -> int:
    t = (text or "").lower()
    if any(s in t for s in SKIP):
        return 0
    score = 0
    for svc, keys in SERVICES.items():
        if any(k in t for k in keys):
            score += 45
            break
    if any(i in t for i in INTENT):
        score += 30
    if "apopka" in t or "central florida" in t or "errol" in t:
        score += 10
    if age_min <= 120:
        score += 15
    elif age_min <= 1440:
        score += 5
    return min(score, 100)

def is_real_lead(score: int) -> bool:
    return score >= 80  # 70-79 = watch, >=80 = real lead (Qualifier rule)

# Hunting priority: fresh "looking for" posts (INTENT phrases) for SERVICES jobs. Writer rule: short, direct, neighborly, with booking+phone.
def draft_comment(author_first: str, job: str) -> str:
    return (f"Hi {author_first}, I'm Anthony — I run Simply Just Task right here in Apopka. "
            f"I can help with {job}. Happy to take a look first and give you a straight starting range, no pressure. "
            f"You can book a consultation here: {BOOKING} or reach me at {PHONE}. "
            f"What's the timing you're hoping for?")

def draft_dm(author_first: str, job: str) -> str:
    return (f"Hi {author_first}, Anthony with Simply Just Task in Apopka — saw your post about {job}. "
            f"I help neighbors with that. Want me to take a look and give you a starting range? "
            f"Booking: {BOOKING} / {PHONE}. No pressure either way.")
# >=80: Zoho + alert + draft comment/DM, wait for owner go. 70-79: daily summary. <70: log only.
# Phone/text/call: NOT live (Retell 0 numbers, parked). Email via /run-daily is the free outreach channel.

import json as _json
def zoho_payload(author, text, score, draft):
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
