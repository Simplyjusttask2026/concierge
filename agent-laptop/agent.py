"""Simply Just Task - Laptop Agent. Nextdoor hunter: read/score/draft/save. No sends without owner go. Free only."""
import os, json, datetime, logging, argparse, csv, pathlib
from zoneinfo import ZoneInfo
ET = ZoneInfo("America/New_York")
BASE = pathlib.Path(__file__).parent
DATA = BASE / "data"; DATA.mkdir(exist_ok=True)
LEADS_CSV = DATA / "leads.csv"; SEEN_JSON = DATA / "seen.json"
logging.basicConfig(filename=DATA / "agent.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("sjt")
BOOKING = "https://cal.com/simply-just-task/simplybook"; PHONE = "(352) 849-2344"
SERVICES = {"handyman": ["handyman","furniture assembly","tv mounting","mount","install","toilet","window ac","drywall","door","fence","paint","odd job","home repair"], "cleaning": ["cleaning","cleaner","house cleaning","deep clean","move out"], "lawn": ["lawn","landscap","yard","mow","trim","palm","tree","garden","bush"], "pressure": ["pressure wash","power wash","driveway clean"], "errands": ["errand","pickup","delivery","concierge","home watch","house sitting","pet sitting","dog walking","senior","help moving"], "engine": ["mower","lawnmower","small engine","toro"]}
INTENT = ["looking for","recommend","need someone","need","help","any recommendations","who do you use","estimate","quote","can anyone","does anyone know"]
SKIP = ["lost dog","lost cat","found dog","found cat","politics","election","for sale","moving sale","lost pet","found pet","sponsored"]
def score_post(text, age_min=60):
    t = (text or "").lower()
    if any(s in t for s in SKIP): return 0
    score = 0
    for keys in SERVICES.values():
        if any(k in t for k in keys): score += 45; break
    if any(i in t for i in INTENT): score += 30
    if "apopka" in t or "central florida" in t: score += 10
    if age_min <= 120: score += 15
    elif age_min <= 1440: score += 5
    return min(score, 100)
def draft_comment(first, job):
    return f"Hi {first}, I'm Anthony - I run Simply Just Task right here in Apopka. I can help with {job}. Happy to take a look first and give you a straight starting range, no pressure. Book: {BOOKING} or {PHONE}. What's the timing you're hoping for?"
def now_et(): return datetime.datetime.now(ET)
def in_window(dt=None):
    dt = dt or now_et(); return 7 <= dt.hour < 22
def load_seen():
    try: return set(json.loads(SEEN_JSON.read_text()))
    except Exception: return set()
def save_seen(s): SEEN_JSON.write_text(json.dumps(sorted(s)))
def append_lead(row):
    exists = LEADS_CSV.exists()
    with open(LEADS_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["time_et","source","score","status","text","draft_comment","url"])
        if not exists: w.writeheader()
        w.writerow({k: row.get(k, "") for k in w.fieldnames})
def scrape_nextdoor(max_posts=40):
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        log.error("Playwright missing: %s", e); return []
    profile = str((BASE / "browser_profile").resolve()); out = []
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(profile, headless=False, viewport={"width": 1300, "height": 900})
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://nextdoor.com/news_feed/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4000)
        for _ in range(6):
            page.mouse.wheel(0, 900); page.wait_for_timeout(1500)
        texts = page.locator("body").inner_text(timeout=10000)
        chunks = [c.strip() for c in texts.split("\n\n") if len(c.strip()) > 40]
        for c in chunks[:max_posts]: out.append({"text": c[:1200], "url": "https://nextdoor.com/news_feed/"})
        ctx.close()
    return out
def run_once():
    if not in_window(): print("Outside 7am-10pm ET window."); return
    seen = load_seen(); leads = 0
    posts = scrape_nextdoor()
    if not posts: print("No posts scraped - run login_nextdoor.bat first."); return
    for post in posts:
        key = post["text"][:120]
        if key in seen: continue
        seen.add(key); sc = score_post(post["text"], 60)
        if sc >= 80: leads += 1; append_lead({"time_et": now_et().isoformat(), "source": "Nextdoor", "score": sc, "status": "DRAFT_ONLY - owner go needed", "text": post["text"][:500], "draft_comment": draft_comment("neighbor", "this"), "url": post["url"]})
        elif sc >= 70: append_lead({"time_et": now_et().isoformat(), "source": "Nextdoor", "score": sc, "status": "watch", "text": post["text"][:500], "draft_comment": "", "url": post["url"]})
    save_seen(seen)
    p = DATA / f"report_{now_et().strftime('%Y%m%d_%H%M')}.txt"
    p.write_text(f"SJT Nextdoor Report {now_et().isoformat()}\nReal leads >=80: {leads}\nDraft-only. No send. Review data/leads.csv, approve: go comment <Name>", encoding="utf-8")
    print(p.read_text()); print("Report:", p)
if __name__ == "__main__":
    argparse.ArgumentParser().parse_args(); run_once()
