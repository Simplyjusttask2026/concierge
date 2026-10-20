# BRAIN UPDATE - 2026-10-20 convo - CONCIERGE ROLE + WINDOWS LAPTOP AI PARTNER (LAST BUILD)
Owner asks: our Concierge bot, we were going to have him doing stuff in this operation, have we done that? Is that in the plans? Also owner wants to create an AI to put on a Windows laptop to use entirely as their own, as a partner of Simply Just Task helping in this Frankenstein creation, but that is the last and final thing to build.

## ANSWER PART 1 - CONCIERGE ROLE: YES IN PLANS, PARTLY BUILT, NOT PROVEN LIVE
Do not confuse: assistant in this chat vs Concierge bot (concierge.py on Render sjt-concierge) vs CrewAI hunter vs Desktop/Windows agent.
Concierge planned job in Frankenstein flow: brain/middle, not just widget.
concierge.py verified sha d6c2e8d5 ~35,099 bytes, routes: /api/chat POST, /debug, /, POST /ingest-crewai-leads, /run-social GET|POST, /run-daily GET|POST, /ping.
Jobs written in code today:
1. Chat /api/chat: customer asks -> Zoho search memory (ZOHO_SEARCH_ZOHO_RECORDS) -> save prompt -> save_lead tool -> ZOHO_CREATE_ZOHO_RECORD Leads dedupe by email, Lead_Source Chat in save_lead / Web Research in bridge, Last_Name mandatory.
2. /ingest-crewai-leads: POST leads/result/output, extracts leads, skips no name/email/phone, dedupe email then phone, creates Zoho Leads with Source: CrewAI Studio Lead Automation-v1 in Description, returns received/created/exists/errors.
3. /run-daily: GET Zoho newest 50 -> AI Qualifier scores/notes -> updates Pre-Qualified/Not Qualified/Junk Lead etc -> warm email via Zoho Mail 8048488000000008002 (cap 10/day) with Cal link -> status Attempted to Contact -> daily report email (owner gets copy). Code exists.
4. /run-social: loads Composio tools for facebook/instagram/twitter as user_id -> Social Media Manager crew posts daily, replies messages/comments, captures leads via save_lead, report email. Code exists.
NOT proven live: no successful end-to-end 9AM combined run yet; 2026-10-19 Daily 9AM jobs were 1-second guard skips; 2026-10-18 /run-daily logs show Render as user_id default missing Zoho connection then. Needs Fix #3 default connections first. Do not claim Concierge is fully doing daily ops until first successful run log proves /run-daily + /run-social 202s + ingest summary created>0 + owner report email received.
Scopes/outdated notes: agent-laptop SOUL/README mention outdated WhatsApp blocked/WABA claims - owner later fixed WhatsApp via Kernel and verified WABA 1302701155079890. SOUL BOOKING link is old simply-just-task hyphen version; do not copy it as source of truth. Rule now: Base44/public exposure uses https://www.simplyjusttask.com/book-a-consultation; internal email/concierge uses https://cal.com/simply-justtask/simplybook unless owner changes.

## ANSWER PART 2 - WINDOWS LAPTOP AI PARTNER: ENVISIONED, SCAFFOLDED, NOT IMPLEMENTED, LAST/FINAL BUILD
Important corrections to protect owner:
- There IS an agent-laptop folder in repo (README, SOUL, agent.py, comms.py, install/run scripts), but assistant could not prove current intended role from those files in this convo and must not mislabel. Before any use, re-read agent-laptop files fresh and confirm with owner.
- Any previous framing where agent-laptop = automated Nextdoor operator must be treated as stale unless proven by fresh read + owner confirmation. brain has Nextdoor as separate AI every 2h supervised Kernel cadence. Do not collapse the new partner idea into that until owner orders edit and brain is updated. Future laptop partner must get fresh SOUL/spec before running.
- SOUL.md + agent.py seen in repo in previous sessions: SOUL describes the original Nextdoor-hunting Laptop Agent (Scout->Qualifier->Writer->Image Maker->Poster, comms gates with SJT_GO_EMAILS/CALLS/TEXTS, daily/2h schedules) but this was NOT re-proved here as the owner's frozen intent for the new dedicated Windows partner, and owner now explicitly says new laptop partner is distinct and last. Keep old laptop code as scaffolding only; do NOT reuse its role assignment or booking links without fresh owner-approved spec.

## OWNER DEFINITION OF LAPTOP PARTNER (LOCK THIS)
- Dedicated Windows laptop, entirely its own machine/entity as a partner of Simply Just Task.
- Helps build/run Frankenstein ops, reports to owner, only connects to Zoho/Cal/social/Composio after owner grants each account.
- NO own money decisions, NO buying/top-ups, NO sending email/text/call/post/DM without owner go gates.
- Needs identity + SOUL.md: mission, what it can/can't do, read BRAIN first, report every run, stop at payment walls, never guarantee price, never approve >10% discount/>$1000/commercial/recurring without owner.
- Windows-native realities: Python, Task Scheduler auto-run, and whichever free local brain/eyes (free local model/helper) will be named/stacked only after owner picks; do NOT assume a local stack until confirmed. Power settings + startup must be documented click-by-click.
- Order: build only after cloud Frankenstein proven (Fix #3, 9AM run, Zoho picklists, WhatsApp template, text/recycle code, Base44 link). LAST and FINAL thing to build.

## BOT FAMILY MAP (must teach in next chat)
- Messenger/front desk: Concierge (render) - chat, save/retrieve Zoho leads, booking help.
- Hunters: CrewAI Studio daily 9AM, Nextdoor AI every 2h, Social AI daily, Base44 front door.
- Vault: Zoho CRM is source of truth.
- Bookers: Cal.com consultation/home visit links (website exposure first, direct for machine emails).
- Approvers: Owner Anthony for every external send/payment/account change.
- Partner (future, last build): Windows Laptop Partner - watches/helps/runs playbooks locally, reports to owner, drafts for owner go.

## NEXT ACTIONS / OWNER DECISION POINTS
1. Finish cloud pieces first (Fix #3 default connections on owner say-so, prove 9AM, Zoho UI, WhatsApp template, text/recycle/book-sync code).
2. When owner says to spec laptop partner: ask Windows version + specs/RAM/free disk, which accounts it may use, how it should report (email only? chat?), hours allowed. Then and only then write SOUL/spec and install script.
3. Do NOT run agent.py or install agent-laptop on any machine yet.

Prior notes still standing: convo-daily-schedule-checklist b13d089, convo-frankenstein-fix3 7cbd98b, convo-fix3-no-render-change a9930de, convo-base44-website-booking 22ae723, convo-composio-limits-brain-reason 393c055, convo-handoff-summary 93b3341. This note adds Concierge-role answer and laptop-partner definition on top. No sends/posts/calls/runs, no installs, no Render change in this convo.
