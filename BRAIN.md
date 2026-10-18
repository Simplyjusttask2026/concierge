# 🧠 SIMPLY JUST TASK — BRAIN FILE
> Read this at the start of every new conversation. It contains everything the assistant needs to know. Update it before ending a conversation ("update my brain file").

## BUSINESS
- **Name:** Simply Just Task
- **Owner:** Anthony Quinones-Savino (tasksupport@simplyjusttask.com)
- **What:** Errands, home tasks, concierge, lifestyle support
- **Market:** Central Florida (Apopka + surrounding)
- **Target leads:** RESIDENTIAL ONLY (busy families, homeowners, seniors) — NO commercial/businesses

## SYSTEMS & KEY IDs
- **Website:** Squarespace (built, hero + booking button + badges live)
- **Booking:** Cal.com booking page — verified working
- **CRM:** ZOHO CRM (free tier) — REPLACED Monday.com (cost). Zoho also handles Mail + Voice. DO NOT switch again.
- **Lead hunter:** CrewAI crew "Simply Just Task Lead Automation-v1" — crew_uuid: d5813278-f085-4cc0-b1c6-d4a388e0bc47
- **AI Concierge chatbot:** Render service "sjt-concierge" (srv-dau0mf8u01pc73aqe3cg), auto-deploys from GitHub repo Simplyjusttask2026/concierge (main branch). Status: LIVE (turquoise widget).
- **CrewAI connection note:** only ONE active connection: crew_ai_codify-axel (old one removed)

## LEAD PIPELINE (Zoho Lead Status mapping)
- New from CrewAI → Not Contacted
- Email sent → Contacted
- Tried, no answer → Attempted to Contact
- Qualified/hot → Pre-Qualified
- Try again later → Contact in Future (RECYCLE)
- Dead → Lost Lead / Junk Lead
- TODO: user adds custom statuses "Appointment Set" + "Recycled" in Zoho UI

## THE MACHINE (goal state)
CrewAI hunts (daily 7am) → leads into Zoho CRM → outreach email via Zoho Mail → qualified leads get called (Zoho Voice, human for now) → appointments booked on Cal.com → cold leads recycled

## KNOWN ISSUES / IN PROGRESS
- ⚠️ CrewAI daily 7am schedule EXISTS ("Daily Lead Hunt – Apopka") but doesn't produce results — likely missing target_profile input in the schedule settings, or Serper API rate limits (429s)
- 🏹 A manual hunt was launched 2026-10-06 (kickoff 5911cde6-6302-4fce-b684-078a3ede4395) — results pending; when done: load leads into Zoho + email printable copy to tasksupport@simplyjusttask.com
- 📧 Outreach email template: not yet written
- 🤖 Make.com daily automation: not yet set up (backup for flaky CrewAI schedule)
- 📱 Texting: decided email first; Google Voice suggested as free texting option

## USER PREFERENCES
- Plain language, boss/employee vibe, emojis ok
- User is not technical — give click-by-click steps, avoid jargon
- User prints lead lists — provide printable formats
- Old Mac being patched with OpenCore Legacy Patcher (USB build)

## LAST UPDATED
2026-10-18
