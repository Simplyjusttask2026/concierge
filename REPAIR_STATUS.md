# Frankenstein repair branch — 2026-10-28

This branch contains real code repairs, NOT a claim that the live machine is fixed.
Production main, Render settings, live data, sends and purchases are untouched.

Implemented and covered by offline regression tests:
- Full oldest-first CRM pagination, token continuation, eligible queue selection, and loud errors instead of fake zero-lead success.
- All waiting lead records can be reached; held Pre-Qualified leads remain eligible. New recycle records get an explicit due date; undated historical recycle records require review, not unsolicited contact.
- Owner management authentication fails closed. No GET job triggers; owner-only persisted job outcomes; HTTP accepted is not completion.
- Durable transactional claims, daily channel caps, receipt-checked send states, uncertain-send replay prevention; no contact status update before provider acceptance.
- Mocked transport tests verify disabled/quiet-hour paths send nothing. Default effects disabled: CRM writes, outreach, social and report emails each require separate activation.
- Paid image generation and synthetic fallback removed from social path; Facebook supports text-only; Instagram requires an explicitly approved real image and remains visibly held without one.
- Both callback numbers and tasksupport email in social caption, no ad Cal link; X is not silently connected to the wrong identity.
- Single catch-up operations runner, downstream work independent of exhausted CrewAI; hunt mode stops explicitly rather than retrying quota exhaustion.
- Existing fetched widget history fix retained, length limited, no token or browser credentials put in code.
- Existing fetched booking pagination retained, bounded and included in applied daily results.
- Compatibility helper supplied for concierge imports; independent jobs/status/report metadata survive mail-report failure.

Important activation limits:
1. No deployment has been performed or authorized by this branch build. Do not merge blindly.
2. SJT_STATE_DIR must be an absolute path to genuinely persistent storage and SJT_DURABLE_STATE_ACK must be acknowledged. SQLite assumes one host/shared durable filesystem. Free Render ephemeral disk is NOT sufficient; this branch does not buy a disk. A genuinely free durable hosting/state arrangement must be validated before activation. SJT_STATE_PATH plus SJT_STATE_PERSISTENT_CONFIRMED supports existing owner draft metadata.
3. MACHINE_TOKEN must be present in the server and GitHub with matching values. Use x-machine-token header, never query strings/chat/repo. Current Render effective-user credentials still require a successful read-only check after connector access is restored.
4. Effects flags: SJT_ENABLE_CRM_WRITES, SJT_ENABLE_OUTREACH, SJT_ENABLE_SOCIAL_POSTS, SJT_ENABLE_REPORT_EMAIL are all OFF by default. Branch tests do not authorize live sends/posts. Exact external actions need owner approval before they occur.
5. Current job outcomes are authoritative, not a deployment green light. Read-only, held, partial, uncertain and failed outcomes do not count as a completed live job. Interrupted jobs are not automatically replayed.
6. CrewAI monthly allowance cannot be restored by code. No paid upgrade, new account or quota bypass. No complete free replacement hunter was built here.
7. Nextdoor live selectors/login and Dell installation/uptime still need on-device validation. This branch does not implement live Zoho Voice AI, solve WhatsApp template permissions, or activate broad social reply bots.
8. No duplicate CRM records deleted; no historical source invented; no known user credentials changed. Historical undated follow-ups and real contact eligibility need review.
9. Independent on-account delivery and end-to-end acceptance remain required. Provider acceptance is not proof of arrival.

Tests are pure offline fixtures with temporary databases and mocked API responses. Full production dependency import, Render deploy, Windows/Dell/browser login and real account sends were NOT tested. The branch's CI installs only requests and Flask for isolated tests; it never runs the concierge or an account job.
