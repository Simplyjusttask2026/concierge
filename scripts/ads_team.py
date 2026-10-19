"""
ADS TEAM - draft production helpers (Simply Just Task)
Status: BUILT 2026-10-19. Owner rule: ALL FREE - $0 ad spend.
Owner confirmed: "no all free" - this team only PRODUCES drafts for
free organic channels (Facebook Page, Instagram, X, Nextdoor).
It has NO post/send/boost/pay function. Posting requires owner
`go post <draft>` per SOPS/ADS_TEAM.md, then a human/approved
Social Crew posts it.
See SOPS/ADS_TEAM.md for the 6 roles:
Strategist / Audience Researcher / Copywriter / Creative /
Compliance Checker / Analyst-Reporter.
"""

BOOKING = "https://cal.com/simply-just-task/simplybook"
PHONE = "(352) 849-2344"
TAGLINE = "Reliable Help for Everyday Life."

SERVICES = {
    "handyman": {"label": "Handyman & Home Repairs", "pain": "the fix-it list that keeps growing", "hook": "That fix-it list isn't getting shorter."},
    "cleaning": {"label": "House Cleaning", "pain": "guests coming and the house is not ready", "hook": "Company coming? House not ready?"},
    "lawn": {"label": "Lawn & Yard Care", "pain": "overgrown yard / code violation letter", "hook": "Yard getting away from you?"},
    "pressure": {"label": "Pressure Washing", "pain": "dirty driveway and siding", "hook": "Your driveway called - it wants its color back."},
    "errands": {"label": "Errands & Concierge", "pain": "too many stops, not enough day", "hook": "Too many stops, not enough day?"},
    "senior": {"label": "Senior & Family Help", "pain": "mom/dad needs a hand around the house", "hook": "Could Mom or Dad use an extra hand at home?"},
}

# Compliance: reject drafts with any of these (BRAIN hard rules)
BANNED = [
    "guaranteed price", "guarantee you", "exact price", "% off", "discount",
    "calendly", "cal.com/simply-justtask/15min", "we don't do that", "we dont do that",
    "commercial", "office cleaning", "business cleaning",
]

def compliance_check(text: str) -> list:
    t = (text or "").lower()
    issues = [b for b in BANNED if b in t]
    if BOOKING not in text and "cal.com" in t:
        issues.append("wrong booking link")
    return issues

def draft_facebook(service: str) -> str:
    s = SERVICES[service]
    return (f"{s['hook']} I'm Anthony with Simply Just Task here in Apopka - "
            f"we help busy families, homeowners, and seniors with {s['label'].lower()} "
            f"and the everyday jobs that pile up. {TAGLINE} "
            f"Happy to stop by for a free, no-pressure estimate: {BOOKING} or {PHONE}. "
            f"What's the one job at home you keep putting off?")

def draft_instagram(service: str) -> str:
    s = SERVICES[service]
    return (f"{s['hook']} \nSimply Just Task - {s['label']} in Apopka & Central FL. "
            f"One call, one contact, one less thing to worry about. Free estimate: link in bio / {BOOKING} "
            f"#Apopka #CentralFlorida #SimplyJustTask")

def draft_x(service: str) -> str:
    s = SERVICES[service]
    txt = (f"{s['hook']} Simply Just Task helps Apopka neighbors with {s['label'].lower()} - "
           f"free estimate, no pressure: {BOOKING} {PHONE}")
    return txt[:280]

def draft_nextdoor(service: str) -> str:
    # Neighbor voice per SOPS/NEXTDOOR_KERNEL.md - short, personal, ends with a question
    s = SERVICES[service]
    return (f"Hi neighbors - I'm Anthony, I run Simply Just Task right here in Apopka. "
            f"We help neighbors with {s['label'].lower()} and the {s['pain']}. "
            f"Happy to take a look and give a straight starting range, no pressure. "
            f"{BOOKING} / {PHONE} - what's the timing you're hoping for?")

def produce_batch(service: str) -> dict:
    """One full free batch for one service. Draft-only. Owner go required to post."""
    drafts = {
        "facebook": draft_facebook(service),
        "instagram": draft_instagram(service),
        "x": draft_x(service),
        "nextdoor": draft_nextdoor(service),
    }
    checked = {}
    for ch, txt in drafts.items():
        issues = compliance_check(txt)
        checked[ch] = {"text": txt, "compliance_issues": issues, "ok": not issues}
    return {"service": service, "label": SERVICES[service]["label"], "drafts": checked,
            "image_idea": f"Real phone photo of a finished {SERVICES[service]['label']} job (owner-supplied). Fallback: text-only post. Never fake before/after.",
            "status": "DRAFT-ONLY - owner `go post <channel>` required. $0 spend."}

if __name__ == "__main__":
    import json, sys
    svc = sys.argv[1] if len(sys.argv) > 1 else "handyman"
    print(json.dumps(produce_batch(svc), indent=2))
