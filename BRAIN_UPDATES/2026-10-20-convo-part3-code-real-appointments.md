# BRAIN UPDATE - 2026-10-20 convo - PART 3 CODE DONE: real confirmed appointments only (deployed, not yet end-to-end proven)

Owner said GO CODE after locking these rules:
- Concierge may book ALL appointment types: Home Visit / Estimate, consultation by phone, virtual, or in person.
- Only REAL appointments: real human, real email/phone, REAL full street address, customer explicitly confirms exact type/date/time/address, both parties aware.
- No real address = no booking. No Cal-confirmed record = not booked.
Owner was working on Google Business Profile in parallel during this step (mentioned only, NOT verified/done here; GBP belongs to Part 6 later).

## CODE SHIPPED
- Patch: scripts/part3_booking_patch.py (fetched by workflow from Composio short link v_q5cIz_B0)
- Workflow: .github/workflows/part3-booking-apply.yml
  - Add-workflow commit: d263caaa5af1a001a71b3f598f79426325a05bbd
  - Run: 39380291813 - SUCCESS https://github.com/Simplyjusttask2026/concierge/actions/runs/39380291813
  - Patch commit on main: 1ef5e2df185b471e3d179028dc13779f78ca1463 (Frankenstein Part3: real confirmed appointments + Zoho Task sync)
  - concierge.py now 61,157 bytes, blob 4f93e83a9a3722289d85bd632109266daeb5a0d4 (was 36,505)

## WHAT THE CODE NOW DOES (concierge.py, marker PART3_REAL_APPOINTMENTS_V1)
1. check_availability now takes appointment_type (consultation/home_visit), consultation_mode (phone/virtual/in_person), duration. Consultations 30/45/60/120 on event 7325379 simplybook. Home Visit 45/60 on event 7554154 home-visit.
2. book_estimate replaced by book_appointment in tools. Requires customer_confirmed=True (agent may only set it after customer explicitly confirms exact appointment).
3. Hard gates before any Cal call: real full name, valid email, real 10-digit phone, REAL address (house number + street suffix + FL/Florida + 5-digit ZIP; rejects TBD/unknown/city-only/PO Box), service needed, future exact slot.
4. After Cal POST: requires booking UID, then RE-FETCHES the booking from Cal and only proceeds if status accepted/confirmed + correct eventTypeId + attendee email matches + time matches chosen slot + real address (house/ZIP) shows on Cal record. Otherwise NOT_BOOKED / NOT_CONFIRMED and Zoho is untouched.
5. Only after Cal proof: Zoho sync - find lead by email then phone (create if missing, Lead_Source Chat), create human Zoho Task (Subject includes Cal UID, Status Not Started, Priority High, Due_Date = appointment date, What_Id -> Leads), then Lead_Status -> Appointment Set with [Cal UID] marker in Description. Task search by UID prevents duplicates.
6. No silent failures: Zoho errors return BOOKED_AND_CONFIRMED_IN_CAL_BUT_ZOHO_SYNC_FAILED with reason (removed silent except:pass pattern for this path).
7. Direct Cal bookings: POST /sync-cal-bookings (MACHINE_TOKEN guard if set) + daily pipeline calls _sync_recent_cal_bookings() - only accepted, upcoming, both event types, with real name/email/phone/address; missing real address = skipped and reported, never marked solid.
8. Prompt (BUSINESS_INFO Step 5) rewritten: ask type/mode, durations, read back exact appointment, ask Should I book this exact appointment?, only call book_appointment on explicit yes, only claim booked on BOOKED_AND_CONFIRMED.
9. /debug now reports cal_consultation_event_id 7325379, cal_home_visit_event_id 7554154, cal_booking_sync part3-v1-real-confirmed-only. No env keys or values changed/printed.

## VERIFIED LIVE
- Local sandbox: patch applied to fresh main copy, ast syntax OK, python -m py_compile OK (61,157 chars after patch in Actions copy; 61,157 bytes on GitHub).
- GitHub Actions run 39380291813: success.
- Render: service sjt-concierge srv-dau0mf8u01pc73aqe3cg, deploy dep-dbbgir9htm6c73ai4eng, commit 1ef5e2d, status LIVE finished 2026-10-20T06:31:31Z.
- GET https://sjt-concierge.onrender.com/ping -> {alive: true}
- GET https://sjt-concierge.onrender.com/debug -> {cal_booking_sync: part3-v1-real-confirmed-only, cal_consultation_event_id: 7325379, cal_home_visit_event_id: 7554154, cal_key_loaded: true, crm: zoho}

## HONEST LIMITS - DO NOT OVERCLAIM
- NO fake test booking was made (owner rule: real appointments only). End-to-end booking -> Zoho Appointment Set + Task is NOT proven yet. First proof = first real customer booking (or a real owner self-booking he wants kept), then verify Cal UID accepted + Zoho Lead/Task live.
- Zoho writes from Render still depend on Fix #3: concierge.py uses COMPOSIO_USER_ID default (env unset). Assistant-side Zoho connection is NOT Render default. If Zoho sync fails live, code will now report it loudly instead of hiding it. Owner has NOT yet said connect default in this step.
- API shapes followed verified patterns (Cal slots/bookings, Zoho Tasks fields Subject/Due_Date/Status/Priority/What_Id) but only a real booking proves them end-to-end. No sends, no posts, no calls, no /run-daily, no /run-social, no test booking in this step. Only code commit + Render auto-deploy + read-only /ping /debug verify.

## NEXT
1. Fix #3: owner says connect default (zoho, zoho_mail, facebook, instagram, twitter for default; no Render env change).
2. First real booking proof (supervised, separate go if a test-with-real-details is wanted).
3. Owner Google Business Profile work - ask owner what was done/changed there before logging any GBP status (Part 6).
4. WhatsApp template, then supervised 9AM run.

Prior notes stand; do not duplicate: part3-home-visit-done a880284, part3-booking-started 6c56720, part2-lead-source-done 7d6c842, frankenstein-fix3, handoff-summary.
