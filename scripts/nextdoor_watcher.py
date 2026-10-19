"""
NEXTDOOR-AGENT-01 watcher — TEAM scoring + dedupe + draft logic
Status: BUILT 2026-10-19, UPDATED 2026-10-19 convo 4 (personal team, website services).
Owner: YES he has a team (Scout/Qualifier/Writer/Image Maker/Poster/Reporter) — see SOPS/NEXTDOOR_KERNEL.md
Schedule: SAME as other AIs — inside Daily 9AM machine (GitHub daily-9am.yml -> /run-daily), NOT a separate Nextdoor timer.
Nextdoor has no API/webhook. Live browser steps run via Kernel MCP with profile nextdoor-anthony-personal.
Posting is intentionally NOT implemented here. No send function in this file.
Human `go comment <name>` / `go post` required, then Poster posts via Kernel manually and verifies.
"""
# SERVICES from simplyjusttask.com/services + homepage (2026-10-19). Residential only per BRAIN.
SERVICES = {
    "handyman": ["handyman", "furniture assembly", "tv mounting", "mount", "install", "toilet", "window ac", "drywall", "door", "fence", "painting", "paint", "touch-up", "touch up", "odd job", "home repair", "maintenance"],
    "cleaning": ["cleaning", "cleaner", "house cleaning", "deep clean", "move out clean", "move-in", "move out"],
    "lawn": ["lawn", "landscap", "yard", "mow", "mowing", "trim", "palm", "tree", "garden", "bush", "bougainvillea"],
    "pressure": ["pressure wash", "power wash", "driveway clean"],
    "errands_concierge": ["errand", "pickup", "pick up", "delivery", "concierge", "personal assistance", "property check", "home watch", "house sitting", "pet sitting", "dog walking", "senior", "help moving"],
    "small_engine": ["mower", "lawnmower", "lawn mower", "small engine", "toro"],
}
INTENT = ["looking for", "recommend", "need someone", "need", "help", "any recommendations", "who do you use", "estimate", "quote", "can anyone", "does anyone know"]
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
