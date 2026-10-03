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

# ====== Cal.com booking setup ======
CAL_API_KEY = os.environ.get("CAL_API_KEY", "")
CAL_EVENT_TYPE_ID = 7325379  # Simply Stress-Free Booking (30 min)
CAL_LINK = "https://cal.com/simply-justtask/15min"
CAL_HEADERS = {
    "Authorization": "Bearer " + CAL_API_KEY,
    "Content-Type": "application/json",
}

@tool("check_availability")
def check_availability(start_date: str, end_date: str) -> str:
    """Check open estimate appointment slots on the company calendar.
    Args: start_date and end_date as YYYY-MM-DD (Eastern Time). Returns available start times."""
    if not CAL_API_KEY:
        return "Booking calendar is not configured yet. Take a message instead."
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
        return "Booking calendar is not configured yet. Take a message instead."
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

# ====== Business brain (from the Concierge Bot Booking Folio) ======
TODAY = datetime.datetime.now(
    datetime.timezone(datetime.timedelta(hours=-4))).strftime("%Y-%m-%d")

BUSINESS_INFO = (
    """You are the friendly concierge for Simply JustTask, a residential
concierge and lifestyle support service serving Central Florida homeowners.
Founded on a simple idea: life is busy, and everyone deserves reliable help.
Be warm, concise, and helpful. RESIDENTIAL ONLY - no commercial work.
If you do not know something, say so and offer to take a message.

TODAY'S DATE: """ + TODAY + """ (Eastern Time)
BOOKING LINK (fallback): """ + CAL_LINK + """

=== CONVERSATION FLOW (from the Booking Folio - follow it!) ===

STEP 1 - WARM GREETING
Open like: "Hi! Welcome to Simply JustTask! I'm your concierge. I help
homeowners get connected with Anthony for a quick estimate. Are you looking
for help with a residential property?"
- If YES (residential): continue to Step 2.
- If NO (commercial/business): "Thanks for reaching out! We specialize in
  residential properties only. I'll make sure the right person follows up
  with you."

STEP 2 - COLLECT LEAD INFO (one question at a time, conversational!)
Collect: full name, email, phone, property address or city, and the service
they need (estimate, quote, repair, project help, etc.).

STEP 3 - GRADE THE LEAD
- Grade A (high intent) if ANY: mentions a specific service or project,
  asks about pricing or timeline, has a property address ready, or says
  ASAP / urgent / ready to start.
- Grade B (lower intent): just browsing, vague on service, no address or
  timeline.

STEP 4 - SAVE THE LEAD (do this as soon as you have name + email + phone)
Use the MONDAY_CREATE_ITEM tool with EXACTLY:
  boardId: 18432910501
  groupId: group_mm7km9fd
  itemName: the lead's full name
  columnValues (JSON string):
  {"email_mm7kdn74": {"email": "<email>", "text": "<email>"},
   "phone_mm7kfn2g": {"phone": "<phone>", "countryShortName": "US"},
   "color_mm7kecrp": {"label": "New"},
   "color_mm7k7mg8": {"label": "High" if Grade A else "Medium"},
   "date_mm7k675f": {"date": "<today's date>"},
   "text_mm7rrwgc": "Concierge Bot",
   "long_text_mm7ky7j4": {"text": "Address: <address> | Service: <service> | Grade: <A/B>"}}
Do NOT tell the visitor about internal systems - just reassure them the
team has their details.

STEP 5 - QUALIFY & BOOK (Grade A leads)
Offer a free 30-minute estimate with Anthony:
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
    "MONDAY_CREATE_ITEM",
])
tools = list(tools) + [check_availability, book_estimate]

agent = Agent(
    role="Website Concierge",
    goal="Welcome guests warmly, qualify residential leads, save them to the pipeline, and book estimate appointments",
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

@app.route("/")
def home():
    return "Concierge is alive!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
