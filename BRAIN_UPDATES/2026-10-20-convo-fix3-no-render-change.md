# BRAIN UPDATE - 2026-10-20 convo - FIX #3 DO NOT CHANGE RENDER / Base44 place
Owner rules this convo: (1) lets not change the Render production config if we do not have to. (2) The original user for Composio is tasksupport@simplyjusttask.com. (3) Also asked how do we include Base44 the app (answered, see below).

## FIX #3 CORRECTED TRUTH - DO NOT CHANGE RENDER
Render production config FROZEN by owner. Do NOT set COMPOSIO_USER_ID on Render unless owner separately orders it in a future chat.
Render sjt-concierge srv-dau0mf8u01pc73aqe3cg env KEYS only: COMPOSIO_API_KEY present, COMPOSIO_USER_ID absent. concierge.py line30 fallback = user_id default. This is INTENTIONAL - keep it.
tasksupport@simplyjusttask.com = owner Composio login email (original user). It is the email shown on zoho/zoho_mail/facebook connections. It is NOT the SDK user_id string. SDK user_id default is a label for connections made under that login, not a different person.
Assistant-side connections verified ACTIVE 2026-10-20: zoho zoho_fent-resign, zoho_mail zoho_mail_batter-musang 8048488000000008002 tasksupport@, facebook, instagram @simply_just_task, twitter @simplyjusttask, whatsapp whatsapp_tony-juggle +1 352-849-2344.
PROOF OF GAP (Render logs read-only, no config change, no pipeline run): 2026-10-18 logs RAW ZOHO FETCH error 404 No connected account found for user ID default for toolkit zoho, code 1810, at 22:17, 22:39, 22:42 UTC. Earlier same day Toolkit version not specified error (fixed in code by dangerously_skip_version_check). So Oct 18 Render could NOT read Zoho as default.
CORRECT FIX (no Render change): connect Zoho, Zoho Mail, Facebook, Instagram, Twitter for entity/user default in Composio, logged in as tasksupport@simplyjusttask.com. Then Render code as-is works. NO RENDER_UPDATE_ENV_VAR.
STATUS: owner has NOT yet said connect default. Do NOT initiate connections until owner says connect default. Do NOT run /run-daily or /run-social to test without separate owner go (sends real email/post).
Base44 note from prior turn stands: no native Composio Base44 toolkit. Base44 = front door only. Path: webhook/link/API -> Zoho first (needs Fix #3 default connections first), Cal stays booking, Zoho stays vault, CrewAI stays hunter. Never paste Base44 API key or Composio API key in chat. Never guess user_id. Never chain Base44->Twitter->Composio.
Prior notes: BRAIN_UPDATES/2026-10-20-convo-daily-schedule-checklist.md b13d089, BRAIN_UPDATES/2026-10-20-convo-frankenstein-fix3.md 7cbd98b. This note supersedes any do Render env change instruction in those notes.
