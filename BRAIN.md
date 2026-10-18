# 🧠 SIMPLY JUST TASK — BRAIN FILE
> Read this at the start of every new conversation. It contains everything the assistant needs to know. Update it before ending a conversation ("update my brain file").

## BUSINESS
- **Name:** Simply Just Task
- **Owner:** Anthony Quinones-Savino (tasksupport@simplyjusttask.com)
- **Website:** www.simplyjusttask.com (Squarespace)
- **What:** Errands, home tasks, concierge, lifestyle support
- **Market:** Central Florida (Apopka + surrounding)
- **Target leads:** RESIDENTIAL ONLY (busy families, homeowners, seniors) — NO commercial/businesses
- **Tagline:** "Reliable Help for Everyday Life. One Call. One Contact. One Less Thing To Worry About." — "We are in the peace-of-mind business."

## SYSTEMS & KEY IDs
- **CRM:** ZOHO CRM (free tier) — REPLACED Monday.com (cost). Zoho also handles Mail + Voice. DO NOT switch again.
- **Lead hunter:** CrewAI crew "Simply Just Task Lead Automation-v1" — crew_uuid: d5813278-f085-4cc0-b1c6-d4a388e0bc47
- **AI Concierge chatbot:** Render service "sjt-concierge" (srv-dau0mf8u01pc73aqe3cg), auto-deploys from GitHub repo Simplyjusttask2026/concierge (main branch). Status: LIVE (turquoise widget).
- **CrewAI connection note:** only ONE active connection: crew_ai_codify-axel (old one removed)

## BOOKING — CAL.COM (⚠️ NOT CALENDLY — user switched specifically so the Concierge can book ITSELF. Never mention Calendly again.)
- **Account:** Simply Just Task / simply-justtask — America/New_York
- **Event:** "Simply Stress-Free Booking" — ID 7325379, slug: simplybook
- **Link:** cal.com/simply-justtask/simplybook
- **Durations:** 30 min default (30/45/60/120 available), 2-hour minimum notice
- **requiresConfirmation: false** → Concierge can finalize bookings INSTANTLY, no human approval
- Concierge can: check slots, reserve, book in visitor's name/email, retrieve/reschedule/cancel

## THE HUMAN-FREE FLOW (user's master plan)
AI finds lead (Findymail/CrewAI) → AI calls/texts + qualifies (RetellAI) → Concierge books ITSELF on Cal.com → Zoho Lead/Deal + Task created → Human only gets the finished appointment notification
- ⚠️ Findymail + RetellAI connections were INITIATED but never finished (links expire — need reconnect when ready)
- ⚠️ NO outreach until user says "start"; user says "build human-free" to wire the full flow

## AI CONCIERGE RULES (from Master File)
- **Rule #1:** NEVER say "We don't do that." Instead: "Let me learn a little more about what you need and see how Simply Just Task may be able to help." — If there's a solution, we help find it.
- **Pricing rule:** May give ranges/starting rates only. NEVER guarantee final pricing, approve discounts, or modify contracts. Say: "Every project is unique, and some processes, pricing, and recommendations may vary... I'll connect you with our team."
- **Escalate to management when:** discount >10%, project >$1,000, commercial contracts, recurring contracts, payment arrangements, special pricing.
- **Philosophy:** flat-rate transparent pricing preferred; customized solutions, not rigid processes. Processes/timelines/pricing may vary (scope, materials, travel, urgency, vendors, weather, etc.).

## PAYMENTS ACCEPTED
Cash, Check, Credit/Debit, Zelle, Cash App, Venmo, PayPal, Business Checks, Electronic Invoices, Bank Transfers. Some projects need deposits / progress payments / materials upfront.

## LEAD PIPELINE (Zoho Lead Status mapping)
- New from CrewAI → Not Contacted
- Email sent → Contacted
- Tried, no answer → Attempted to Contact
- Qualified/hot → Pre-Qualified
- Try again later → Contact in Future (RECYCLE)
- Dead → Lost Lead / Junk Lead
- TODO: user adds custom statuses "Appointment Set" + "Recycled" in Zoho UI

## KNOWN ISSUES / IN PROGRESS
- ⚠️ CrewAI daily 7am schedule EXISTS ("Daily Lead Hunt – Apopka") but doesn't produce results — likely missing target_profile input in schedule settings, or Serper API rate limits (429s)
- 🏹 Manual hunt launched 2026-10-06 (kickoff 5911cde6-6302-4fce-b684-078a3ede4395) — results pending; when done: load leads into Zoho + email printable copy to tasksupport@simplyjusttask.com
- 📧 Outreach email template: not yet written
- 🤖 Make.com daily automation: not yet set up (backup for flaky CrewAI schedule)
- 📞 Findymail + RetellAI: need reconnecting for human-free flow
- 📱 Texting: decided email first; Google Voice suggested as free option
- 🌐 Website TODO (when available): Google Business Profile link, testimonials, before/after photos, service area map, FAQs, sample estimates/contracts, insurance/licensing info, videos

## USER PREFERENCES
- Plain language, boss/employee vibe, emojis ok
- User is not technical — click-by-click steps, no jargon
- User prints lead lists — provide printable formats
- Old Mac being patched with OpenCore Legacy Patcher (USB build): 8GB RAM, 2.6GHz Dual-Core i5, DDR3 1600MHz
- ⚠️ Chats hit a 10,000-message limit — always keep this file updated before chat ends!

## LAST UPDATED
2026-10-18 (added Cal.com details, human-free flow plan, Findymail/RetellAI status from old conversation)
