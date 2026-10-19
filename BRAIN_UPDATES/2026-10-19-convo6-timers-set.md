# BRAIN UPDATE - 2026-10-19 convo 6 (append to BRAIN.md on next full sync)

## TIMERS SET (OWNER GO) - GitHub Actions, FREE ONLY
- Owner approved setting timers after CREWAI_BEARER_TOKEN secret was verified present (repo secrets total_count=1, added 2026-10-19T03:21:26Z). Token value never printed/stored.
- `.github/workflows/daily-9am.yml`: kept DST guard (13:00 + 14:00 UTC, script proceeds only at 09:00 America/New_York). Manual dispatch now defaults force=false so an accidental click does NOT trigger live pipelines.
- `scripts/daily_job.py` v2: wake Render /ping -> CrewAI Lead Automation-v1 kickoff (fails visibly if token missing/bad) -> THEN GET Render /run-daily + /run-social. Order matters: no silent email/post run when the token step fails.
- `.github/workflows/keep-awake.yml` NEW: cron */10 * * * * curls https://sjt-concierge.onrender.com/ping to keep free Render awake. Note: GitHub scheduled workflows can be delayed/dropped under load and are disabled after 60 days of repo inactivity on forks; verify runs in Actions tab.
- `concierge.py` BUG FIX PENDING SEPARATE COMMIT: CAL_LINK https://cal.com/simply-justtask/15min -> https://cal.com/simply-justtask/simplybook (Event 7325379 Simply Stress-Free Booking).
- NO manual live test was run as part of setting timers, except safe keep-awake ping. First real Daily run = next 9:00 AM ET schedule, unless owner separately says `go live test`. That first run WILL: qualify newest 50 Zoho leads, email up to OUTREACH_DAILY_CAP=10 Pre-Qualified, post 1x/day per CONNECTED social platform, reply to messages/comments, email SJT Lead Machine Report + SJT Social Crew Report to tasksupport@simplyjusttask.com cc a.quinones@simplyjusttask.com.
- STILL BLOCKING a useful first run (owner clicks, free): Render Composio user "default" (COMPOSIO_USER_ID unset on Render) must have zoho, zoho_mail, facebook, instagram connected, or pipelines return errors. Assistant-side Composio connections are NOT the Render default user.
- Images with every post: NOT implemented in code. Social crew currently creates text posts only. Gemini image 402 - FREE ONLY: do not pay/retry. Path: owner supplies real job photos.
- Nextdoor timer truth: NO GitHub Actions timer can run Nextdoor (no API). Every-2-hours 7am-10pm ET remains supervised Kernel/chat cadence, max 1 own post/day + 3 replies/check, draft-only until owner go.
