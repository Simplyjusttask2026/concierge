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

## === CONVO LOG — 2026-10-18 (assistant new conversation) ===
Owner: Anthony (tasksupport@simplyjusttask.com). User clarified repeatedly:
- BRAIN.md is FOR THE ASSISTANT (memory across chats) — NOT the concierge brain. Concierge brain = MASTER_KNOWLEDGE + BUSINESS_INFO prompts inside concierge.py on Render.
- Booking link user pasted: https://cal.com/simply-justtask/simplyb (TRUNCATED). Verified live via Cal API: correct link is https://cal.com/simply-justtask/simplybook — Event 7325379 "Simply Stress-Free Booking", 30/45/60/120 min, requiresConfirmation=false. NOTE: concierge.py CAL_LINK currently wrong: "https://cal.com/simply-justtask/15min" — FIX to /simplybook pending approval.
- User asked: "how often will they post and what else do they do do they post answer messages" — ANSWER GIVEN / CADENCE CONFIRMED: Social crew 1x/day = 1 post per connected platform (Facebook Page 886504424556575 + Instagram @simply_just_task; twitter only if connected) AND checks/replies new messages/comments + save_lead (grade A/B). Lead machine daily 9am ET = qualify newest 50 Zoho leads, score 0-100 + notes, email MAX 10 Pre-Qualified/day (OUTREACH_DAILY_CAP=10, rest queued), status Attempted to Contact. Concierge chat 24/7: greets, lookup_lead memory, save_lead Zoho dedupe, book via Cal.com. Reports expected by owner EVERY run: "SJT Lead Machine Report" + "SJT Social Crew Report" emailed to tasksupport@simplyjusttask.com cc a.quinones@simplyjusttask.com with ALL leads/outreach copies/posts/replies/errors.
- User wants: "make sure its all running without me but also sending me an email" + "fix all of it make it a perfect machine integrate my lead generating crew thats in crew studio" — APPROVAL: yes to timers + email reports (no live test run yet without separate go).
- Architecture confirmed with user: Everything on Render EXCEPT Crew Studio lead gen. Render sjt-concierge srv-dau0mf8u01pc73aqe3cg https://sjt-concierge.onrender.com repo Simplyjusttask2026/concierge main autoDeploy=yes free plan. External: CrewAI Studio "Simply Just Task Lead Automation-v1" uuid d5813278-f085-4cc0-b1c6-d4a388e0bc47 Online https://simply-just-task-lead-automation-v1-d581327-df40e8a1.crewai.com kickoff needs input target_profile only. Integration plan: /run-daily Step0 kicks Studio hunter -> leads land in Zoho -> qualify/outreach same morning.
- Migration done earlier same day: 140 unreached leads Monday -> Zoho (status Not Contacted, 21 "On website" emails stripped). Zoho org tasksupport@ (CRM tasksupport accountId for Mail 8048488000000008002). Concierge brain upgrade commit 17bacd5 IS deployed live 2026-10-18 22:42 UTC (Render dep-dbakl2nlk1mc73d013tg): lookup_lead memory, partner reasoning HOW TO THINK, history last 12, async auto-save faster replies, daily cap 10.
- Owner check routine GIVEN: 1) Zoho Mail search "SJT" for reports, 2) https://sjt-concierge.onrender.com/ping safe check {alive:true}, 3) Zoho CRM Leads status flow Not Contacted->Pre-Qualified->Attempted to Contact, 4) FB Page + IG post daily, DEEP: Render dashboard Logs + GitHub Actions. WARN owner NOT to click /run-daily or /run-social just to look — they trigger real outreach/posts.
- Blockers FOUND this convo (live checks, NOT assumptions): GitHub daily-9am.yml active but total_count workflow runs=0 + repository secrets=0 => CREWAI_BEARER_TOKEN missing, Studio hunter never auto-fired. No /run-daily or /run-social timer yet (cron-job.org still pending). Render logs 22:39 UTC: /run-daily RAW ZOHO FETCH error "No connected account found for user ID default for toolkit zoho" (code 1810) => Leads reviewed: 0, 0 reports emailed. Zoho Mail inboxes searched: NO SJT reports landed yet, only old Render build emails. Render env keys present: COMPOSIO_API_KEY, GROQ_API_KEY, CAL_API_KEY, PYTHON_VERSION, stale MONDAY_API_TOKEN unused. COMPOSIO_USER_ID unset => default "default". FIX PLAN (built locally, syntax-checked, NOT yet pushed at time of this log): fix CAL_LINK to /simplybook, add Crew Studio Step0 + MACHINE_TOKEN optional guard, add GitHub timers (daily-machine 9am ET DST-proof + keep-awake /ping every 10min), update BRAIN cadence. Still needs owner clicks: connect Zoho CRM + Zoho Mail + Facebook + Instagram for Composio user "default" (Render), set CREWAI_BEARER_TOKEN on Render + GitHub secret, then supervised first live test (max 10 emails + 1 post/platform) only on owner separate "go".
- Assistant notes: crew_ai account crew_ai_salina-yan worked for Studio list/status; crew_ai_codify-axel returned 401 Bad credentials in one call. Assistant's own Composio Zoho connection (zoho_potion-parel) is NOT same as Render default user. Never print API keys/tokens. Keep updating this file before chat ends.
