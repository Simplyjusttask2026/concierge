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
- **CRM:** ZOHO CRM (free tier) — REPLACED Monday.com (cost). Zoho also handles Mail + Voice. DO NOT switch again. Tracker Task created: 7624789000000771001
- **Lead hunter:** CrewAI crew "Simply Just Task Lead Automation-v1" — crew_uuid: d5813278-f085-4cc0-b1c6-d4a388e0bc47 — Online, profile: local residential Central Florida
- **AI Concierge chatbot:** Render service "sjt-concierge" (srv-dau0mf8u01pc73aqe3cg), https://sjt-concierge.onrender.com, auto-deploys from GitHub Simplyjusttask2026/concierge (main). Status: LIVE (turquoise widget)
- **CrewAI connection:** only ONE active: crew_ai_codify-axel
- **Findymail:** ACTIVE — 25 credits + 10 verifier credits, unused. STOP at 0, never buy more without asking
- **RetellAI:** agent exists but PARKED — 0 phone numbers bought, low balance, DO NOT top up or pay
- **Facebook:** Page "Simply Just Task" ID 886504424556575 — active (25 posts + 5 Messenger convos checked previously)
- **Nextdoor:** new account under tasksupport@simplyjusttask.com — NOT verified yet (no verify email seen in inbox)
- **Outlook:** daily report DRAFT created — template only, not sending yet

## BOOKING — CAL.COM (⚠️ NOT CALENDLY — user switched so the Concierge can book ITSELF. Never mention Calendly again.)
- **Account:** Simply Just Task / simply-justtask — America/New_York
- **Event:** "Simply Stress-Free Booking" — ID 7325379, slug: simplybook
- **Link:** cal.com/simply-justtask/simplybook
- **Durations:** 30 min default (30/45/60/120), 2-hour minimum notice
- **requiresConfirmation: false** → Concierge books INSTANTLY, no human approval

## THE HUMAN-FREE FLOW (user's master plan)
AI finds lead (Findymail/CrewAI) → AI calls/texts + qualifies (RetellAI, parked) → Concierge books ITSELF on Cal.com → Zoho Lead/Deal + Task created → Human only gets the finished appointment notification
- ⚠️ NO outreach until user says "start"; user says "build human-free" to wire the full flow
- ⚠️ Chat assistant CANNOT self-schedule — real automation needs an outside timer: plan = GitHub Actions cron (free) in concierge repo at 9:00 AM America/New_York → CrewAI run + Zoho Mail Nextdoor check + lead logging + owner copy/daily report. Secrets stored encrypted, never in chat/code. Requires user reply "set 9am schedule" to activate.

## AI CONCIERGE RULES (from Master File)
- **Rule #1:** NEVER say "We don't do that." Instead: "Let me learn a little more about what you need and see how Simply Just Task may be able to help."
- **Pricing rule:** ranges/starting rates only. NEVER guarantee final pricing, approve discounts, or modify contracts. "Every project is unique... I'll connect you with our team."
- **Escalate to management when:** discount >10%, project >$1,000, commercial contracts, recurring contracts, payment arrangements, special pricing
- **Philosophy:** flat-rate transparent pricing; customized solutions, not rigid processes

## PAYMENTS ACCEPTED
Cash, Check, Credit/Debit, Zelle, Cash App, Venmo, PayPal, Business Checks, Electronic Invoices, Bank Transfers. Some projects need deposits / progress payments / materials upfront.

## LEAD PIPELINE (Zoho Lead Status mapping)
- New → Not Contacted | Email sent → Contacted | No answer → Attempted to Contact | Qualified → Pre-Qualified | Recycle → Contact in Future | Dead → Lost Lead / Junk Lead
- TODO: user adds custom statuses "Appointment Set" + "Recycled" in Zoho UI

## TODO LIST (as of last status check)
1. ⏳ Nextdoor verification — user clicks verify email + turns ON email notifications
2. ⏳ 9 AM daily trigger — GitHub Actions timer not built yet (awaiting "set 9am schedule")
3. ⏳ First lead run — CrewAI never completed a run; Findymail credits untouched
4. ⏳ Live auto-post — user chose: post WITHOUT approval + send owner a copy
5. ⏳ Daily report — draft only, not live
6. ⚠️ CrewAI "Daily Lead Hunt" 7am schedule exists but broken — missing target_profile input and/or Serper 429 rate limits
7. 📧 Outreach email template — not written yet
8. 🌐 Website TODO: Google Business Profile, testimonials, photos, service-area map, FAQs, sample contracts, insurance info, videos

## USER PREFERENCES
- Plain language, boss/employee vibe, emojis ok
- Not technical — click-by-click steps, no jargon
- Prints lead lists — provide printable formats
- Posts: auto-post WITHOUT approval but always send owner a copy
- Old Mac for OpenCore: 8GB DDR3 1600MHz, 2.6GHz Dual-Core i5 (~2012-2014) → target Ventura/Sonoma, NOT Tahoe
- ⚠️ Chats hit a 10,000-message limit — always update this file before chat ends!

## LAST UPDATED
2026-10-18 (merged status scoreboard: Findymail active, RetellAI parked, Facebook active, Nextdoor pending, 9am scheduler plan)
