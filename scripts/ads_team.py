"""
ADS TEAM - draft production helpers (Simply Just Task)
Owner rule: ALL FREE - $0. Owner update 2026-10-19: DO NOT use Cal link in ads.
Use Anthony cell (352) 849-2344 and Michael Sabo (321) 745-5894.
Draft-only, no post function. Images: real website photos or text-only, never fake before/after as our work.
"""
PHONE_ANTHONY = "(352) 849-2344"
PHONE_MICHAEL = "(321) 745-5894"
CONTACT_LINE = f"Call/text Anthony {PHONE_ANTHONY} or Michael Sabo {PHONE_MICHAEL}"
CONTACT_SHORT = f"Call/text {PHONE_ANTHONY} or {PHONE_MICHAEL}"
TAGLINE = "Reliable Help for Everyday Life."
SERVICES = {
    "handyman": {"label": "Handyman & Home Repairs", "pain": "fix-it lists that keep growing", "hook": "That fix-it list isn't getting shorter."},
    "cleaning": {"label": "House Cleaning", "pain": "guests are coming and the house is not ready", "hook": "Company coming? House not ready?"},
    "lawn": {"label": "Lawn & Yard Care", "pain": "an overgrown yard or a code violation letter", "hook": "Yard getting away from you?"},
    "pressure": {"label": "Pressure Washing", "pain": "a dirty driveway and siding", "hook": "Your driveway called - it wants its color back."},
    "errands": {"label": "Errands & Concierge", "pain": "too many stops and not enough day", "hook": "Too many stops, not enough day?"},
    "senior": {"label": "Senior & Family Help", "pain": "mom or dad needs a hand around the house", "hook": "Could Mom or Dad use an extra hand at home?"},
}
BANNED = ["guaranteed price", "guarantee you", "exact price", "% off", "discount", "calendly", "cal.com", "simplybook", "we don't do that", "commercial", "office cleaning"]
def compliance_check(text):
    t = (text or "").lower()
    issues = [b for b in BANNED if b in t]
    if PHONE_ANTHONY not in text:
        issues.append("missing Anthony phone")
    if PHONE_MICHAEL not in text:
        issues.append("missing Michael phone")
    return issues
def draft_facebook(service):
    s = SERVICES[service]
    return f"{s['hook']} I'm Anthony with Simply Just Task here in Apopka - we help busy families, homeowners, and seniors with {s['label'].lower()} and the everyday jobs that pile up. {TAGLINE} Free, no-pressure estimate - {CONTACT_LINE}. What's the one job at home you keep putting off?"
def draft_instagram(service):
    s = SERVICES[service]
    return f"{s['hook']} Simply Just Task - {s['label']} in Apopka & Central FL. One call, one contact, one less thing to worry about. Free estimate - {CONTACT_SHORT} #Apopka #CentralFlorida #SimplyJustTask"
def draft_x(service):
    s = SERVICES[service]
    return f"{s['hook']} Simply Just Task helps Apopka neighbors with {s['label'].lower()} - free estimate, no pressure: {CONTACT_SHORT}"[:280]
def draft_nextdoor(service):
    s = SERVICES[service]
    return f"Hi neighbors - I'm Anthony, I run Simply Just Task right here in Apopka. We help neighbors with {s['label'].lower()}, especially when it's {s['pain']}. Happy to take a look and give a straight starting range, no pressure. {CONTACT_LINE} - what's the timing you're hoping for?"
def produce_batch(service):
    drafts = {"facebook": draft_facebook(service), "instagram": draft_instagram(service), "x": draft_x(service), "nextdoor": draft_nextdoor(service)}
    checked = {}
    for ch, txt in drafts.items():
        issues = compliance_check(txt)
        checked[ch] = {"text": txt, "compliance_issues": issues, "ok": not issues}
    return {"service": service, "label": SERVICES[service]["label"], "drafts": checked, "image_idea": "Use a REAL photo already on simplyjusttask.com, or text-only. Never fake a before/after.", "contact": CONTACT_LINE, "status": "DRAFT-ONLY - owner final go required. $0. No Cal link in ads."}
if __name__ == "__main__":
    import json, sys
    svc = sys.argv[1] if len(sys.argv) > 1 else "handyman"
    print(json.dumps(produce_batch(svc), indent=2))
