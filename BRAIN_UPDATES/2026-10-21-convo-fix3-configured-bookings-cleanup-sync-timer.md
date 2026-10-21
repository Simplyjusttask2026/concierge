# BRAIN UPDATE - 2026-10-21 convo - FIX #3 CONFIGURED + BOOKINGS CLEANUP + SYNC TIMER + CANCEL/RESCHEDULE LOOK
Summary only. No secret, client secret, API key, token, refresh token, grant code, password, env var value, or full street address in this note. No env var value was recorded.
BRAIN.md itself was NOT edited or merged in this convo. This note is the Frankenstein list update, as done in prior BRAIN_UPDATES notes, until owner says merge brain.
Repo: Simplyjusttask2026/concierge, branch main.

## FRANKENSTEIN LIST UPDATES

### Fix #3 - CONFIGURED, NOT YET PROVEN
- CONFIGURED: true - all 3 Zoho keys are present in Render (key names only, no values recorded), /debug verified true.
- Token not yet used. Fix #3 is NOT proven yet.
- Supersedes the older status that said zoho_direct_bypass_configured FALSE / keys not found on the service.

### Part 3 / Direct Cal Bookings - UNBLOCKED, AWAITING FIRST SYNC PROOF
- Direct Cal.com bookings: customer self-books at cal.com/simplyjusttask/... , no instant Zoho sync; it only reaches Zoho later via /sync-cal-bookings.
- Website concierge chat bookings: book_appointment sends straight to Cal API (source: website concierge), then instantly syncs Zoho Lead + Task.
- Both paths end as a Zoho Task stamped with [Cal UID].
- No /sync-cal-bookings run yet in this convo. No Zoho Lead/Task verified yet for a direct Cal booking. Claim Part 3 / Fix #3 WORKING only after a sync proof: synced >=1 AND Zoho search finds the Lead (Appointment Set) + Task containing the Cal UID.

### Bookings cleanup
- Owner's 2 bad bookings cancelled and verified CANCELLED: uiSi... (253 phone) and t7b... (wrong name). Full IDs not expanded in this note beyond what owner provided in convo.
- Clean Anthony booking kept: today 12:00 PM ET, Cal UID npyYZdCp8uCYimeMW2NKmC.
- Michael bookings: owner confirmed they are tests - still in Cal, not yet cancelled.

### Auto-sync
- Today auto-sync only runs inside 9AM /run-daily (after CrewAI). Chat limit does not stop Render/GitHub.
- Proposed 4x/day timer NOT built: cal-sync-4x.yml at 9:15 / 1:15 / 5:15 / 9:15 ET.
- Needs separate owner go: go cancel tests and build timer.

### Concierge cancel / reschedule - LOOKED AT, NOT BUILT
- Current agent tools in code: save_lead, lookup_lead, check_availability, book_appointment only. No lookup/cancel/reschedule tool for an existing booking exists yet.
- Customer can self-cancel via Cal email today. Zoho is NOT updated if a synced booking later cancels.
- Zoho Tasks picklist checked live: Not Started, Deferred, In Progress, Completed, Waiting for input. There is no Cancelled status.
- Proposed build (not done): lookup_appointment, cancel_appointment, reschedule_appointment in concierge.py, keyed on Cal UID, covering both website concierge and direct Cal.com bookings, with customer confirm-gate and Zoho Task/Lead update rules from the convo proposal, plus prompt Step 6 and /debug marker appointment_changes: cancel-reschedule-v1.
- Building it needs a separate exact go: go build cancel reschedule. First real test would be supervised on one Michael test booking - separate go, not automatic.

## CONVO SUMMARY
- WhatsApp / Kernel logged-in check reported done at start of convo.
- Fix #3 moved from not configured to CONFIGURED: true, verified via /debug, token not yet used.
- Bookings cleanup done as above; Michael test bookings left in Cal pending owner go to cancel tests.
- Sync timing clarified: only 9AM /run-daily today; 4x/day timer proposed, not built.
- Cancel/reschedule gap confirmed in code, including direct website-through-Cal.com booking path owner flagged.

## PENDING GATES - SEPARATE OWNER GO REQUIRED
1. go cancel tests and build timer - cancel Michael test bookings and build cal-sync-4x.yml.
2. Sync proof - run /sync-cal-bookings proof, then verify Zoho Lead + Task by Cal UID before claiming Fix #3 / Part 3 working.
3. go build cancel reschedule - build lookup/cancel/reschedule tools as proposed above.
4. Merge brain - only when owner says so; BRAIN.md not edited in this convo.

FREE ONLY always. No Zoho record, booking create/cancel, email, text, post, or call was made by this BRAIN upload itself.
