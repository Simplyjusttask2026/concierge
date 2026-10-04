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
MONDAY_API_TOKEN = os.environ.get("MONDAY_API_TOKEN", "")
CAL_EVENT_TYPE_ID = 7325379  # Simply Stress-Free Booking (30 min)
CAL_LINK = "https://cal.com/simply-justtask/15min"
MONDAY_BOARD_ID = 18432910501
MONDAY_GROUP_ID = "group_mm7km9fd"  # Incoming Leads (New)
CAL_HEADERS = {
    "Authorization": "Bearer " + CAL_API_KEY,
    "Content-Type": "application/json",
}

@tool("save_lead")
def save_lead(full_name: str, email: str, phone: str, address: str,
              service_needed: str, grade: str) -> str:
    """Save a new lead to the monday.com pipeline board (Incoming Leads (New) group).
    Args: full_name, email, phone, property address/city, service_needed,
    grade = 'A' (high intent) or 'B' (browsing)."""
    if not MONDAY_API_TOKEN:
        return "ERROR: monday token not configured. Tell the guest you will take a message and a human will follow up."
    today = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=-4))).strftime("%Y-%m-%d")
    column_values = {
        "email_mm7kdn74": {"email": email, "text": email},
        "phone_mm7kfn2g": {"phone": phone, "countryShortName": "US"},
        "color_mm7kecrp": {"label": "New"},
        "color_mm7k7mg8": {"label": "High" if grade.upper() == "A" else "Medium"},
        "date_mm7k675f": {"date": today},
        "text_mm7rrwgc": "Concierge Bot",
        "long_text_mm7ky7j4": {"text": "Address: %s | Service: %s | Grade: %s"
                               % (address, service_needed, grade.upper())},
    }
    query = ("mutation ($board: ID!, $group: String!, $name: String!, $cols: JSON!) {"
             " create_item(board_id: $board, group_id: $group, item_name: $name,"
             " column_values: $cols) { id } }")
    r = requests.post(
        "https://api.monday.com/v2",
        headers={"Authorization": MONDAY_API_TOKEN, "Content-Type": "application/json"},
        json={"query": query, "variables": {
            "board": str(MONDAY_BOARD_ID),
            "group": MONDAY_GROUP_ID,
            "name": full_name,
            "cols": json.dumps(column_values),
        }},
        timeout=30,
    )
    try:
        d = r.json()
    except Exception:
        return "ERROR: lead save failed (HTTP %s). Tell the guest a human will follow up." % r.status_code
    if d.get("data", {}).get("create_item", {}).get("id"):
        return "SUCCESS: lead saved to the pipeline board with id " + str(d["data"]["create_item"]["id"])
    return "ERROR: lead save failed: " + json.dumps(d)[:300]

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
"""
)

llm = LLM(model="groq/openai/gpt-oss-120b")
composio = Composio(provider=CrewAIProvider())
tools = composio.tools.get(user_id="default", tools=[
    "MONDAY_LIST_BOARDS",
    "MONDAY_LIST_BOARD_ITEMS",
    "MONDAY_LIST_ITEMS",
])
tools = list(tools) + [save_lead, check_availability, book_estimate]

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
    if not message:
        return jsonify({"reply": "Please type a message! :)"})
    task = Task(description="A website guest asks: " + message,
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
        "monday_token_loaded": bool(MONDAY_API_TOKEN),
        "cal_key_loaded": bool(CAL_API_KEY),
    })

@app.route("/")
def home():
    return "Concierge is alive!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
