# FRANKENSTEIN STATUS - Simply Just Task
Live-tested 2026-10-21 overnight closeout. Summary only; BRAIN.md + BRAIN_UPDATES are full memory. FREE ONLY always.

## LIST IN ORDER
1 BONES  2 LEAD VAULT  3 BOOKING  4 LEAD HUNTERS  5 CALL CENTER  6 SOCIAL AI  7 NEXTDOOR AI  8 DAILY SCHEDULE  9 FREE ONLY LOCK

## DONE / TESTED LIVE
- GitHub Simplyjusttask2026/concierge, 15 workflows; Render /ping alive, /debug OK.
- Cal 7325379 + Home Visit 7554154 live; 2 upcoming bookings checked.
- Zoho modules + picklists DONE: Appointment Set, Recycled, Contact in Future; CrewAI, Nextdoor, Instagram, TikTok, YouTube, LinkedIn sources.
- CrewAI Lead Automation-v1 Online; GitHub CREWAI_BEARER_TOKEN exists (name only).
- Keep Awake scheduled success. Daily 9AM workflow exists, scheduled runs guard-skip when delayed past 9 ET.
- FB Page 52, IG @simply_just_task 218/7, X @simplyjusttask OK. WhatsApp 1 keeper number. Retell draft parked.
- concierge.py compile OK. Direct-Zoho bypass code deployed. Closeout: WhatsApp drafts + recycle candidates added to daily report, DRAFT ONLY (verify /debug frankenstein_closeout after deploy).
- SOPs created: SOPS/CALL_CENTER.md, SOPS/WHATSAPP_TEMPLATE.md, SOPS/EMAIL_CLEAN.md.

## OWNER NEEDED WHEN AWAKE
1. Fix #3: enter ZOHO_CLIENT_ID + ZOHO_CLIENT_SECRET + ZOHO_REFRESH_TOKEN in Render sjt-concierge Environment (only there). Proof tested tonight: synced 0, Composio 404 default, bypass false, Zoho Task 0.
2. WhatsApp Meta: verify phone + create/approve template sjt_booking_intro_v1. Templates 0, NOT_VERIFIED tonight.
3. Supervised 9AM proof (CrewAI to Zoho to daily to social, reports). Not run at night - outreach safety 8am-9pm.
4. Later: TikTok/LinkedIn/YouTube in concierge, Nextdoor timer, Email Clean rules - each needs its own go.

## BUILT 2026-10-21 OVERNIGHT
- Call Center: /call-center plan v1 draft-only + daily report section. Unit-tested fake leads, compile OK.
- Nextdoor: watcher v2 CLI, live Kernel scan 3 leads scored 80 saved to Zoho verified by ID, 1 watch, NO post/comment/DM sent (owner go per item).
- Nextdoor timer workflow every 2h proves watcher logic only; live Kernel hunt needs chat/agent session.
- WhatsApp template API FAILED WABA not allowed. Owner Meta step unchanged.

## ADDENDUM 2026-10-22 (verified live)
- Studio test run finished, Zoho leads created 2026-10-22 = 0. Manual Studio runs do not use the GitHub bridge (`scripts/daily_job.py`).
- Fix #3 updated: Render Zoho keys ARE present, but direct token test fails `invalid_code`. Owner must regenerate `ZOHO_REFRESH_TOKEN` in Render only. Composio fallback read verified via `/call-center` on 2026-10-22.
- Hunt-only 3x/day added: `crewai-hunt-3x.yml` + `HUNT_ONLY` in `daily_job.py` (11AM/3PM/7PM ET, Zoho ingest only, NO outreach).
- Supervised 9AM proof still pending (daylight 8AM-9PM ET only). WhatsApp Meta still owner-only. `MACHINE_TOKEN` missing on both GitHub and Render - set both together or neither.

## ADDENDUM 2026-10-30 — Dell integration and recovery scope (documentation only)
Historical verification labels above retain their original dates; they are NOT fresh health checks. Owner confirmed a separate documentation branch and separate OneDrive backup, not deployment or live automation changes.

- [x] Locate current main and Dell feature-branch source; identify existing panel/email/draft functions.
- [x] Save dated baseline source ZIPs to a new Simply Just Task AI Safe OneDrive folder; initial permissions returned owner only.
- [x] Record public-safe conversation memory in BRAIN_UPDATES/2026-10-30-dell-frankenstein-safe.md, preserving BRAIN.md.
- [ ] Complete inventory and validation of all relevant master documents; only an initial subset has been reviewed.
- [ ] BONES: source-traceable knowledge, non-secret configuration, tested installation, runtime diagnostics and rollback.
- [ ] LEAD VAULT: reuse verified existing CRM, deduplicate, retain source links, lifecycle, opt-outs and follow-up history; no competing production database.
- [ ] BOOKING: verified calendar availability, duration/travel buffers, estimates and confirmed scheduling; no unverified promises.
- [ ] LEAD HUNTERS: relevant real inquiries, qualification, respectful follow-ups; never fabricate contacts or import sample leads.
- [ ] CALL CENTER: individual email drafts/replies/new composition, threading, correct mailbox, configurable owner CC/BCC, duplicate/loop protection, recipient validation and confirmed sends. Owner copy address remains unconfirmed.
- [ ] CALL CENTER: provider-supported voice intake, AI disclosure/consent, summaries and human handoff; phone AI not established by opening Zoho Voice.
- [ ] SOCIAL AI: content drafts and clearly labeled image generation; no fake completed-project photos or live publishing under this authorization.
- [ ] NEXTDOOR AI: permitted intake, real source links, lead scoring and personalized drafts; validate access and platform constraints before implementation.
- [ ] DAILY SCHEDULE: monitored runs, locks, stop controls, safe retries, restart recovery and reports; avoid duplicate cloud/Dell jobs. Existing live schedules unchanged.
- [ ] FREE ONLY LOCK: no purchases or paid upgrades; document provider limits and require separate approval for costs.
- [ ] RECOVERY: capture Dell-only settings and lead database safely, establish encrypted offline copy, verify archive contents/checksums and complete a restore exercise. Source snapshots alone are not a full system backup.

Open decisions: owner BCC address; current business contacts; commercial/residential policy conflict; actual local model and mailbox configuration. Preserve current send-confirmation controls. See SOPS/DELL_RECOVERY_PLAN.md. Runtime features remain planned or unverified unless separately proven. No merge/deploy authorized.
