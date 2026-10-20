import os, time, json, datetime
# Keys come from environment variables (set on Render) - safe!

import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool
import crewai.llm as _crew_llm_mod
from composio import Composio
from composio_crewai import CrewAIProvider

# ====== FIX: strip 'cache_breakpoint' markers that Groq rejects ======
_orig_fmt = _crew_llm_mod.LLM._format_messages_for_provider

def _fmt_no_cache_breakpoint(self, messages):
    if messages:
        messages = [
            {k: v for k, v in m.items() if k != "cache_breakpoint"}
            for m in messages
        ]
    return _orig_fmt(self, messages)

_crew_llm_mod.LLM._format_messages_for_provider = _fmt_no_cache_breakpoint

# ====== Config ======
CAL_API_KEY = os.environ.get("CAL_API_KEY", "")
CAL_EVENT_TYPE_ID = 7325379  # Simply Stress-Free Booking (30 min)
CAL_LINK = "https://cal.com/simply-justtask/simplybook"
COMPOSIO_USER_ID = os.environ.get("COMPOSIO_USER_ID", "default")
REPORT_EMAIL = os.environ.get("REPORT_EMAIL", "tasksupport@simplyjusttask.com")
REPORT_CC = os.environ.get("REPORT_CC", "a.quinones@simplyjusttask.com")
ZOHO_MAIL_ACCOUNT_ID = os.environ.get("ZOHO_MAIL_ACCOUNT_ID", "8048488000000008002")  # tasksupport mailbox
ZOHO_FROM = os.environ.get("ZOHO_FROM_ADDRESS", "tasksupport@simplyjusttask.com")
CAL_HEADERS = {
    "Authorization": "Bearer " + CAL_API_KEY,
    "Content-Type": "application/json",
}

composio = Composio(provider=CrewAIProvider())

def zoho_exec(slug, args):
    """Execute a Composio tool directly (Zoho CRM / Zoho Mail)."""
    try:
        return composio.tools.execute(slug=slug, arguments=args, user_id=COMPOSIO_USER_ID,
                                      dangerously_skip_version_check=True)
    except TypeError:
        try:
            return composio.tools.execute(slug, args, COMPOSIO_USER_ID)
        except Exception as e:
            return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}

def zoho_ok(resp):
    return isinstance(resp, dict) and not resp.get("error") and resp.get("successful", True)

@tool("save_lead")
def save_lead(full_name: str, email: str, phone: str, address: str,
              service_needed: str, grade: str) -> str:
    """Save a new lead to the Zoho CRM Leads module.
    Args: full_name, email, phone, property address/city, service_needed,
    grade = 'A' (high intent) or 'B' (browsing)."""
    parts = full_name.strip().split()
    first, last = parts[0], (parts[-1] if len(parts) > 1 else parts[0])
    # Dedupe by email
    try:
        existing = zoho_exec("ZOHO_SEARCH_ZOHO_RECORDS",
                             {"module_api_name": "Leads", "email": email,
                              "fields": "id,Full_Name,Email", "per_page": 1})
        data = (existing.get("data") or {}).get("data") if isinstance(existing, dict) else None
        if data:
            return "SUCCESS: lead already exists in CRM with id " + str(data[0].get("id"))
    except Exception:
        pass
    desc = ("Address: %s | Service: %s | Grade: %s | Source: Website Concierge" %
            (address, service_needed, grade.upper()))
    resp = zoho_exec("ZOHO_CREATE_ZOHO_RECORD", {
        "module_api_name": "Leads",
        "data": [{
            "First_Name": first, "Last_Name": last,
            "Email": email, "Phone": phone,
            "Company": address or "Residential",
            "City": address,
            "Description": desc,
            "Lead_Source": "Chat",
            "Lead_Status": "Not Contacted",
        }],
    })
    try:
        recs = (resp.get("data") or {}).get("data") or []
        if recs and recs[0].get("code") == "SUCCESS":
            return "SUCCESS: lead saved to Zoho CRM with id " + str(recs[0]["details"]["id"])
        return "ERROR: lead save failed: " + json.dumps(resp)[:300]
    except Exception:
        return "ERROR: lead save failed: " + json.dumps(resp)[:300]

@tool("lookup_lead")
def lookup_lead(email_or_phone: str) -> str:
    """Look up a returning customer in Zoho CRM by email or phone to remember past
    interactions, notes, and AI qualification. Use when a guest gives contact info."""
    for key in ({"email": email_or_phone}, {"phone": email_or_phone}):
        try:
            args = {"module_api_name": "Leads",
                    "fields": "Full_Name,Email,Phone,City,Lead_Status,Description"}
            args.update(key)
            r = zoho_exec("ZOHO_SEARCH_ZOHO_RECORDS", args)
            data = (r.get("data") or {}).get("data") if isinstance(r, dict) else None
            if data:
                d = data[0]
                return ("FOUND returning lead: %s | status %s | notes: %s" %
                        (d.get("Full_Name"), d.get("Lead_Status"),
                         (d.get("Description") or "")[:400]))
        except Exception:
            pass
    return "No existing record - brand new guest."

@tool("check_availability")
def check_availability(start_date: str, end_date: str) -> str:
    """Check open estimate appointment slots on the company calendar.
    Args: start_date and end_date as YYYY-MM-DD (Eastern Time). Returns available start times."""
    if not CAL_API_KEY:
        return "ERROR: booking calendar not configured. Share the booking link instead: " + CAL_LINK
    r = requests.get(
        "https://api.cal.com/v2/slots",
        headers={**CAL_HEADERS, "cal-api-version": "2024-09-04"},
        params={"eventTypeId": CAL_EVENT_TYPE_ID, "start": start_date,
                "end": end_date, "timeZone": "America/New_York"},
        timeout=30,
    )
    data = r.json().get("data", {})
    if not data:
        return "No open slots in that range. Suggest a different week."
    lines = []
    for day, slots in data.items():
        times = [s["start"][11:16] for s in slots][:8]
        lines.append(day + ": " + ", ".join(times))
    return "Available slots (Eastern Time):\n" + "\n".join(lines)

@tool("book_estimate")
def book_estimate(full_name: str, email: str, phone: str, address: str,
                  service_needed: str, start_iso: str) -> str:
    """Book an estimate appointment on the company calendar.
    Args: full_name, email, phone, property address/city, service_needed,
    and start_iso = the exact slot start time from check_availability
    (ISO 8601 with timezone offset)."""
    if not CAL_API_KEY:
        return "ERROR: booking calendar not configured. Share the booking link instead: " + CAL_LINK
    body = {
        "start": start_iso,
        "eventTypeId": CAL_EVENT_TYPE_ID,
        "attendee": {"name": full_name, "email": email,
                     "timeZone": "America/New_York", "language": "en"},
        "metadata": {"phone": phone, "address": address,
                     "service": service_needed, "source": "website concierge"},
    }
    r = requests.post("https://api.cal.com/v2/bookings",
                      headers={**CAL_HEADERS, "cal-api-version": "2024-08-13"},
                      json=body, timeout=30)
    d = r.json()
    if r.status_code in (200, 201) and d.get("status") == "success":
        # Frankenstein Part 2: booking writes back to Zoho as Appointment Set (owner added 2026-10-20).
        try:
            got = zoho_exec("ZOHO_SEARCH_ZOHO_RECORDS", {"module_api_name": "Leads", "email": email, "fields": "id,Full_Name,Email,Description", "per_page": 1})
            found = (got.get("data") or {}).get("data") if isinstance(got, dict) else None
            if found:
                zoho_exec("ZOHO_UPDATE_ZOHO_RECORD", {"module_api_name": "Leads", "data": [{"id": str(found[0]["id"]), "Lead_Status": "Appointment Set", "Description": ((found[0].get("Description") or "") + "\n[Cal booked %s] Appointment Set via Concierge book_estimate." % start_iso)[:2000]}]})
        except Exception:
            pass
        return ("BOOKED! Confirmation email sent to " + email +
                ". Booking details: " + json.dumps(d.get("data", {}))[:300])
    return "Booking failed: " + json.dumps(d)[:300]

# ====== Business brain ======
TODAY = datetime.datetime.now(
    datetime.timezone(datetime.timedelta(hours=-4))).strftime("%Y-%m-%d")

MASTER_KNOWLEDGE = """
=== SIMPLY JUST TASK - MASTER KNOWLEDGE BASE v1.0 ===
Tagline: Reliable Help for Everyday Life.
One Call. One Contact. One Less Thing To Worry About.
We are not in the task business. We are in the peace-of-mind business.

COMPANY INFO
Website: SimplyJustTask.com | Email: tasksupport@simplyjusttask.com
Customer Service: (888) 566-7570 | Office: (321) 236-5574
Address: 2246 E Semoran Blvd, Suite 2082, Apopka, FL 32703

COMPANY STORY
Simply Just Task began in 2024 helping neighbors and community members with
errands, deliveries, projects, and everyday needs. Built on kindness and
family values; legally established in late 2025. Name inspired by the phrase
'Why don't you just ask.'

LEADERSHIP
Anthony Quinones - CEO & President, Customer Service & Client Relations
Michael Sabo - VP & Head of Operations, Dream Makers Landscape Design Division
Gary Greenawalt - CFO, Billing, Finance, Invoicing, Job & Task Assignment
Derrick McAlister - Head of Engineering & Small Engine Division

SERVICES
Concierge Services, Handyman Services, Cleaning Services, Landscape Design,
Property Services, Small Engine Services, Business Support, Administrative
Services, Appointment Scheduling, Project Coordination, AI & Technology Services.

HOURS
Mon-Fri 9:00 AM-5:00 PM ET | Sat-Sun 11:00 AM-4:00 PM ET

SOCIAL MEDIA
Facebook: Simply Just Task | Instagram: @simply_just_task | YouTube: Simply Just Task

=== PRICING RULES ===
Golden Rule 1: Always try to give a flat-rate project quote first. Customers
prefer knowing the final cost. Preferred: fixed price. Secondary: hourly.
Large projects: custom proposal.
Golden Rule 2: If scope is unclear, collect info BEFORE quoting. Ask: what
service, address, timeline, materials included, project size, photos.
Golden Rule 3: Never underprice. Travel time, fuel, experience, insurance,
and customer service all have value.

PRICING GUIDELINES (ESTIMATES ONLY - ranges, never guarantees):
CLEANING: apartment/small home $100-150 | standard house (3 bed/2 bath) $140-200 |
  deep clean $220-380 | move-in/move-out $250-450 | Airbnb turnover $100-160 |
  commercial: custom proposal (collect sqft, frequency, building type first)
HANDYMAN: TV mounting $90-180 | furniture assembly $80-250 | general repairs
  $75-120/hr | drywall/patching $100-250 | ceiling fan $125-300 | door repair
  $100-350 | half-day multi-job $250-400 | large projects: custom proposal
LAWN & LANDSCAPE: mow + edge (standard lot) $45-75/visit | full yard cleanup
  $150-350 | mulching/trimming $120-300 | consult $75-150 | design $250-1,500+
PRESSURE WASHING: driveway $100-200 | house exterior $200-400
ERRAND RUNNING: grocery run + delivery $35-55 plus store receipt | pickups and
  drop-offs $25-40 | multi-stop errand hour $35-50/hr
CONCIERGE/ADMIN: coordination from $75/project or $50-75/hr
SMALL ENGINE: diagnostic $50-100 | tune-up $100-250 | repair: quote after inspection
AI/TECH: website help $150-500 | website dev $750-5,000+ | AI setup from $250

FLEXIBLE PRICING PROMISE (use this wording):
Our pricing is FLEXIBLE and NEGOTIABLE. After giving a range, ALWAYS add warmly:
"These are honest estimates - our pricing is flexible and we work with your
budget. Your free in-person estimate is where we lock in a number that works
for you. No pressure, no hidden fees." We promise to be CLOSE to the estimate
but never guarantee exact pricing. Use every price question as a reason to book
the FREE estimate - never argue about price, always pivot to booking. If pushed
for a firm number, say a team member will work it out personally at the visit.

TRAVEL FEES: within 15 miles of Apopka: free | 15-30 miles: $20 | beyond 30: custom quote
EMERGENCY: same-day +25% | after-hours +50% | holidays: custom quote

DISCOUNTS: may offer MANAGEMENT REVIEW for seniors, veterans, first responders,
nonprofits, repeat customers. Discounts are never automatically guaranteed.

REVENUE PROTECTION: NEVER give a firm quote when materials unknown, photos
unavailable, scope unclear, multiple trades involved, or requirements change.
Instead say: 'Based on the information provided, we'd recommend a consultation
so we can provide an accurate fixed-price quote.'
When uncertain, say: 'Every project is unique, and Simply Just Task prefers
transparent flat-rate pricing whenever possible. I'd be happy to gather a few
details and connect you with our team for a customized quote.'

=== PAYMENTS ===
Accepted: Cash, Check, Credit Cards, Debit Cards, Zelle, Cash App, Venmo,
PayPal, Business Checks, Electronic Invoices, Bank Transfers (when applicable).
Terms vary by service type, project size, materials, vendors, contract,
timeline. Some projects require deposit, progress payments, materials upfront,
or final payment on completion.

PRICING DISCLAIMER: pricing examples are general guidelines; final pricing may
vary with scope, location, materials, labor, duration, travel, accessibility,
urgency, vendor costs. Never guarantee final pricing without full scope.

QUOTE AUTHORITY:
You MAY: provide ranges, starting rates, explain pricing philosophy, gather info.
You MAY NOT: approve discounts, guarantee final prices, modify contracts, override policies.
MANAGEMENT APPROVAL REQUIRED for: discounts over 10%, projects over $1,000,
commercial contracts, recurring contracts, payment arrangements, special pricing.

COMPANY POLICY: fair, honest, transparent pricing; exceptional value; reliable
service; long-term relationships, not one-time transactions.
"""

BUSINESS_INFO = (
    """You are the friendly concierge for Simply Just Task, serving Central Florida
homeowners. Be warm, concise, human, and helpful. RESIDENTIAL focus; for
commercial requests, say we specialize in residential and a team member will
follow up. If you do not know something, say so and offer to take a message.

TODAY'S DATE: """ + TODAY + """ (Eastern Time)
BOOKING LINK (fallback): """ + CAL_LINK + MASTER_KNOWLEDGE + """

=== CONVERSATION FLOW (from the Booking Folio - follow it!) ===

STEP 1 - WARM GREETING
Open like: "Hi! Welcome to Simply Just Task! I'm your concierge. I help
homeowners get connected with Anthony for a quick estimate. Are you looking
for help with a residential property?"

STEP 2 - COLLECT LEAD INFO (one question at a time, conversational!)
Collect: full name, email, phone, property address or city, and the service
they need.

STEP 3 - GRADE THE LEAD
- Grade A (high intent) if ANY: mentions a specific service or project,
  asks about pricing or timeline, has a property address ready, or says
  ASAP / urgent / ready to start.
- Grade B (lower intent): just browsing, vague on service, no address or
  timeline.

STEP 4 - SAVE THE LEAD (as soon as you have name + email + phone)
Call the save_lead tool with the collected info and the grade.
IMPORTANT: only tell the guest their info was captured if the tool returns
SUCCESS. If it returns ERROR, say a team member will follow up instead.
Do NOT mention internal systems to the visitor.

STEP 5 - QUALIFY & BOOK (Grade A leads)
Offer a free estimate with Anthony:
1. Ask their preferred day.
2. Use check_availability for that week, offer 2-3 open times.
3. Use book_estimate with their chosen slot.
4. Confirm warmly: date, time, and that a confirmation email is on the way.
If booking fails or they prefer it: share the booking link """ + CAL_LINK + """

GRADE B leads: thank them, save the lead, and promise a friendly follow-up.

=== HOW TO THINK (partner-level reasoning) ===
You are Anthony's business partner, not a script. Before every reply, silently reason:
1) What does this person ACTUALLY need (the real job behind their words)?
2) What do I already know? If they gave an email or phone earlier, use lookup_lead
   to remember them and reference it naturally (welcome back!).
3) What is the single best next step toward a booked free estimate?
Then speak like a smart, caring human: warm, confident, concise, never robotic.
Remember details they mention within the conversation and use them later.
If you learn something new about the customer, include it when you save_lead
so the CRM gets smarter over time.
"""
)

llm = LLM(model="groq/openai/gpt-oss-120b")
tools = [save_lead, check_availability, book_estimate, lookup_lead]

agent = Agent(
    role="Website Concierge",
    goal="Welcome guests warmly, answer questions using the master knowledge base, qualify residential leads, save them to the pipeline, and book estimate appointments",
    backstory=BUSINESS_INFO,
    tools=tools,
    llm=llm,
    verbose=True,
)

app = Flask(__name__)
CORS(app)

@app.route("/api/chat", methods=["POST"])
def chat():
    message = request.json.get("message", "").strip()
    history = request.json.get("history", [])[-12:]
    if not message:
        return jsonify({"reply": "Please type a message! :)"})

    def _autosave():
        try:
            resp = llm.call([
                {"role": "system", "content": "Extract lead info from the message. Reply with ONLY a JSON object with keys: full_name, email, phone, address, service_needed, grade ('A' if ready to start/urgent/specific, else 'B'). Use empty string for anything missing. No markdown."},
                {"role": "user", "content": message},
            ])
            txt = str(resp).strip()
            if txt.startswith("```"):
                txt = txt.strip("`").replace("json", "", 1).strip()
            info = json.loads(txt)
            if info.get("full_name") and info.get("email") and info.get("phone"):
                print("AUTO-SAVE:", save_lead(
                    info["full_name"], info["email"], info["phone"],
                    info.get("address", ""), info.get("service_needed", ""),
                    info.get("grade", "B")))
        except Exception as ex:
            print("auto-extract skipped:", ex)

    threading.Thread(target=_autosave, daemon=True).start()

    convo = ""
    if history:
        convo = "Conversation so far:\n" + "\n".join(
            ("Guest: " if m.get("role") == "user" else "You: ") + str(m.get("content", ""))
            for m in history) + "\n\n"
    task = Task(description=convo + "A website guest asks: " + message,
                expected_output="A short, friendly, helpful reply (2-4 sentences)",
                agent=agent)
    for attempt in range(4):
        try:
            result = Crew(agents=[agent], tasks=[task]).kickoff()
            return jsonify({"reply": str(result)})
        except Exception as e:
            if "rate_limit" in str(e).lower():
                time.sleep(45)
            else:
                return jsonify({"reply": "DEBUG: " + str(e)[:400]})

@app.route("/debug")
def debug():
    return jsonify({
        "crm": "zoho",
        "cal_key_loaded": bool(CAL_API_KEY),
    })

@app.route("/")
def home():
    return "Concierge is alive!"


# ================= DAILY LEAD PIPELINE (9am crew) =================
import threading

QUALIFY_PROMPT = """You are the lead qualification crew for Simply Just Task, a Central Florida
residential services company (cleaning, handyman, lawn/landscape, pressure washing,
errands, concierge, small engine, AI/tech). Score this lead and reply with ONLY JSON:
{"status": one of "Pre-Qualified", "Not Qualified", "Junk Lead", "Recycled",
 "score": 0-100, "notes": "2-3 sentence AI note on intent, fit, and suggested next step"}
Rules: Pre-Qualified = real person, residential service fit, reachable contact info,
some buying intent. Not Qualified = out of area/commercial/vague. Junk = spam/test/gibberish."""

OUTREACH_DAILY_CAP = int(os.environ.get("OUTREACH_DAILY_CAP", "10"))

OUTREACH_PROMPT = """You are the outreach crew for Simply Just Task. Write a short, warm,
plain-text follow-up email (under 120 words) from Anthony at Simply Just Task to this lead.
Mention their service need, offer a FREE no-pressure estimate, include this booking link:
""" + CAL_LINK + """ and phone (888) 566-7570. Sign off as 'Anthony & the Simply Just Task Team'.
Reply with ONLY JSON: {"subject": "...", "body": "..."}"""

def _llm_json(system, user):
    resp = llm.call([{"role": "system", "content": system},
                     {"role": "user", "content": user}])
    txt = str(resp).strip()
    if txt.startswith("```"):
        txt = txt.strip("`")
        if txt.lower().startswith("json"):
            txt = txt[4:]
    return json.loads(txt.strip())

def run_daily_pipeline():
    report = {"date": datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=-4))).strftime("%Y-%m-%d %H:%M ET"),
        "leads": [], "outreach": [], "errors": []}
    try:
        resp = zoho_exec("ZOHO_GET_ZOHO_RECORDS", {
            "module_api_name": "Leads",
            "fields": "First_Name,Last_Name,Email,Phone,City,Description,Lead_Status,Lead_Source,Created_Time",
            "sort_by": "Created_Time", "sort_order": "desc", "per_page": 50})
        print("RAW ZOHO FETCH:", json.dumps(resp, default=str)[:800])
        leads = (resp.get("data") or {}).get("data") or []
    except Exception as e:
        leads = []
        report["errors"].append("fetch leads failed: " + str(e)[:200])
    for ld in leads:
        status = ld.get("Lead_Status")
        name = (ld.get("Full_Name") or ((ld.get("First_Name") or "") + " " + (ld.get("Last_Name") or ""))).strip()
        entry = {"id": ld.get("id"), "name": name, "email": ld.get("Email"),
                 "phone": ld.get("Phone"), "city": ld.get("City"),
                 "source": ld.get("Lead_Source"), "old_status": status}
        try:
            if status in ("Not Contacted", None, "-None-"):
                q = _llm_json(QUALIFY_PROMPT, json.dumps(ld, default=str)[:2000])
                entry["ai_score"] = q.get("score")
                entry["ai_notes"] = q.get("notes")
                raw_status = q.get("status", "Not Qualified")
                # Frankenstein Part 2 recycle pool (owner rule, 2026-10-20): Not Qualified / Recycled = keep, do not drop.
                # Owner added Zoho Lead_Status values Appointment Set + Recycled and Lead_Source values CrewAI/Nextdoor/Instagram/TikTok/YouTube/LinkedIn.
                # Junk Lead is the only true drop.
                new_status = "Recycled" if raw_status in ("Not Qualified", "Recycled") else raw_status
                entry["new_status"] = new_status
                recycled_note = ""
                if new_status == "Recycled":
                    recycled_note = " | Recycle follow-up: +30 days, never delete."
                note = "\n\n[AI Qualifier %s] Score %s/100. %s%s" % (
                    report["date"], q.get("score"), q.get("notes"), recycled_note)
                zoho_exec("ZOHO_UPDATE_ZOHO_RECORD", {
                    "module_api_name": "Leads",
                    "data": [{"id": str(ld["id"]), "Lead_Status": new_status,
                              "Description": ((ld.get("Description") or "") + note)[:2000]}]})
                if (new_status == "Pre-Qualified" and ld.get("Email")
                        and len(report["outreach"]) >= OUTREACH_DAILY_CAP):
                    entry["ai_notes"] = (entry.get("ai_notes") or "") + " | Outreach QUEUED for tomorrow (daily cap)"
                elif new_status == "Pre-Qualified" and ld.get("Email"):
                    try:
                        m = _llm_json(OUTREACH_PROMPT, json.dumps(ld, default=str)[:1500])
                        send = zoho_exec("ZOHO_MAIL_MESSAGES_SEND_EMAIL", {
                            "accountId": ZOHO_MAIL_ACCOUNT_ID,
                            "fromAddress": ZOHO_FROM,
                            "toAddress": ld["Email"],
                            "subject": m.get("subject", "Your free estimate from Simply Just Task"),
                            "content": m.get("body", ""), "mailFormat": "plaintext"})
                        zoho_exec("ZOHO_UPDATE_ZOHO_RECORD", {
                            "module_api_name": "Leads",
                            "data": [{"id": str(ld["id"]), "Lead_Status": "Attempted to Contact"}]})
                        entry["new_status"] = "Attempted to Contact"
                        entry["outreach_sent"] = zoho_ok(send)
                        report["outreach"].append({"to": ld["Email"], "name": name,
                            "subject": m.get("subject"), "body": m.get("body"),
                            "sent": zoho_ok(send)})
                    except Exception as e:
                        report["errors"].append("outreach %s: %s" % (name, str(e)[:200]))
            else:
                entry["new_status"] = status
                entry["ai_notes"] = "Skipped - already " + str(status)
        except Exception as e:
            report["errors"].append("qualify %s: %s" % (name, str(e)[:200]))
        report["leads"].append(entry)
    # Build + send report email
    lines = ["DAILY LEAD PIPELINE REPORT - " + report["date"], "",
             "Leads reviewed: %d | Outreach sent: %d | Errors: %d" % (
                 len(report["leads"]),
                 sum(1 for o in report["outreach"] if o.get("sent")),
                 len(report["errors"])), "", "=== LEADS ==="]
    for e in report["leads"]:
        lines.append("- %s | %s | %s | %s" % (e.get("name"), e.get("email"),
                                              e.get("phone"), e.get("city")))
        lines.append("  source: %s | status: %s -> %s | score: %s" % (
            e.get("source"), e.get("old_status"), e.get("new_status"), e.get("ai_score", "-")))
        lines.append("  AI notes: %s" % (e.get("ai_notes") or "-"))
    lines += ["", "=== OUTREACH COPIES ==="]
    for o in report["outreach"]:
        lines.append("TO: %s (%s) | sent=%s" % (o.get("to"), o.get("name"), o.get("sent")))
        lines.append("SUBJECT: " + str(o.get("subject")))
        lines.append(str(o.get("body")))
        lines.append("---")
    if report["errors"]:
        lines += ["", "=== ERRORS ==="] + report["errors"]
    body = "\n".join(lines)
    try:
        zoho_exec("ZOHO_MAIL_MESSAGES_SEND_EMAIL", {
            "accountId": ZOHO_MAIL_ACCOUNT_ID, "fromAddress": ZOHO_FROM,
            "toAddress": REPORT_EMAIL, "ccAddress": REPORT_CC,
            "subject": "SJT Lead Machine Report - " + report["date"],
            "content": body, "mailFormat": "plaintext"})
    except Exception as e:
        print("report email failed:", e)
    print(body)


# ================= SOCIAL MEDIA CREW =================
SOCIAL_PLATFORMS = ["facebook", "instagram", "twitter"]  # twitter re-added 2026-10-19: @simplyjusttask connected in Composio

def run_social_pipeline():
    rep = {"date": datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=-4))).strftime("%Y-%m-%d %H:%M ET"),
        "actions": [], "errors": []}
    social_tools = []
    for tk in SOCIAL_PLATFORMS:
        try:
            t = composio.tools.get(user_id=COMPOSIO_USER_ID, toolkits=[tk])
            t = list(t)
            rep["actions"].append("%s: %d tools loaded" % (tk, len(t)))
            social_tools += t
        except Exception as e:
            rep["errors"].append("%s toolkit: %s" % (tk, str(e)[:150]))
    if not social_tools:
        rep["errors"].append("No social platforms connected in Composio for user " + COMPOSIO_USER_ID)
    else:
        social_agent = Agent(
            role="Social Media Manager",
            goal=("Run Simply Just Task social media: make one friendly daily post per connected "
                  "platform about residential services in Central Florida, check and warmly reply "
                  "to any new messages/comments, and capture anyone interested as a lead."),
            backstory="You represent Simply Just Task. Tagline: Reliable Help for Everyday Life. "
                      "Residential focus, Central Florida. Warm, human, never pushy. "
                      "Booking link: " + CAL_LINK + MASTER_KNOWLEDGE[:1500],
            tools=social_tools + [save_lead], llm=llm, verbose=True)
        tasks = [
            Task(description="Create and publish one short daily post on each connected platform "
                             "(Facebook, Instagram, Twitter/X) promoting Simply Just Task residential "
                             "services. Skip any platform whose tools are unavailable.",
                 expected_output="List of posts published with platform + post text", agent=social_agent),
            Task(description="Check for new unread messages/comments on connected platforms. Reply "
                             "warmly and helpfully. If anyone shows buying intent, collect name, email, "
                             "phone, service needed and call save_lead (grade A).",
                 expected_output="List of replies sent and any leads saved", agent=social_agent),
        ]
        try:
            result = Crew(agents=[social_agent], tasks=tasks).kickoff()
            rep["actions"].append("crew result: " + str(result)[:1500])
        except Exception as e:
            rep["errors"].append("social crew: " + str(e)[:300])
    body = "SOCIAL MEDIA CREW REPORT - " + rep["date"] + "\n\n" + \
           "\n".join(rep["actions"]) + "\n\nERRORS:\n" + "\n".join(rep["errors"])
    try:
        zoho_exec("ZOHO_MAIL_MESSAGES_SEND_EMAIL", {
            "accountId": ZOHO_MAIL_ACCOUNT_ID, "fromAddress": ZOHO_FROM,
            "toAddress": REPORT_EMAIL, "ccAddress": REPORT_CC,
            "subject": "SJT Social Crew Report - " + rep["date"],
            "content": body, "mailFormat": "plaintext"})
    except Exception as e:
        print("social report email failed:", e)
    print(body)

# ================= CREWAI STUDIO -> ZOHO BRIDGE =================
# POST /ingest-crewai-leads  {leads:[...]}  or {result: "..."} or {output: "..."}
# CrewAI Studio hunter finishes -> scripts/daily_job.py sends its result here.
# Each lead is saved to Zoho CRM (dedupe by email, then phone) as
# Lead_Status=Not Contacted, Lead_Source=CrewAI (owner added CrewAI to Zoho Lead_Source 2026-10-20 convo, verified live),
# with "Source: CrewAI Studio Lead Automation-v1" in Description.
# Optional guard: set MACHINE_TOKEN on Render + GitHub; send x-machine-token header.
MACHINE_TOKEN = os.environ.get("MACHINE_TOKEN", "")

def _crewai_norm_lead(raw):
    if not isinstance(raw, dict):
        return None
    def g(*keys):
        for k in keys:
            v = raw.get(k)
            if v:
                return str(v).strip()
        return ""
    name = g("full_name", "name", "Full_Name", "Name")
    email = g("email", "Email")
    phone = g("phone", "Phone", "mobile", "Mobile")
    if not name and not email and not phone:
        return None
    return {
        "full_name": name or "CrewAI Lead",
        "email": email, "phone": phone,
        "address": g("address", "Address", "city", "City"),
        "service_needed": g("service_needed", "service", "Service_Needed", "notes", "Notes"),
        "grade": (g("grade", "Grade") or "B").upper()[:1],
        "score": g("score", "Score"),
    }

def _crewai_extract_leads(payload):
    leads = []
    if isinstance(payload, dict):
        for key in ("leads", "data", "results", "output_leads"):
            if isinstance(payload.get(key), list):
                for item in payload[key]:
                    n = _crewai_norm_lead(item)
                    if n: leads.append(n)
                if leads: return leads
        for key in ("result", "output", "raw", "text"):
            v = payload.get(key)
            if isinstance(v, str):
                leads = _crewai_extract_leads({"_text": v})
                if leads: return leads
            elif isinstance(v, (dict, list)):
                leads = _crewai_extract_leads(v)
                if leads: return leads
    text = ""
    if isinstance(payload, dict):
        text = str(payload.get("_text") or "")
    elif isinstance(payload, str):
        text = payload
    if text:
        try:
            parsed = json.loads(text)
            return _crewai_extract_leads(parsed if isinstance(parsed, (dict, list)) else {"_text": text})
        except Exception:
            pass
        # fallback: find JSON array/object chunks in prose
        import re
        for chunk in re.findall(r"\[.*?\]|\{.*?\}", text, flags=re.S):
            try:
                parsed = json.loads(chunk)
            except Exception:
                continue
            got = _crewai_extract_leads(parsed if isinstance(parsed, (dict, list)) else {"_text": chunk})
            if got: leads.extend(got)
    if isinstance(payload, list):
        for item in payload:
            n = _crewai_norm_lead(item)
            if n: leads.append(n)
    return leads

def _crewai_save_one(lead):
    first_parts = lead["full_name"].strip().split()
    first = first_parts[0] if first_parts else "CrewAI"
    last = first_parts[-1] if len(first_parts) > 1 else first
    # dedupe email
    if lead["email"]:
        try:
            ex = zoho_exec("ZOHO_SEARCH_ZOHO_RECORDS", {"module_api_name": "Leads", "email": lead["email"], "fields": "id,Full_Name,Email", "per_page": 1})
            data = (ex.get("data") or {}).get("data") if isinstance(ex, dict) else None
            if data:
                return "exists:" + str(data[0].get("id"))
        except Exception:
            pass
    # dedupe phone
    if lead["phone"]:
        try:
            ex = zoho_exec("ZOHO_SEARCH_ZOHO_RECORDS", {"module_api_name": "Leads", "phone": lead["phone"], "fields": "id,Full_Name,Phone", "per_page": 1})
            data = (ex.get("data") or {}).get("data") if isinstance(ex, dict) else None
            if data:
                return "exists:" + str(data[0].get("id"))
        except Exception:
            pass
    desc = ("Address: %s | Service: %s | Grade: %s | Score: %s | Source: CrewAI Studio Lead Automation-v1" % (lead["address"], lead["service_needed"], lead["grade"] or "B", lead["score"] or "-"))
    resp = zoho_exec("ZOHO_CREATE_ZOHO_RECORD", {"module_api_name": "Leads", "data": [{"First_Name": first, "Last_Name": last, "Email": lead["email"], "Phone": lead["phone"], "Company": lead["address"] or "Residential", "City": lead["address"], "Description": desc, "Lead_Source": "CrewAI", "Lead_Status": "Not Contacted"}]})
    try:
        recs = (resp.get("data") or {}).get("data") or []
        if recs and recs[0].get("code") == "SUCCESS":
            return "created:" + str(recs[0]["details"]["id"])
        return "error:" + json.dumps(resp)[:300]
    except Exception:
        return "error:" + json.dumps(resp)[:300]

@app.route("/ingest-crewai-leads", methods=["POST"])
def ingest_crewai_leads():
    if MACHINE_TOKEN and request.headers.get("x-machine-token") != MACHINE_TOKEN:
        return jsonify({"error": "unauthorized"}), 401
    payload = request.get_json(silent=True) or {}
    # also accept form/raw text
    if not payload and request.data:
        try:
            payload = json.loads(request.data.decode("utf-8", "ignore"))
        except Exception:
            payload = {"result": request.data.decode("utf-8", "ignore")}
    leads = _crewai_extract_leads(payload)
    results = []
    for lead in leads[:100]:
        results.append({"name": lead["full_name"], "email": lead["email"], "result": _crewai_save_one(lead)})
    created = sum(1 for r in results if r["result"].startswith("created:"))
    exists = sum(1 for r in results if r["result"].startswith("exists:"))
    errors = sum(1 for r in results if r["result"].startswith("error:"))
    return jsonify({"status": "ok", "received": len(leads), "created": created, "exists": exists, "errors": errors, "results": results}), 200


@app.route("/run-social", methods=["GET", "POST"])
def run_social():
    threading.Thread(target=run_social_pipeline, daemon=True).start()
    return jsonify({"status": "started",
                    "note": "social crew running; report will be emailed to " + REPORT_EMAIL}), 202

@app.route("/run-daily", methods=["GET", "POST"])
def run_daily():
    threading.Thread(target=run_daily_pipeline, daemon=True).start()
    return jsonify({"status": "started",
                    "note": "pipeline running; report will be emailed to " + REPORT_EMAIL}), 202

@app.route("/ping")
def ping():
    return jsonify({"alive": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
