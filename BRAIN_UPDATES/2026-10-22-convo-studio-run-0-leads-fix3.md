# BRAIN UPDATE - 2026-10-22 - Studio run 0 leads + fix-it list

Verified live 2026-10-22:
- CrewAI Simply Just Task Lead Automation-v1: Online / Successful, no error.
- Zoho leads created 2026-10-22: 0. Newest lead still 2026-10-21 01:46:04 -05:00.
- Manual Studio runs do not create Zoho leads. Bridge is scripts/daily_job.py Crew kickoff -> wait -> POST /ingest-crewai-leads -> Zoho.
- Render /ping alive, /debug HTTP 200. Zoho keys present in Render (names only), but /zoho-direct-test fails invalid_code. Owner must regenerate ZOHO_REFRESH_TOKEN in Render only, never in chat.
- Composio Zoho fallback read works: /call-center read Zoho leads 2026-10-22.
- GitHub secrets names only: CREWAI_BEARER_TOKEN present. MACHINE_TOKEN missing in GitHub and Render (both empty). Do not set one side only.

Fixed without owner 2026-10-22:
- HUNT_ONLY mode in scripts/daily_job.py (11AM/3PM/7PM ET, Crew hunt + Zoho ingest only, skips /run-daily and /run-social, no outreach).
- New .github/workflows/crewai-hunt-3x.yml schedule plus manual force_hunt.
- Addendum in FRANKENSTEIN_STATUS.md.

Still owner/daylight only:
- Regenerate Zoho refresh token in Render, then say render zoho saved.
- Supervised 9AM proof still not proven; do not force outside 8AM-9PM ET.
- WhatsApp Meta verify + template sjt_booking_intro_v1 owner-only.
- MACHINE_TOKEN set both GitHub and Render together, or neither.

FREE ONLY always.
