# BRAIN UPDATE - 2026-10-21 convo - OWNER ADDED ZOHO SECRET TO RENDER (CHECKED: NOT FOUND ON SJT-CONCIERGE) + ENTIRE BRAIN/FRANKENSTEIN READ + FIX #3 BYPASS CODE LIVE, NOT CONFIGURED
Owner said in this convo: also added the secret to Render and saved it for Zoho; upload to brain file; read entire brain file, really read Frankenstein list and notes to see where we are; you are on fix three and a build.
Upload only in this step. Summary only. No secret, client secret, API key, token, refresh token, grant code, password, env var value, full street address, or record contents in this note. No env var value was recorded. No Zoho record, booking, email, text, post, or call was created/sent in this convo.

## ENTIRE BRAIN READ - DONE THIS CONVO (live from GitHub main)
Repo: Simplyjusttask2026/concierge, owner Simplyjusttask2026. Only repo found for authenticated user; BRAIN is BRAIN.md in this repo, not a separate repo.
Read in full / decoded:
- BRAIN.md - 96,976 bytes, sha 78fb69d7d5ff397b03a0f0c2de97fe27c13a3074, 403 lines at read time.
- BRAIN_UPDATES/2026-10-20-convo-frankenstein-fix3.md - 6,114 bytes, sha 7bbd22f6.
- BRAIN_UPDATES/2026-10-21-convo-full-fix3-bypass-start.md - 18,723 bytes, sha 11a77688.
- BRAIN_UPDATES/2026-10-21-convo-zoho-secret-location-connection-test.md - 6,381 bytes, sha ea785053.
- BRAIN_UPDATES/2026-10-20-convo-fix3-connect-default-done.md - 6,301 bytes, sha 0212c898.
- BRAIN_UPDATES/2026-10-20-convo-fix3-no-render-change.md - 2,579 bytes, sha f9255569.
- BRAIN_UPDATES/2026-10-21-convo-zoho-fix3-whatsapp-cleanup.md - 8,937 bytes, sha 7dffb6bd.
- scripts/fix3_bypass_patch.py - 5,938 bytes, sha 6c92e56c.
- .github/workflows/fix3-bypass-apply.yml - 996 bytes, sha 37bf5de8.
- concierge.py - 65,855 bytes, sha 57c4ecbad1f7c593ae87ccdeb7030965dd18a21e.
Repo tree enumerated: 105 entries, truncated false. BRAIN.md itself was NOT changed or merged in this convo.

## FRANKENSTEIN LIST - WHERE WE ARE (both taxonomies preserved, do not smooth over)
A) 9-part owner plan (2026-10-20):
1 BONES: BRAIN/GitHub/Render/Composio live; Fix #3 Render proof still open; Keep Awake proven in prior notes, Daily 9AM not proven end-to-end.
2 LEAD VAULT: Zoho CRM live assistant-side; dedupe rule in code/notes; Zoho picklists Lead_Status Appointment Set/Recycled and Lead_Source CrewAI/Nextdoor/Instagram still owner-UI pending per BRAIN TODO.
3 BOOKING: Cal consultation 7325379 + Home Visit 7554154 live in code/debug; Cal->Zoho write-back code live, NOT proven (see Fix #3 proof below).
4 LEAD HUNTERS: CrewAI/website save_lead/Findymail/social inbound pieces built in prior notes; no proven real 9AM end-to-end run.
5 CALL CENTER: email path built; WhatsApp in prior notes cleaned to 1 ACTIVE keeper, 0 templates, cold text blocked; Retell parked FREE ONLY; text/recycle chase not proven complete.
6 SOCIAL AI: FB/IG/X connected assistant-side in prior notes; daily post/reply/DM->Zoho not proven via Render.
7 NEXTDOOR: separate personal-only Kernel, draft-only, every-2h target, no API.
8 DAILY SCHEDULE: /ping every 10 min target, 9AM chain target, not proven scheduled end-to-end.
9 FREE ONLY LOCK: unchanged. Human only: consultation, home visit, job, discount >10%, project >$1000, contracts, payment plans.
B) Later 8-part monster list: 1 BRAIN live, 2 Recycle Loop code/drafts 0 emails, 3 Cal->Zoho blocked Fix #3, 4 Email Clean plan only, 5 Call Center asked/not fully built, 6 Website Concierge live, 7 Direct Cal Bookings code live proven up to Zoho wall, 8 Social Hub + 9AM built never proven. Separate: Home Sheet/AppSheet plan no code, Nextdoor Kernel draft-only.
Blockers in order carried forward: Fix #3 Render proof, Daily 9AM proof, Zoho picklists, WhatsApp template, supervised first run.

## FIX #3 + BUILD - NEW LIVE TRUTH THIS CONVO (supersedes older 'bypass not deployed')
Older note said the direct-Zoho bypass patch was built locally only, NOT committed/deployed. That is no longer current:
- Live concierge.py on main NOW contains: ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_REFRESH_TOKEN, ZOHO_ACCOUNTS_URL, ZOHO_CRM_API_URL env reads; _zoho_direct_configured(); direct-crm-fallback-v1; zoho_exec = Composio first, direct Zoho CRM fallback on Composio failure; CRM-only v1 (mail still Composio).
- Live Render check this convo: GET https://sjt-concierge.onrender.com/ping -> {alive:true}. GET /debug -> cal_booking_sync part3-v1-real-confirmed-only, cal_consultation_event_id 7325379, cal_home_visit_event_id 7554154, cal_key_loaded true, crm zoho, composio_user_id default, zoho_direct_bypass_configured FALSE, zoho_path composio-first,direct-crm-fallback-v1.
Truth: the bypass BUILD is deployed/live, but it is NOT configured. Fix #3 is still NOT proven. No /sync-cal-bookings proof was run in this convo.

## OWNER-ADDED RENDER ZOHO SECRET - CHECKED, NOT FOUND ON THE SERVICE
Owner reported adding/saving the Zoho secret in Render.
Checked Render service sjt-concierge srv-dau0mf8u01pc73aqe3cg (only Render service found; page 2 empty; repo Simplyjusttask2026/concierge main):
- RENDER_LIST_ENV_VARS_FOR_SERVICE keys ONLY (values never recorded): MONDAY_API_TOKEN, CAL_API_KEY, PYTHON_VERSION, GROQ_API_KEY, COMPOSIO_API_KEY = 5 total.
- Page 2 env vars: empty. Env groups: none.
- No ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, or ZOHO_REFRESH_TOKEN key was present at check time.
Conclusion: either the var was added under a different name/account/service, was not saved, or did not stick. Do NOT claim it is on Render until the API key list and /debug show it.
Important: secret ALONE would still be insufficient. _zoho_direct_configured() returns true only when ALL THREE are present in Render: ZOHO_CLIENT_ID + ZOHO_CLIENT_SECRET + ZOHO_REFRESH_TOKEN (exact names). A client secret without a refresh token cannot mint a Zoho access token. Owner must enter all 3 directly in Render dashboard only (Environment for sjt-concierge); assistant never sees/types values. Adding them will trigger a redeploy.
Composio path also unchanged: Render still uses composio_user_id default, and the last proven Render->Composio Zoho result in prior notes was 404 No connected account found for user ID default. That also remains unproven until a new proof run is separately approved.

## NEXT EXACT STEPS - AWAITING OWNER
1) Owner re-opens Render dashboard -> sjt-concierge -> Environment, confirms the 3 exact keys above exist (values entered by owner only, never in chat/GitHub/BRAIN). If only the secret was entered elsewhere, move/enter correctly there and Save.
2) Owner then says only: render zoho env entered. Assistant re-checks env KEY names only (no values) + /ping + /debug. Claim configured ONLY if zoho_direct_bypass_configured: true.
3) Proof gate, separate exact go required because it can create Zoho records: state the one /sync-cal-bookings proof first; claim Part 3 / Fix #3 WORKING only if synced >=1 AND assistant Zoho search finds the Lead (Appointment Set) + Task containing the Cal UID. Otherwise report exact error and stop.
4) Do NOT run /run-daily, /run-social, CrewAI kickoff, any email/text/post/call, booking create/cancel, picklist change, WhatsApp template submit, BRAIN.md merge, COMPOSIO_USER_ID change to a guessed ID, or deletion of old connections without a separate explicit owner go. FREE ONLY always.
