# BRAIN UPDATE - 2026-10-20 convo - PART 3 HOME VISIT CAL EVENT DONE (verified live)

Owner said DONE after click-by-click create. Assistant verified live before logging; did not trust DONE alone.

## OWNER DECISIONS THIS CONVO
- Consultation event Simply Stress-Free Booking: LEAVE IT EXACTLY AS-IS (30/45/60/120). Do not change it.
- New separate Home Visit event: 45 min to 1 hour (assistant recommendation accepted: default 60, choices 45/60).
- Assistant provided draft Home Visit description. Live description saved (see below) is the owner's shorter saved version, not verbatim assistant draft - logged honestly, do not claim assistant draft was pasted word-for-word.

## VERIFIED LIVE 2026-10-20 (Cal.com CAL_LIST_EVENT_TYPES, username simply-justtask)
Now 2 event types (was 1):

1) EXISTING - UNTOUCHED
- Title: Simply Stress-Free Booking
- Slug: simplybook
- ID: 7325379
- URL: https://cal.com/simply-justtask/simplybook
- Length: 30, multipleDuration [30,45,60,120]
- Location: somewhereElse / customLabel (unchanged)
- Price 0, hidden false

2) NEW - HOME VISIT
- Title: Home Visit / Estimate
- Slug: home-visit
- ID: 7554154
- URL: https://cal.com/simply-justtask/home-visit
- Length: 60, multipleDuration [45,60]
- Location: attendeeInPerson (customer home address)
- Price 0, hidden false, requiresConfirmation false, minimumBookingNotice 120
- Description saved: One Call. One Contact. One Less Thing To Worry About. Schedule a home visit and let us create a plan tailored to your needs.

## PART 3 STATUS
- Separate Cal Home Visit/Estimate event: DONE
- Leave simplybook as-is: DONE (verified unchanged)
- NOT done: booking writes back to Zoho as Appointment Set + Task. That is code work, needs owner code go (booking sync). Do not claim Part 3 fully complete until that sync exists.
- No sends, posts, calls, emails, CrewAI runs, /run-daily, /run-social, Render/env/code changes in this step. Only Cal UI create by owner + read-only verify + this brain upload.

## NEXT NEEDS (BRAIN order, after this step)
1. Owner says connect default (Fix #3) -> connect zoho, zoho_mail, facebook, instagram, twitter for user default, no Render change. Render config still frozen.
2. Supervised 9AM end-to-end run (separate owner go; up to 10 emails + social posts when live).
3. WhatsApp template (still 0 templates; cold text blocked).
4. Code go: WhatsApp text step, recycle loop, Cal booking sync to Zoho Appointment Set + Task, Lead_Source mapping in code.

Prior notes stand; do not duplicate: part3-booking-started 6c56720, part2-lead-source-done 7d6c842, part2-lead-status-done b363b97, frankenstein-fix3, handoff-summary.
