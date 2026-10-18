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

## SYSTEMS & KEY IDS
- **CRM:** ZOHO CRM (free tier) — REPLACED Monday.com (cost). Zoho also handles Mail + Voice. DO NOT switch again. Tracker Task created: 7624789000000771001. Test lead: 7624789000000777001 (safe to delete)
- **Zoho Mail sender account:** tasksupport@simplyjusttask.com — accountId 8048488000000008002 (used for outreach + reports)
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

## === 2026-10-18 LATE — ZOHO SWITCH DEPLOYED + LEAD MACHINE + SOCIAL CREW ===
Commits to concierge repo (main): Zoho switch (09944a6), BRAIN update (6cbc97b), social crew (a4fcccb), version-check fix (a930e735).
- concierge.py rewritten: save_lead → Zoho Leads (dedupe by email, Lead_Source=Chat, Lead_Status=Not Contacted). Monday code REMOVED.
- Endpoints: /run-daily (qualifier + email outreach + report), /run-social (social crew), /ping, /debug.
- /run-daily: pulls latest 50 Zoho leads → AI Qualifier scores (0-100) + notes appended to Description → status Pre-Qualified/Not Qualified/Junk Lead → Pre-Qualified get warm email via Zoho Mail + Cal.com link → status Attempted to Contact → DAILY REPORT emailed to tasksupport@simplyjusttask.com cc a.quinones@simplyjusttask.com (all leads, statuses, AI notes, outreach copies, errors).
- /run-social: Social Media Manager crew — daily post on connected platforms (facebook/instagram/twitter toolkits via Composio), replies to messages/comments, captures leads via save_lead, emails SOCIAL CREW REPORT.
- ⚠️ CRITICAL FIX: Composio manual tools.execute needs dangerously_skip_version_check=True (in zoho_exec). Without it: "Toolkit version not specified" error.
- Composio user_id on Render = env COMPOSIO_USER_ID (default "default") — Zoho + Zoho Mail + social toolkits must be connected in Composio for THAT user or pipelines return empty/errors.
- RetellAI calls + WhatsApp: planned but OFF (cost money). Email = free outreach channel.

## TODO LIST
1. ⏳ cron-job.org (free): GET https://sjt-concierge.onrender.com/run-daily daily 9:00 AM ET; GET /ping every 10 min (keeps Render awake). User must create account — click-by-click given
2. ⏳ Verify Composio "default" user has Zoho CRM, Zoho Mail, Facebook connected (else pipelines run empty)
3. ⏳ Verify first real report email arrives after next /run-daily with the version fix live
4. ⏳ Nextdoor verification — user clicks verify email + turns ON email notifications
5. ⏳ First real lead run — Findymail credits untouched
6. ⏳ Instagram + Twitter(X) + Snapchat: not connected in Composio yet — Snapchat has no API support; connect IG + X when ready
7. 📧 Outreach email template — written into OUTREACH_PROMPT (auto-generated per lead now)
8. 🌐 Website TODO: Google Business Profile, testimonials, photos, service-area map, FAQs, sample contracts, insurance info, videos
9. ⏳ Zoho custom statuses "Appointment Set" + "Recycled" (user adds in Zoho UI)

## USER PREFERENCES
- Plain language, boss/employee vibe, emojis ok
- Not technical — click-by-click steps, no jargon
- Prints lead lists — provide printable formats
- Posts: auto-post WITHOUT approval but always send owner a copy
- Wants reports emailed of EVERYTHING: all leads, all outreach copies, AI notes — DONE via /run-daily + /run-social reports
- Old Mac for OpenCore: 8GB DDR3 1600MHz, 2.6GHz Dual-Core i5 (~2012-2014) → target Ventura/Sonoma, NOT Tahoe
- ⚠️ Chats hit a 10,000-message limit — always update this file before chat ends!

## LAST UPDATED
2026-10-18 late (Zoho deployed, lead machine + social crew live, version-check fix pushed, cron-job.org pending user)
