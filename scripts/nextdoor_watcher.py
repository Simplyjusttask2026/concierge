"""
NEXTDOOR-AGENT-01 watcher — scoring + dedupe + draft logic
Status: BUILT 2026-10-19, first run must be supervised.
Nextdoor has no API/webhook. Live browser steps run via Kernel MCP.
Posting is intentionally NOT implemented. No send function.
Human `go <name>` required, then assistant posts via Kernel manually.
"""
SERVICES = {
    "handyman": ["handyman","fix","repair","install","toilet","window ac","drywall","door","fence"],
    "cleaning": ["cleaning","cleaner","house cleaning","deep clean","move out clean"],
    "lawn": ["lawn","landscap","yard","mowing","trim","palm","tree","garden"],
    "pressure": ["pressure wash","power wash","driveway clean"],
    "errands": ["errand","pickup","delivery","concierge","help moving"],
}
INTENT = ["looking for","recommend","need","help","any recommendations","who do you use","estimate","quote"]
SKIP = ["lost dog","lost cat","found dog","found cat","politics","election","for sale","moving sale"]

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
    if "apopka" in t or "central florida" in t:
        score += 10
    if age_min <= 120:
        score += 15
    elif age_min <= 1440:
        score += 5
    return min(score, 100)

def draft_comment(author_first: str, job: str) -> str:
    return (f"Hi {author_first}, I'm Anthony with Simply Just Task here in Apopka \u2014 "
            f"we help neighbors with {job}. Happy to take a look and give you a straight "
            f"estimate, no pressure. You can book a time here: "
            f"https://cal.com/simply-just-task/simplybook or reach me at (352) 849-2344. "
            f"What's the timing you're hoping for?")
# >=70 alert+draft+Zoho, 40-69 morning summary, <40 log only.
